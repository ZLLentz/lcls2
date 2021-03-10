####!/usr/bin/env python
""":py:class:`Graphics` wrapping methods for matplotlib
=======================================================

Usage::

    import psana.pyalgos.generic.Graphics as gr

    # Methods

    fig = gr.figure(figsize=(13,12), title='Image', dpi=80, facecolor='w', edgecolor='w', frameon=True, move=None)
    gr.move_fig(fig, x0=200, y0=100)
    gr.move(x0=200, y0=100)
    fig, axis = gr.add_axes(fig, axwin=(0.05, 0.03, 0.87, 0.93))
    fig, axim, axcb = gr.fig_img_cbar_axes(fig=None, win_axim=(0.05,0.03,0.87,0.93), win_axcb=(0.923,0.03,0.02,0.93))
    gr.set_win_title(fig, titwin='Image')
    gr.add_title_labels_to_axes(axes, title=None, xlabel=None, ylabel=None, fslab=14, fstit=20, color='k')
    gr.show(mode=None)
    gr.draw()
    gr.draw_fig(fig)
    gr.save_plt(fname='img.png', verb=True)
    gr.save_fig(fig, fname='img.png', verb=True)
    gr.save(fname='img.png', do_save=True, pbits=0o377)

    hi = gr.hist(axhi, arr, bins=None, amp_range=None, weights=None, color=None, log=False)
    imsh = gr.imshow(axim, img, amp_range=None, extent=None, interpolation='nearest', aspect='auto', origin='upper', orientation='horizontal', cmap='inferno')
    cbar = gr.colorbar(fig, imsh, axcb, orientation='vertical', amp_range=None)
    imsh, cbar = gr.imshow_cbar(fig, axim, axcb, img, amin=None, amax=None, extent=None, interpolation='nearest', aspect='auto', origin='upper', orientation='vertical', cmap='inferno')

    gr.drawCircle(axes, xy0, radius, linewidth=1, color='w', fill=False)
    gr.drawCenter(axes, xy0, s=10, linewidth=1, color='w')
    gr.drawLine(axes, xarr, yarr, s=10, linewidth=1, color='w')
    gr.drawRectangle(axes, xy, width, height, linewidth=1, color='w')
 
    # Depricated methods from pyimgalgos.GlobalGraphics.py added for compatability  

    fig, axhi, hi = gr.hist1d(arr, bins=None, amp_range=None, weights=None, color=None, show_stat=True,
                              log=False, figsize=(6,5), axwin=(0.15, 0.12, 0.78, 0.80), title=None, 
                              xlabel=None, ylabel=None, titwin=None)
    axim = gr.plotImageLarge(arr, img_range=None, amp_range=None, figsize=(12,10), title='Image', origin='upper', 
                             window=(0.05, 0.03, 0.94, 0.94), cmap='inferno')
    fig, ax = gr.plotGraph(x,y, figsize=(5,10), window=(0.15, 0.10, 0.78, 0.86), pfmt='b-', lw=1)

See:
  - :py:class:`Utils`
  - :py:class:`NDArrUtils`
  - :py:class:`Graphics`
  - :py:class:`NDArrGenerators`
  - `matplotlib <https://matplotlib.org/contents.html>`_.

This software was developed for the LCLS2 project.
If you use all or part of it, please give an appropriate acknowledgment.

Modified on 2018-01-25 by Mikhail Dubrovin
"""

import logging
logger = logging.getLogger('Graphics')

import numpy as np
from time import time, localtime, strftime
from math import log10, sqrt

import matplotlib
import matplotlib.pyplot  as plt
import matplotlib.lines   as lines
import matplotlib.patches as patches

plt.rcParams.update({'figure.max_open_warning': 0}) #get rid of warning: More than 20 figures have been opened.

#----

def figure(**kwa):
    """ Creates and returns figure.
        local pars: title='Image', move=None
    """
    # redefine default parameters for plt.figure
    kwa.setdefault('figsize',(13,12))
    kwa.setdefault('dpi',80)
    kwa.setdefault('facecolor','w')
    kwa.setdefault('edgecolor','w')
    kwa.setdefault('frameon', True)

    title = kwa.pop('title', 'Image')
    move  = kwa.pop('move', None)

    fig = plt.figure(**kwa)

    fig.canvas.set_window_title(title) #, **kwa)
    if move is not None: move_fig(fig, x0=move[0], y0=move[1])
    return fig


