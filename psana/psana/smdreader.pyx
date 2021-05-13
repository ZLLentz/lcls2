## cython: linetrace=True
## distutils: define_macros=CYTHON_TRACE_NOGIL=1
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from dgramlite cimport Xtc, Sequence, Dgram
from parallelreader cimport Buffer, ParallelReader
from libc.stdint cimport uint32_t, uint64_t
from cpython cimport array
import time, os
cimport cython
from psana.psexp import TransitionId


cdef class SmdReader:
    cdef ParallelReader prl_reader
    cdef int            winner, view_size
    cdef int            max_retries, sleep_secs
    cdef array.array    buf_offsets, stepbuf_offsets, buf_sizes, stepbuf_sizes
    cdef array.array    i_evts, founds

    def __init__(self, int[:] fds, int chunksize, int max_retries):
        assert fds.size > 0, "Empty file descriptor list (fds.size=0)."
        self.prl_reader         = ParallelReader(fds, chunksize)
        
        # max retries has no default value (set when creating datasource)
        self.max_retries        = max_retries
        self.sleep_secs         = 1
        self.buf_offsets        = array.array('Q', [0]*fds.size)
        self.stepbuf_offsets    = array.array('Q', [0]*fds.size)
        self.buf_sizes          = array.array('Q', [0]*fds.size)
        self.stepbuf_sizes      = array.array('Q', [0]*fds.size)
        self.i_evts             = array.array('Q', [0]*fds.size)
        self.founds             = array.array('Q', [0]*fds.size)

    def is_complete(self):
        """ Checks that all buffers have at least one event 
        """
        cdef int is_complete = 1
        cdef int i

        for i in range(self.prl_reader.nfiles):
            if self.prl_reader.bufs[i].n_ready_events - \
                    self.prl_reader.bufs[i].n_seen_events == 0:
                is_complete = 0

        return is_complete


    def get(self, found_xtc2):
        self.prl_reader.just_read()
        
        if self.max_retries > 0:

            cn_retries = 0
            while not self.is_complete():
                flag_founds = found_xtc2('smd') 

                # Only when .inprogress file is used and ALL xtc2 files are found 
                # that this will return a list of all(True). If we have a mixed
                # of True and False, we let ParallelReader decides which file
                # to read but we'll still need to do sleep.
                if all(flag_founds): break

                time.sleep(self.sleep_secs)
                print(f'smdreader waiting for an event...retry#{cn_retries+1} (max_retries={self.max_retries})')
                self.prl_reader.just_read()
                cn_retries += 1
                if cn_retries >= self.max_retries:
                    break

    @cython.boundscheck(False)
    def view(self, int batch_size=1000):
        """ Returns memoryview of the data and step buffers.

        This function is called by SmdReaderManager only when is_complete is True (
        all buffers have at least one event). It returns events of batch_size if
        possible or as many as it has for the buffer.
        """

        # Find the winning buffer
        cdef int i, i_evt
        cdef uint64_t limit_ts=0
        
        for i in range(self.prl_reader.nfiles):
            if self.prl_reader.bufs[i].timestamp < limit_ts or limit_ts == 0:
                limit_ts = self.prl_reader.bufs[i].timestamp
                self.winner = i

        # Apply batch_size
        # Find the boundary or limit ts of the winning buffer
        # this is either the nth or the batch_size event.
        self.view_size = self.prl_reader.bufs[self.winner].n_ready_events - \
                self.prl_reader.bufs[self.winner].n_seen_events
        if self.view_size > batch_size:
            limit_ts = self.prl_reader.bufs[self.winner].ts_arr[\
                    self.prl_reader.bufs[self.winner].n_seen_events - 1 + batch_size]
            self.view_size = batch_size

        # Locate the viewing window and update seen_offset for each buffer
        cdef uint64_t[:] ts_view
        cdef uint64_t prev_seen_offset  = 0
        cdef uint64_t block_size
        cdef Buffer* buf
        cdef uint64_t[:] buf_offsets    = self.buf_offsets
        cdef uint64_t[:] buf_sizes      = self.buf_sizes
        cdef uint64_t[:] stepbuf_offsets= self.stepbuf_offsets
        cdef uint64_t[:] stepbuf_sizes  = self.stepbuf_sizes
        cdef uint64_t[:] i_evts         = self.i_evts 
        cdef uint64_t[:] founds         = self.founds
        cdef unsigned view_size         = 0
        for i in range(self.prl_reader.nfiles):
            buf = &(self.prl_reader.bufs[i])
            buf_offsets[i] = buf.seen_offset
            
            # All the events before found_pos are within max_ts
            if buf.n_seen_events < buf.n_ready_events:
                i_evts[i] = buf.n_seen_events # safe to move index up
            else:
                i_evts[i] = buf.n_seen_events - 1 # keep idx fixed (-1: index vs. no.) 

            founds[i] = 0
            while i_evts[i] < buf.n_ready_events - 1 and        \
                    buf.ts_arr[i_evts[i]] < limit_ts  and    \
                    buf.sv_arr[i_evts[i]] != TransitionId.EndRun:
                i_evts[i] += 1

            if buf.ts_arr[i_evts[i]] > limit_ts:
                if i_evts[i] == 0:
                    view_size = 0
                else:
                    i_evts[i] -= 1
                    view_size = i_evts[i] + 1 - buf.n_seen_events
            else:
                view_size = i_evts[i] + 1 - buf.n_seen_events
            
            # Update view_size in case exit with EndRun found
            if i == self.winner:
                self.view_size = view_size

            if view_size == 0:
                buf_sizes[i] = 0
            else:
                founds[i] = i_evts[i]              
                buf.seen_offset = buf.next_offset_arr[founds[i]]
                buf.n_seen_events = founds[i] + 1
                buf_sizes[i] = buf.seen_offset - buf_offsets[i]

                # Check if this viewing window has EndRun at the end 
                if buf.sv_arr[founds[i]] == TransitionId.EndRun:
                    buf.found_endrun = 1
            
            # Handle step buffers the same way
            buf = &(self.prl_reader.step_bufs[i])
            stepbuf_offsets[i] = buf.seen_offset
            
            # All the events before found_pos are within max_ts
            if buf.n_seen_events < buf.n_ready_events:
                i_evts[i] = buf.n_seen_events     # safe to move index up
            else:
                i_evts[i] = buf.n_seen_events - 1 # keep idx fixed (-1: index vs. no.) 

            founds[i] = 0
            while i_evts[i] < buf.n_ready_events - 1 and        \
                    buf.ts_arr[i_evts[i]] < limit_ts  and    \
                    buf.sv_arr[i_evts[i]] != TransitionId.EndRun:
                i_evts[i] += 1

            # Correct the index in case over count by one
            if buf.ts_arr[i_evts[i]] > limit_ts:
                if i_evts[i] == 0: 
                    view_size = 0
                else:
                    i_evts[i] -= 1
                    view_size = i_evts[i] + 1 - buf.n_seen_events
            else:
                view_size = i_evts[i] + 1 - buf.n_seen_events

            if view_size == 0:
                stepbuf_sizes[i] = 0
            else:
                founds[i] = i_evts[i]
                buf.seen_offset = buf.next_offset_arr[founds[i]]
                buf.n_seen_events = founds[i] + 1
                stepbuf_sizes[i] = buf.seen_offset - stepbuf_offsets[i]
        
        # output as a list of memoryviews for both L1 and step buffers
        mmrv_bufs = []
        mmrv_step_bufs = []
        cdef char[:] view
        for i in range(self.prl_reader.nfiles):
            buf = &(self.prl_reader.bufs[i])
            if buf_sizes[i] > 0:
                prev_seen_offset = buf_offsets[i]
                block_size = buf_sizes[i]
                view = <char [:block_size]> (buf.chunk + prev_seen_offset)
                mmrv_bufs.append(view)
            else:
                mmrv_bufs.append(0) # add 0 as a place=holder for empty buffer
            
            buf = &(self.prl_reader.step_bufs[i])
            if self.stepbuf_sizes[i] > 0:
                prev_seen_offset = stepbuf_offsets[i]
                block_size = stepbuf_sizes[i]
                view = <char [:block_size]> (buf.chunk + prev_seen_offset)
                mmrv_step_bufs.append(view)
            else:
                mmrv_step_bufs.append(0) # add 0 as a place=holder for empty buffer
        
        return mmrv_bufs, mmrv_step_bufs


    @property
    def view_size(self):
        return self.view_size


    @property
    def got(self):
        return self.prl_reader.got

    @property
    def chunk_overflown(self):
        return self.prl_reader.chunk_overflown

    def found_endrun(self):
        cdef int i
        found = False
        cn_endruns = 0
        for i in range(self.prl_reader.nfiles):
            if self.prl_reader.bufs[i].found_endrun == 1:
                cn_endruns += 1
        if cn_endruns == self.prl_reader.nfiles:
            found = True
        return found


