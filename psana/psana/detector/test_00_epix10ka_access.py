#!/usr/bin/env python

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname).1s] %(message)s', level=logging.DEBUG)

from psana import DataSource

import sys

SCRNAME = sys.argv[0].rsplit('/')[-1]
USAGE = '\n  python %s <test-name>' % SCRNAME\
      + '\n  where test-name: '\
      + '\n    0 - quad'\
      + '\n    1 - quad segs 1 and 3'\
      + '\n    2 - opal - test tutorials/ami2/tmo/pop_raw_imgs.xtc2'\
      + '\n    3 - opal - real exp:tmolw0518, run:102, detname:tmoopal'\
      + '\n    4 - opal - real exp:tmolw0618, run:52, detname:tmoopal'\
      + '\n    5 - opal - real exp:tstx00117, run:144'\

print(USAGE)

tname = sys.argv[1] if len(sys.argv)>1 else '2'


def datasource_run(**kwa):
    ds = DataSource(**kwa)
    return ds, next(ds.runs())


def datasource_run_det(**kwa):
    ds = DataSource(**kwa)
    run = next(ds.runs())
    return ds, run, run.Detector(kwa.get('detname','opal'))


if tname in ('0','1'):

    fname = '/reg/g/psdm/detector/data2_test/xtc/data-tstx00417-r0014-epix10kaquad-e000005.xtc2' if tname ==0 else\
            '/reg/g/psdm/detector/data2_test/xtc/data-tstx00417-r0014-epix10kaquad-e000005-seg1and3.xtc2'

    ds,run,det = datasource_run_det(files=fname, detname='epix10k2M')

    print('XXX dir(det):\n', dir(det))
    print('XXX dir(run):\n', dir(run))

    raw = det.raw
    print('dir(det.raw):', dir(det.raw))

    print('raw._configs:', raw._configs)
    cfg = raw._configs[0]
    print('dir(cfg):', dir(cfg))

    c0 = cfg.epix10k2M[0]
    print('dir(c0):', dir(c0))

    print('dir(c0.raw):', dir(c0.raw))

    print('WHAT IS THAT? c0.raw.raw', c0.raw.raw)


elif tname in('2','3','4'):

    from psana.pyalgos.generic.NDArrUtils import info_ndarr # print_ndarr

    kwa = {'files':'/reg/g/psdm/tutorials/ami2/tmo/pop_raw_imgs.xtc2'} if tname=='2' else\
          {'exp':'tmolw0518', 'run':102, 'detname':'tmoopal'} if tname=='3' else\
          {'exp':'tmolw0618', 'run':52, 'detname':'tmoopal'}

    ds,run,det = datasource_run_det(**kwa)

    print('XXX dir(det):\n', dir(det))
    print('XXX dir(run):\n', dir(run))

    print('XXX run.runnum  : ', run.runnum)   # 101
    print('XXX run.detnames: ', run.detnames) # {'opal'}
    print('XXX run.expt    : ', run.expt)     # amox27716
    print('XXX run.id      : ', run.id)       # 0

    print('XXX det.calibconst.keys(): ', det.calibconst.keys())   # dict_keys(['pop_rbfs'])
    #print('XXX det.calibconst[pop_rbfs]: ', det.calibconst['pop_rbfs']) #

    resp =  det.calibconst['pop_rbfs']
    print('XXX len(det.calibconst[pop_rbfs]): ', len(resp))
    rbfs_cons, rbfs_meta = resp

    for k,v in rbfs_cons.items():
        if k>20: break
        print(info_ndarr(v,'%03d: '%k, last=5))

    print('XXX type(rbfs_cons): ', type(rbfs_cons)) # <class 'dict'>
    print('XXX type(rbfs_meta): ', type(rbfs_meta)) # <class 'dict'>
    print('XXX rbfs_meta: ', rbfs_meta) #

elif tname == '5':
    #on daq-det-drp01:
    #detnames /u2/lcls2/tst/tstx00117/xtc/tstx00117-r0144-s000-c000.xtc2

    #ds,run = datasource_run(exp='tstx00117', run=144)
    ds,run = datasource_run(files='/u2/lcls2/tst/tstx00117/xtc/tstx00117-r0144-s000-c000.xtc2')

    print('XXX dir(run):\n', dir(run))

    print('XXX run.runnum  : ', run.runnum)   # 101
    print('XXX run.detnames: ', run.detnames) # {'opal'}
    print('XXX run.expt    : ', run.expt)     # amox27716
    print('XXX run.id      : ', run.id)       # 0

    #print('XXX dir(det):\n', dir(det))
    #print('XXX det.calibconst.keys(): ', det.calibconst.keys())   # dict_keys(['pop_rbfs'])
    #print(det.calibconst)

else:
    print(USAGE)
    exit('TEST %s IS NOT IMPLEMENTED'%tname)

exit('END OF TEST %s'%tname)