def set_win_title(fig, titwin='Image', **kwa):
    fig.canvas.set_window_title(titwin, **kwa)


def move_fig(fig, x0=200, y0=100):
    fig.canvas.manager.window.move(x0, y0)
    #fig.canvas.manager.window.geometry('+%d+%d' % (x0, y0)) # in previous version of matplotlib


def move(x0=200,y0=100):
    plt.get_current_fig_manager().window.move(x0, y0)
    #plt.get_current_fig_manager().window.geometry('+%d+%d' % (x0, y0))


def add_axes(fig, axwin=(0.05, 0.03, 0.87, 0.93), **kwa):
    """Add axes to figure from input list of windows.
    """
    return fig.add_axes(axwin, **kwa)


def fig_img_axes(fig=None, win_axim=(0.08, 0.05, 0.89, 0.93), **kwa):
    """ Returns figure and image axes
    """
    _fig = figure(figsize=(6,5)) if fig is None else fig
    axim = _fig.add_axes(win_axim, **kwa)
    return _fig, axim


def fig_img_cbar_axes(fig=None,\
                      win_axim=(0.05,  0.05, 0.87, 0.93),\
                      win_axcb=(0.923, 0.05, 0.02, 0.93),\
                      **kwa):
    """ Returns figure and axes for image and color bar
    """
    _fig = figure() if fig is None else fig
    return _fig,\
           _fig.add_axes(win_axim, **kwa),\
           _fig.add_axes(win_axcb, **kwa)


FYMIN, FYMAX = 0.050, 0.90
def fig_img_cbar_hist_axes(fig=None,\
                      win_axim=(0.02,  FYMIN, 0.8,  FYMAX),\
                      win_axcb=(0.915, FYMIN, 0.01, FYMAX),\
                      win_axhi=(0.76,  FYMIN, 0.15, FYMAX),\
                      **kwa):
    """ Returns figure and axes for image, color bar, and spectral histogram
    """
    _fig = figure() if fig is None else fig
    return _fig,\
           _fig.add_axes(win_axim, **kwa),\
           _fig.add_axes(win_axcb, **kwa),\
           _fig.add_axes(win_axhi, **kwa)


def add_title_labels_to_axes(axes, title=None, xlabel=None, ylabel=None, fslab=14, fstit=20, color='k', **kwa):
    if title  is not None: axes.set_title(title, color=color, fontsize=fstit, **kwa)
    if xlabel is not None: axes.set_xlabel(xlabel, fontsize=fslab, **kwa)
    if ylabel is not None: axes.set_ylabel(ylabel, fontsize=fslab, **kwa)


def show(mode=None):
    if mode is None: plt.ioff() # hold contraol at show() (connect to keyboard for controllable re-drawing)
    else           : plt.ion()  # do not hold control
    plt.pause(0.001) # hack to make it work... othervise show() does not work...
    plt.show()


def draw():
    plt.draw()


def draw_fig(fig):
    fig.canvas.draw()


def save_plt(fname='img.png', verb=True, **kwa):
    if verb: print('Save plot in file: %s' % fname)
    plt.savefig(fname, **kwa)


def save_fig(fig, fname='img.png', prefix=None, suffix='.png', verb=True, **kwa):
    path = fname
    if prefix is not None:
        ts = strftime('%Y-%m-%dT%H%M%S', localtime(time()))
        path='%s%s%s' % (prefix,ts,suffix)
    if verb: print('Save figure in file: %s' % path)
    fig.savefig(path, **kwa)


def save(fname='img.png', do_save=True, verb=True, **kwa):
    if not do_save: return
    save_plt(fname, verb, **kwa)


