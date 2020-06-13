%matplotlib
import glob
import os
import re

import numpy as np
from matplotlib import pylab as plt
from tifffile import imsave

from Processing import diffalign_cleanup as dfa

plt.rcParams.update({'font.size': 18,'font.weight':'bold','font.family':'Helvetica Neue','axes.linewidth':1.8,'ytick.major.width':2,'ytick.major.size':8,'xtick.major.width':2,'xtick.major.size':8})

#%%
filepath = '/Volumes/Seagate Backup Plus Drive/Xi_Si_111/Si111_30x80_ser9999_CL2o4_shifts100/averagedStack.tif'
deterctorsize = [128,128]
diffalign = dfa.diffalign(filepath,deterctorsize)

# display patterns
allPatterns = diffalign.displaypatterns()
diffalign.indexPatterns()

# select pattern for alignment
index = 10
range_x = 30
range_y = 40

# give initial value for alignment
[overlapx0,overlapy0,shiftx0,shifty0,rotation0] = [45, 45, 0, 0, 0]

[[overlapx,overlapy,shiftx,shifty],success] = diffalign.fit_overlapxy_shiftxy(index,overlapx0,overlapy0,shiftx0,shifty0,range_x,range_y)

print([[overlapx, overlapy, shiftx, shifty], success])

# check fitted parameters
expandedImages = diffalign.expandImages(diffalign.images, 150)
combined = diffalign.subpixelstitch(expandedImages, overlapx, overlapy, shiftx, shifty, 0)

plt.figure()
plt.imshow(np.log(combined))

imsave(savepath+'/combined.tif', combined, shape=combined.shape)
