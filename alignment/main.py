import re
from tifffile import imsave
import numpy as np
from Processing import AverageStack as AS
from matplotlib import pylab as plt

# fetch all the raw files and their directory
folder = '/Volumes/Seagate Backup Plus Drive/Xi_Si_111/Si111_30x80_ser9999_CL2o4_shifts100'
path_files = AS.fetchrawfile(folder)

#%% no shift write raw to tiff
shifts = 100
averagedstack = np.zeros([shifts, 124, 124])

for path, file in path_files:

    # print(index, path, file)
    start = 0
    index = re.findall('\d+(?=of)',path)
    # index = re.findall('(?<=shift_)\d*',path)
    index = int(index[0])

    dwell = re.findall('(?<=x)\d*',file)
    dwell = int(dwell[0])
    num_patterns = dwell
    skip = 0
    AverageStack = AS.creatAverageStack(path, file, num_patterns, 1)
    averagedpattern = AverageStack.serStack(start, dwell, skip)
    averagedstack[shifts - index, :, :] = averagedpattern

averagedstack = averagedstack.astype('float32')
imsave(folder + '/averagedStack.tif', averagedstack, shape=averagedstack.shape)

# %% export one shift raw to tiff
path = '/Volumes/Seagate Backup Plus Drive/TQD_20180702_Si/Si110_CL4o1_ser9999_area4'
file = 'series_93_x9999.raw'
num_patterns = 9999
AverageStack = AS.creatAverageStack(path, file, num_patterns, 1)
averagedpattern = AverageStack.serStack(0, 9999, 0)
averagedpattern = averagedpattern[0]
plt.imshow(np.log(averagedpattern))
savepath = '/Volumes/Seagate Backup Plus Drive/TQD_20180702_Si/Si110_CL4o1_ser9999_area4/tifffiles'
imsave(savepath + '/averagedStack.tif', averagedpattern, shape=averagedpattern.shape)

# %% regular autoshift: export patterns, head and end for estimate dwell
folder = '/Volumes/Seagate Backup Plus Drive/pmn30pt110P_diffshift'
Path_Files = AS.fetchrawfile(folder)
print(Path_Files)
#
for path,file in Path_Files[4:]:
    shifts = re.findall('\d+(?=shift)',path)
    shifts = int(shifts[0])
    num_patterns = re.findall('(?<=x)\d*',file)
    num_patterns = int(num_patterns[0])
    num_patterns_x = int(np.sqrt(shifts))
    num_patterns_y = int(np.sqrt(shifts))
    num_ser = int(num_patterns/(shifts-4))
    AverageStack = AS.creatAverageStack(path,file,num_patterns_x,num_patterns_y)
    #AverageStack.savePatterns()
    AverageStack.head_end_Patterns(num_ser)


path, file = Path_Files[4]

shifts = 64
num_patterns = re.findall('(?<=x)\d*',file)
num_patterns = int(num_patterns[0])
print(num_patterns)
AverageStack = AS.creatAverageStack(path, file, num_patterns, shifts)


# to save all the sub-patterns:
AverageStack.savePatterns()

start = 85000
end = start + 20000
AverageStack.mid_Patterns(start, end)

num_ser = 5000
AverageStack.head_end_Patterns(num_ser)


# create average stack:
# start = 206
# skip = 400
# dwell = 2681 - skip
# AverageStack.serStack(start,dwell,skip)