def proc_stat(weights, bins):
    center = np.array([0.5*(bins[i] + bins[i+1]) for i,w in enumerate(weights)])

    sum_w  = weights.sum()
    if sum_w <= 0: return  0, 0, 0, 0, 0, 0, 0, 0, 0
    
    sum_w2 = (weights*weights).sum()
    neff   = sum_w*sum_w/sum_w2 if sum_w2>0 else 0
    sum_1  = (weights*center).sum()
    mean = sum_1/sum_w
    d      = center - mean
    d2     = d * d
    wd2    = weights*d2
    m2     = (wd2)   .sum() / sum_w
    m3     = (wd2*d) .sum() / sum_w
    m4     = (wd2*d2).sum() / sum_w

    #sum_2  = (weights*center*center).sum()
    #err2 = sum_2/sum_w - mean*mean
    #err  = sqrt(err2)

    rms  = sqrt(m2) if m2>0 else 0
    rms2 = m2
    
    err_mean = rms/sqrt(neff)
    err_rms  = err_mean/sqrt(2)    

    skew, kurt, var_4 = 0, 0, 0

    if rms>0 and rms2>0:
        skew  = m3/(rms2 * rms) 
        kurt  = m4/(rms2 * rms2) - 3
        var_4 = (m4 - rms2*rms2*(neff-3)/(neff-1))/neff if neff>1 else 0
    err_err = sqrt(sqrt(var_4)) if var_4>0 else 0 
    #print  'mean:%f, rms:%f, err_mean:%f, err_rms:%f, neff:%f' % (mean, rms, err_mean, err_rms, neff)
    #print  'skew:%f, kurt:%f, err_err:%f' % (skew, kurt, err_err)
    return mean, rms, err_mean, err_rms, neff, skew, kurt, err_err, sum_w


def add_stat_text(axhi, weights, bins):
    #mean, rms, err_mean, err_rms, neff = proc_stat(weights,bins)
    mean, rms, err_mean, err_rms, neff, skew, kurt, err_err, sum_w = proc_stat(weights,bins)
    pm = r'$\pm$' 
    txt  = 'Entries=%d\nMean=%.2f%s%.2f\nRMS=%.2f%s%.2f\n' % (sum_w, mean, pm, err_mean, rms, pm, err_rms)
    txt += r'$\gamma1$=%.3f  $\gamma2$=%.3f' % (skew, kurt)
    #txt += '\nErr of err=%8.2f' % (err_err)
    xb,xe = axhi.get_xlim()     
    yb,ye = axhi.get_ylim()     
    #x = xb + (xe-xb)*0.84
    #y = yb + (ye-yb)*0.66
    #axhi.text(x, y, txt, fontsize=10, color='k', ha='center', rotation=0)
    x = xb + (xe-xb)*0.98
    y = yb + (ye-yb)*0.95

    if axhi.get_yscale() is 'log':
        #print 'axhi.get_yscale():', axhi.get_yscale()
        log_yb, log_ye = log10(yb), log10(ye)
        log_y = log_yb + (log_ye-log_yb)*0.95
        y = 10**log_y

    axhi.text(x, y, txt, fontsize=10, color='k',
              horizontalalignment='right',
              verticalalignment='top',
              rotation=0)


def hist(axhi, arr, bins=None, amp_range=None, weights=None, color=None, log=False, **kwa):
    """Makes historgam from input array of values (arr), which are sorted in number of bins (bins) in the range (amp_range=(amin,amax))
    """
    #axhi.cla()
    hi = axhi.hist(arr.flatten(), bins=bins, range=amp_range, weights=weights, color=color, log=log, **kwa) #, log=logYIsOn)
    if amp_range is not None: axhi.set_xlim(amp_range) # axhi.set_autoscale_on(False) # suppress autoscailing
    wei, bins, patches = hi
    add_stat_text(axhi, wei, bins)
    return hi


def imshow(axim, img, amp_range=None, extent=None,\
           interpolation='nearest', aspect='auto', origin='upper',\
           orientation='horizontal', cmap='inferno', **kwa):
    """
    extent - list of four image physical limits for labeling,
    cmap: 'jet', 'gray_r', 'inferno'
    #axim.cla()
    """
    imsh = axim.imshow(img, interpolation=interpolation, aspect=aspect, origin=origin, extent=extent, cmap=cmap, **kwa)
    axim.autoscale(False)
    if amp_range is not None: imsh.set_clim(amp_range[0],amp_range[1])
    return imsh


