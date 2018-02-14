import peakFinder
import numpy as np
import matplotlib.pyplot as plt
calib = np.load("/reg/neh/home4/yoon82/temp/lcls2/cxitut13_r10_32.npy")
data = calib[0]
mask = np.ones_like(data, dtype=np.uint16)
print(mask.shape)

# step 1
a = peakFinder.peak_finder_algos()
print("Done step1")

# step 2
a.set_peak_selection_parameters(npix_min=2, npix_max=30, amax_thr=200, atot_thr=600, son_min=7)
print("Done step2")

# step 3
mypeaks = a.peak_finder_v3r3_d2(data, mask, rank=3, r0=4, dr=2, nsigm=0)
print("Done step3")

fig, ax = plt.subplots()
ax.imshow(calib[0], interpolation='none')
for p in mypeaks:
    print("Row:%d Col:%d I:%f SON:%f"%(p.row, p.col, p.amp_tot, p.son))
    #print(p.seg, p.row, p.col, p.npix, p.amp_max, p.amp_tot, p.row_cgrav, p.col_cgrav, p.row_sigma, p.col_sigma, p.row_min, p.row_max, p.col_min, p.col_max, p.bkgd, p.noise, p.son)
    #ax.plot(p.col, p.row,'o',markersize=20)
    ax.scatter(p.col, p.row, s=50, facecolors='none', edgecolors='r')
plt.show()

#peaks = peaks_adaptive(data, mask, rank=5, r0=7.0, dr=2.0, nsigm=3,\
#                           npix_min=1, npix_max=None, amax_thr=0, atot_thr=0, son_min=8)
#    print 'peaks_adaptive: img.shape=%s consumed time = %.6f(sec)' % (str(sh), time()-t0_sec)
#    for p in peaks : 
#        print '  seg:%4d, row:%4d, col:%4d, npix:%4d, son:%4.1f' % (p.seg, p.row, p.col, p.npix, p.son)

exit()

#a = something.pything()
#print(a)

f = final.make_matrix(3,4)
f[0,0] = 5.7
f[2,3] = 11.2
print(f, f.dtype, f.shape, type(f.dtype))
fc = f
f = None # f is not deallocated due to fc

g = final.make_array(5)
print(g, g.dtype, g.shape)
import numpy as np
h = np.append(g,[9,8,7,6,5])
print(h, h.dtype, h.shape)
i = np.sort(h)
print("sorted: ", i )

