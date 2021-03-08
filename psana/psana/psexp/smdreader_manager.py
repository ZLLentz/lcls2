from psana.smdreader import SmdReader
from psana.eventbuilder import EventBuilder
from psana.psexp.tools import Logging as logging
from psana.psexp import *
import os, time
from psana import dgram
from psana.event import Event


class BatchIterator(object):
    """ Iterates over batches of events.

    SmdReaderManager returns this object when a chunk is read.
    """
    def __init__(self, views, configs, run, batch_size=1, filter_fn=0, destination=0):
        self.batch_size     = batch_size
        self.filter_fn      = filter_fn
        self.destination    = destination
        self.run            = run 
        
        empty_view = True
        for view in views:
            if view:
                empty_view = False
                break

        if empty_view:
            self.eb = None
        else:
            self.eb = EventBuilder(views, configs)


    def __iter__(self):
        return self


    def __next__(self):
        # With batch_size known, smditer returns a batch_dict,
        # {rank:[bytearray, evt_size_list], ...} for each next 
        # while updating offsets of each smd memoryview
        if not self.eb: raise StopIteration

        batch_dict, step_dict = self.eb.build(batch_size=self.batch_size, 
                filter_fn=self.filter_fn, 
                destination=self.destination,
                run=self.run)
        if self.eb.nevents == 0 and self.eb.nsteps == 0: raise StopIteration
        return batch_dict, step_dict



class SmdReaderManager(object):
    def __init__(self, smd_fds, dsparms, configs=None):
        self.n_files = len(smd_fds)
        self.dsparms = dsparms
        self.configs = configs
        assert self.n_files > 0
        
        self.smd0_n_events = int(os.environ.get('PS_SMD_N_EVENTS', 1000))
        if self.dsparms.max_events:
            if self.dsparms.max_events < self.smd0_n_events:
                self.smd0_n_events = self.dsparms.max_events
        
        self.chunksize = int(os.environ.get('PS_SMD_CHUNKSIZE', 0x1000000))
        self.smdr = SmdReader(smd_fds, self.chunksize, self.dsparms.max_retries)
        self.processed_events = 0
        self.got_events = -1
        self._run = None
        
        # Collecting Smd0 performance using prometheus
        self.c_read = self.dsparms.prom_man.get_metric('psana_smd0_read')

    def _get(self):
        st = time.time()
        self.smdr.get()
        en = time.time()
        logging.info(f'smdreader_manager: read {self.smdr.got/1e6:.5f} MB took {en-st}s. rate: {self.smdr.got/(1e6*(en-st))} MB/s')
        self.c_read.labels('MB', 'None').inc(self.smdr.got/1e6)
        self.c_read.labels('seconds', 'None').inc(en-st)
        
        if self.smdr.chunk_overflown > 0:
            msg = f"SmdReader found dgram ({self.smdr.chunk_overflown} MB) larger than chunksize ({self.chunksize/1e6} MB)"
            raise ValueError(msg)

    def get_next_dgrams(self):
        if self.dsparms.max_events > 0 and \
                self.processed_events >= self.dsparms.max_events:
            logging.info(f'smdreader_manager: get_next_dgrams max_events={self.dsparms.max_events} reached')
            return None

        dgrams = None
        if not self.smdr.is_complete():
            self._get()
         
        if self.smdr.is_complete():
            mmrv_bufs, _ = self.smdr.view(batch_size=1)

            # For configs, we need to copy data from smdreader's buffers
            # This prevents it from getting overwritten by other dgrams.
            bytearray_bufs = [bytearray(mmrv_buf) for mmrv_buf in mmrv_bufs]
            
            if self.configs is None:
                dgrams = [dgram.Dgram(view=ba_buf, offset=0) for ba_buf in bytearray_bufs]
                self.configs = dgrams
            else:
                dgrams = [dgram.Dgram(view=ba_buf, config=config, offset=0) for ba_buf, config in zip(bytearray_bufs, self.configs)]
        return dgrams


    def __iter__(self):
        return self


    def __next__(self):
        """
        Returns a batch of events as an iterator object.
        This is used by non-parallel run. Parallel run uses chunks
        generator that yields chunks of raw smd data and steps (no
        event building). 
        
        The iterator stops reading under two conditions. Either there's
        no more data or max_events reached.
        """
        if self.dsparms.max_events and self.processed_events >= self.dsparms.max_events:
            raise StopIteration
        
        if not self.smdr.is_complete():
            self._get()
            if not self.smdr.is_complete():
                raise StopIteration
        
        mmrv_bufs, _ = self.smdr.view(batch_size=self.smd0_n_events)
        batch_iter = BatchIterator(mmrv_bufs, self.configs, self._run, 
                batch_size  = self.dsparms.batch_size, 
                filter_fn   = self.dsparms.filter, 
                destination = self.dsparms.destination)
        self.got_events = self.smdr.view_size
        self.processed_events += self.got_events

        return batch_iter
        

    def chunks(self):
        """ Generates a tuple of smd and step dgrams """
        is_done = False
        while not is_done:
            if self.smdr.is_complete():
                mmrv_bufs, mmrv_step_bufs = self.smdr.view(batch_size=self.smd0_n_events)
                self.got_events = self.smdr.view_size
                self.processed_events += self.got_events
                
                # sending data to prometheus
                logging.info('smdreader_manager: smd0 got %d events'%(self.got_events))

                if self.dsparms.max_events and self.processed_events >= self.dsparms.max_events:
                    logging.info(f'smdreader_manager: max_events={self.dsparms.max_events} reached')
                    is_done = True
                
                smd_view = bytearray()
                smd_pf = PacketFooter(n_packets=self.n_files)
                step_view = bytearray()
                step_pf = PacketFooter(n_packets=self.n_files)
                
                for i, (mmrv_buf, mmrv_step_buf) in enumerate(zip(mmrv_bufs, mmrv_step_bufs)):
                    if mmrv_buf != 0:
                        smd_view.extend(mmrv_buf)
                        smd_pf.set_size(i, memoryview(mmrv_buf).nbytes)
                    
                    if mmrv_step_buf != 0:
                        step_view.extend(mmrv_step_buf)
                        step_pf.set_size(i, memoryview(mmrv_step_buf).nbytes)

                if smd_view or step_view:
                    if smd_view:
                        smd_view.extend(smd_pf.footer)
                    if step_view:
                        step_view.extend(step_pf.footer)
                    yield (smd_view, step_view)

            else: # if self.smdr.is_complete()
                self._get()
                if not self.smdr.is_complete():
                    is_done = True
                    break
        

    @property
    def min_ts(self):
        return self.smdr.min_ts


    @property
    def max_ts(self):
        return self.smdr.max_ts

    def set_run(self, run):
        self._run = run

    def get_run(self):
        return self._run