def colorbar(fig, imsh, axcb, orientation='vertical', amp_range=None, **kwa):
    """
    orientation = 'horizontal'
    amp_range = (-10,50)
    """
    if amp_range is not None: imsh.set_clim(amp_range[0],amp_range[1])
    cbar = fig.colorbar(imsh, cax=axcb, orientation=orientation, **kwa)
    return cbar


def imshow_cbar(fig, axim, axcb, img, amin=None, amax=None, **kwa):
    """
    extent - list of four image physical limits for labeling,
    cmap: 'gray_r'
    #axim.cla()
    """
    orientation = kwa.pop('orientation', 'vertical') # because imshow does not have it

    axim.cla()
    if img is None: return
    imsh = axim.imshow(img,\
           cmap=kwa.pop('cmap', 'inferno'),\
           norm=kwa.pop('norm',None),\
           aspect=kwa.pop('aspect', 'auto'),\
           interpolation=kwa.pop('interpolation', 'nearest'),\
           alpha=kwa.pop('alpha',None),\
           vmin=amin,\
           vmax=amax,\
           origin=kwa.pop('origin', 'upper'),\
           extent=kwa.pop('extent', None),\
           filternorm=kwa.pop('filternorm',True),\
           filterrad=kwa.pop('filterrad',4.0),\
           resample=kwa.pop('resample',None),\
           url=kwa.pop('url',None),\
           data=kwa.pop('data',None),\
           **kwa)
    axim.autoscale(False)
    ave = np.mean(img) if amin is None and amax is None else None
    rms = np.std(img)  if amin is None and amax is None else None
    cmin = amin if amin is not None else ave-1*rms if ave is not None else None
    cmax = amax if amax is not None else ave+3*rms if ave is not None else None
    if cmin is not None: imsh.set_clim(cmin, cmax)

    cbar = fig.colorbar(imsh, cax=axcb, orientation=orientation)
    return imsh, cbar


def drawCircle(axes, xy0, radius, **kwa): 
    kwa.setdefault('radius', radius)
    kwa.setdefault('linewidth', 1)
    kwa.setdefault('color', 'w')
    kwa.setdefault('fill', False)
    circ = patches.Circle(xy0, **kwa)
    axes.add_artist(circ)


def drawCenter(axes, xy0, **kwa): 
    s = kwa.pop('s', 10)
    kwa.setdefault('linewidth', 1)
    kwa.setdefault('color', 'w')
    xc, yc = xy0
    d = 0.15*s
    arrx = (xc+s, xc-s, xc-d, xc,   xc)
    arry = (yc,   yc,   yc-d, yc-s, yc+s)
    line = lines.Line2D(arrx, arry, **kwa)   
    axes.add_artist(line)


def drawLine(axes, xarr, yarr, **kwa): 
    kwa.setdefault('linewidth', 1)
    kwa.setdefault('color', 'w')
    line = lines.Line2D(xarr, yarr, **kwa)   
    axes.add_artist(line)


def drawRectangle(axes, xy, width, height, **kwa):
    kwa.setdefault('linewidth', 1)
    kwa.setdefault('color', 'w')
    rect = patches.Rectangle(xy, width, height, **kwa)
    axes.add_artist(rect)

#--------------------------------
# DEPRICATED from GlobalGraphics
#--------------------------------

def plotImageLarge(arr, img_range=None, amp_range=None, figsize=(12,10), title='Image', origin='upper', window=(0.05,  0.03, 0.94, 0.94), cmap='inferno'): 
    fig  = plt.figure(figsize=figsize, dpi=80, facecolor='w', edgecolor='w', frameon=True)
    axim = fig.add_axes(window)
    imsh = axim.imshow(arr, interpolation='nearest', aspect='auto', origin=origin, extent=img_range, cmap=cmap)
    axim.autoscale(False)
    colb = fig.colorbar(imsh, pad=0.005, fraction=0.09, shrink=1, aspect=40) # orientation=1
    if amp_range is not None: imsh.set_clim(amp_range[0], amp_range[1])
    #else: 
    #    ave, rms = arr.mean(), arr.std()
    #    imsh.set_clim(ave-1*rms, ave+5*rms)
    fig.canvas.set_window_title(title)
    return axim


