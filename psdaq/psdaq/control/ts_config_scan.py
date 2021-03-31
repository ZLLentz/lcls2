import sys
import logging
from psalg.utils.syslog import SysLog # FIXME remove
import threading
import zmq
from psdaq.control.ControlDef import ControlDef
from psdaq.control.DaqControl import DaqControl
from psdaq.control.ConfigScan import ConfigScan
from psdaq.control.control import DaqPVA, MyFloatPv, MyStringPv
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-B', metavar='PVBASE', required=True, help='PV base')
    parser.add_argument('-p', type=int, choices=range(0, 8), default=0,
                        help='platform (default 0)')
    parser.add_argument('-x', metavar='XPM', type=int, required=True, help='master XPM')
    parser.add_argument('-C', metavar='COLLECT_HOST', default='localhost',
                        help='collection host (default localhost)')
    parser.add_argument('-t', type=int, metavar='TIMEOUT', default=10000,
                        help='timeout msec (default 10000)')
    parser.add_argument('-c', type=int, metavar='READOUT_COUNT', default=1, help='# of events to aquire at each step (default 1)')
    parser.add_argument('-g', type=int, metavar='GROUP_MASK', help='bit mask of readout groups (default 1<<plaform)')
    parser.add_argument('--config', metavar='ALIAS', help='configuration alias (e.g. BEAM)')
    parser.add_argument('-v', action='store_true', help='be verbose')
    args = parser.parse_args()

    if args.g is not None:
        if args.g < 1 or args.g > 255:
            parser.error('readout group mask (-g) must be 1-255')

    if args.c < 1:
        parser.error('readout count (-c) must be >= 1')

    # instantiate DaqControl object
    control = DaqControl(host=args.C, platform=args.p, timeout=args.t)

    try:
        instrument = control.getInstrument()
    except KeyboardInterrupt:
        instrument = None

    if instrument is None:
        sys.exit('Error: failed to read instrument name (check -C <COLLECT_HOST>)')

    # configure logging handlers
    if args.v:
        level=logging.DEBUG
    else:
        level=logging.WARNING
    logger = SysLog(instrument=instrument, level=level)
    logging.info('logging initialized')

    # get initial DAQ state
    daqState = control.getState()
    logging.info('initial state: %s' % daqState)
    if daqState == 'error':
        sys.exit(1)

    # optionally set BEAM or NOBEAM
    if args.config is not None:
        # config alias request
        rv = control.setConfig(args.config)
        if rv is not None:
            logging.error('%s' % rv)

    # instantiate ConfigScan
    scan = ConfigScan(control, daqState=daqState, args=args)

    scan.stage()

    # -- begin script --------------------------------------------------------

    # PV scan setup
    motors = [MyFloatPv("tstts_step_value"), MyStringPv("tstts_step_docstring")]
    scan.configure(motors = motors)

    # config scan setup
    keys_dict = {"configure": {"step_keys":     ["tstts_0:expert.group0.inhibit0.interval"],
                               "NamesBlockHex": scan.getBlock(transitionid=ControlDef.transitionId['Configure'],
                                                              add_names=True, add_shapes_data=False).hex()}}
    # scan loop
    for interval in [10,20,30]:
        # update
        scan.update(value=scan.step_count())
        values_dict = \
          {"beginstep": {"step_values":        {"tstts_0:expert.group0.inhibit0.interval": interval},
                         "ShapesDataBlockHex": scan.getBlock(transitionid=ControlDef.transitionId['BeginStep'],
                                                             add_names=False, add_shapes_data=True).hex()}}
        # trigger
        scan.trigger(phase1Info={**keys_dict, **values_dict})

    # -- end script ----------------------------------------------------------

    scan.unstage()

    scan.push_socket.send_string('shutdown') #shutdown the daq communicator thread
    scan.comm_thread.join()

if __name__ == '__main__':
    main()
