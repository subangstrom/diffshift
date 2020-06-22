import numpy as np
from matplotlib import pylab as plt
from tifffile import imsave
from alignment import diffalign as dfa

#
filepath = '/Users/xi/Dropbox (MIT)/diffshift_paper/datas/Si_[111]_1o2m_81/Si_111_1o2m_250x250_81shifts_6600avepatterns.tif'
savepath = '/Users/xi/Dropbox (MIT)/diffshift_paper/datas/Si_[111]_1o2m_81'

diffalign = dfa.diffalign(filepath)

# display patterns
allPatterns = diffalign.displaypatterns()
diffalign.indexPatterns()

# select pattern for alignment
index = 40
range_x = 40
range_y = 10

# give initial value for alignment
v1_0 = [70, 0]
v2_0 = [0, 70]
[[v1_x, v1_y, v2_x, v2_y], success] = diffalign.fit_v1_v2(index, v1_0, v2_0, range_x, range_y)

print([[v1_x, v1_y, v2_x, v2_y], success])

# check fitted parameters
expandedImages = diffalign.expandImages(diffalign.images, 150)
combined = diffalign.subpixelstitch(expandedImages, [v1_x, v1_y], [v2_x, v2_y])

plt.figure()
plt.imshow(np.log(combined))

# imsave(savepath+'/combined.tif', combined, shape=combined.shape)