def hist1d(arr, bins=None, amp_range=None, weights=None, color=None, show_stat=True, log=False,\
           figsize=(6,5), axwin=(0.15, 0.12, 0.78, 0.80),\
           title=None, xlabel=None, ylabel=None, titwin=None):
    """Makes historgam from input array of values (arr), which are sorted in number of bins (bins) in the range (amp_range=(amin,amax))
    """
    #print 'hist1d: title=%s, size=%d' % (title, arr.size)
    if arr.size==0: return None, None, None
    fig = plt.figure(figsize=figsize, dpi=80, facecolor='w', edgecolor='w', frameon=True)
    if   titwin is not None: fig.canvas.set_window_title(titwin)
    elif title  is not None: fig.canvas.set_window_title(title)
    axhi = fig.add_axes(axwin)
    hbins = bins if bins is not None else 100
    hi = axhi.hist(arr.flatten(), bins=hbins, range=amp_range, weights=weights, color=color, log=log) #, log=logYIsOn)
    if amp_range is not None: axhi.set_xlim(amp_range) # axhi.set_autoscale_on(False) # suppress autoscailing
    if title  is not None: axhi.set_title(title, color='k', fontsize=20)
    if xlabel is not None: axhi.set_xlabel(xlabel, fontsize=14)
    if ylabel is not None: axhi.set_ylabel(ylabel, fontsize=14)
    if show_stat:
        weights, bins, patches = hi
        add_stat_text(axhi, weights, bins)
    return fig, axhi, hi


def plotGraph(x,y, figsize=(5,10), window=(0.15, 0.10, 0.78, 0.86), pfmt='b-', lw=1): 
    fig = plt.figure(figsize=figsize, dpi=80, facecolor='w', edgecolor='w', frameon=True)
    ax = fig.add_axes(window)
    ax.plot(x, y, pfmt, linewidth=lw)
    return fig, ax


def img_from_pixel_arrays(rows, cols, W=None, dtype=np.float32, vbase=0):
    """Returns image from rows, cols index arrays and associated weights W.
       Methods like matplotlib imshow(img) plot 2-d image array oriented as matrix(rows,cols).
    """
    if rows.size != cols.size \
    or (W is not None and rows.size !=  W.size):
        msg = 'img_from_pixel_arrays(): input array sizes are different;' \
            + ' rows.size=%d, cols.size=%d, W.size=%d' % (rows.size, cols.size, W.size)
        logger.warning(msg)
        return img_default()

    rowsfl = rows.flatten()
    colsfl = cols.flatten()

    rsize = int(rowsfl.max())+1 
    csize = int(colsfl.max())+1

    weight = W.flatten() if W is not None else np.ones_like(rowsfl)
    img = vbase*np.ones((rsize,csize), dtype=dtype)
    img[rowsfl,colsfl] = weight # Fill image array with data 
    return img
    
#----

#from psana.pscalib.geometry.GeometryAccess import img_from_pixel_arrays
getImageFromIndexArrays = img_from_pixel_arrays # backward compatability

#----

if __name__ == "__main__":

  def test01():
    """ imshow
    """
    img = random_standard(shape=(40,60), mu=200, sigma=25)
    #fig = figure(figsize=(6,5), title='Test imshow', dpi=80, facecolor='w', edgecolor='w', frameon=True, move=(100,10))    
    #axim = add_axes(fig, axwin=(0.10, 0.08, 0.85, 0.88))
    fig, axim = fig_img_axes()
    move_fig(fig, x0=200, y0=100)
    imsh = imshow(axim, img, amp_range=None, extent=None,\
           interpolation='nearest', aspect='auto', origin='upper',\
           orientation='horizontal', cmap='jet') 


  def test02():
    """ hist
    """
    mu, sigma = 200, 25
    arr = random_standard((500,), mu, sigma)
    #fig = figure(figsize=(6,5), title='Test hist', dpi=80, facecolor='w', edgecolor='w', frameon=True, move=(100,10))    
    #axhi = add_axes(fig, axwin=(0.10, 0.08, 0.85, 0.88))
    fig, axhi = fig_img_axes()
    his = hist(axhi, arr, bins=100, amp_range=(mu-6*sigma,mu+6*sigma), weights=None, color=None, log=False)


  def test03():
    """ Update image in the event loop
    """
    #fig = figure(figsize=(6,5), title='Test hist', dpi=80, facecolor='w', edgecolor='w', frameon=True, move=(100,10))
    #axim = add_axes(fig, axwin=(0.10, 0.08, 0.85, 0.88))
    fig, axim = fig_img_axes()
    imsh = None
    for i in range(10):
       print('Event %3d' % i)
       img = random_standard((1000,1000), mu=200, sigma=25)
       #axim.cla()
       set_win_title(fig, 'Event %d' % i)

       if imsh is None:
           imsh = imshow(axim, img, amp_range=None, extent=None,\
                  interpolation='nearest', aspect='auto', origin='upper',\
                  orientation='horizontal', cmap='jet') 
       else:
           imsh.set_data(img)
       show(mode=1)  # !!!!!!!!!!       
       #draw_fig(fig) # !!!!!!!!!!


  def test04():
    """ Update histogram in the event loop
    """
    mu, sigma = 200, 25
    #fig = figure(figsize=(6,5), title='Test hist', dpi=80, facecolor='w', edgecolor='w', frameon=True, move=(100,10))
    #axhi = add_axes(fig, axwin=(0.10, 0.08, 0.85, 0.88))
    fig, axhi = fig_img_axes()

    for i in range(10):
       print('Event %3d' % i)
       arr = random_standard((500,), mu, sigma, dtype=np.float)
       axhi.cla()
       set_win_title(fig, 'Event %d' % i)
       his = hist(axhi, arr, bins=100, amp_range=(mu-6*sigma,mu+6*sigma), weights=None, color=None, log=False)

       show(mode=1) # !!!!!!!!!!
       #draw(fig)    # !!!!!!!!!!


  def test05():
    """ Update image with color bar in the event loop
    """
    fig, axim, axcb = fig_img_cbar_axes()
    move_fig(fig, x0=200, y0=0)
    imsh = None
    for i in range(20):
       print('Event %3d' % i)
       img = random_standard((1000,1000), mu=i, sigma=10)
       #axim.cla()
       set_win_title(fig, 'Event %d' % i)
       if imsh is None:
           imsh, cbar = imshow_cbar(fig, axim, axcb, img, amin=None, amax=None, extent=None,\
                                    interpolation='nearest', aspect='auto', origin='upper',\
                                    orientation='vertical', cmap='inferno')
       else:
           imsh.set_data(img)
           ave, rms = img.mean(), img.std()
           imsh.set_clim(ave-1*rms, ave+3*rms)
       show(mode=1)  # !!!!!!!!!!       
       #draw_fig(fig) # !!!!!!!!!!


  def usage():
    msg = 'Usage: python psalgos/examples/ex-02-localextrema.py <test-number>'\
          '\n  where <test-number> ='\
          '\n  1 - single 2d random image'\
          '\n  2 - single random histgram'\
          '\n  3 - in loop 2d random images'\
          '\n  4 - in loop random histgrams'\
          '\n  5 - in loop 2d large random images'
    print(msg)


  def do_test():
    from time import time
    from psana.pyalgos.generic.NDArrGenerators import random_standard; global random_standard

    if len(sys.argv)==1:
        print('Use command > python %s <test-number [1-5]>' % sys.argv[0])
        sys.exit ('Add <test-number> in command line...')

    tname = sys.argv[1] if len(sys.argv) > 1 else '1'
    print(50*'_', '\nTest %s' % tname)
    t0_sec=time()
    if   tname == '1': test01()
    elif tname == '2': test02()
    elif tname == '3': test03()
    elif tname == '4': test04()
    elif tname == '5': test05()
    else: usage(); sys.exit('Test %s is not implemented' % tname)
    msg = 'Test %s consumed time %.3f' % (tname, time()-t0_sec)
    show()
    sys.exit(msg)

#----

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s: %(message)s',\
                        datefmt='%m-%d-%Y %H:%M:%S',\
                        level=logging.INFO)

    import sys; global sys
    do_test()
    sys.exit('End of test')

#----

