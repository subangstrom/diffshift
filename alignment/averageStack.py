import os
import re
from fnmatch import fnmatch

import numpy as np
from tifffile import imsave


def fetchrawfile(folder):
    Path_Files = []
    for path,subdir,files in os.walk(folder):
        #print(path,files)
        for file in files:
            if fnmatch(file,'*.raw'):
                # print(file)
                Path_Files.append([path,file])
    return Path_Files

class creatAverageStack:

    def __init__(self,filepath,filename,num_patterns, shifts):

        self.num_patterns = num_patterns
        self.shifts = shifts

        patterns = np.fromfile(filepath +'/'+ filename, dtype='float32')
        patterns = patterns.reshape([self.num_patterns, 130,128])

        patterns = patterns[:,2:126,2:126]
        patterns = np.array([p for p in patterns if not np.all(np.isnan(p))])

        self.patterns = patterns

        self.patternSize = self.patterns[0,:,:].shape

        self.savepath = filepath + '/tifffiles'

        if not os.path.exists(self.savepath):
            os.mkdir(self.savepath)

    def savePatterns(self):
        imsave(self.savepath+'/'+'patterns.tif', self.patterns, shape=self.patterns.shape,  imagej=True)

    def averagePattern(self,data,xPositions):

        subData = data[xPositions[0]:xPositions[1],:,:]
        subAvg = np.mean(subData, 0)
        #subAvg = np.mean(subAvg,0)
        return subAvg

    def head_end_Patterns(self,num_ser):
        head = self.patterns[0:num_ser,:,:]
        end = self.patterns[self.num_patterns-num_ser-1:-1,:,:]
        #imsave(self.savepath+'/'+'averageStack.tif', self.patterns, shape=self.patterns.shape,  imagej=True)
        imsave(self.savepath+'/'+'patterns_head.tif', head, shape=head.shape,  imagej=True)
        imsave(self.savepath+'/'+'patterns_end.tif', end, shape=end.shape,  imagej=True)

    def mid_Patterns(self,start,end):
        mid = self.patterns[start:end,:,:]
        imsave(self.savepath+'/'+'patterns_mid.tif', mid, shape=mid.shape,  imagej=True)

    def serStack(self,start,dwell,skip):
        averagePatterns = np.zeros([self.shifts,self.patternSize[0], self.patternSize[1]],dtype='float32')
        count = 0
        # averagePatterns.dtype
        for i in range(start, (dwell+skip)*self.shifts, dwell+skip):
            half_skip = int(skip/2)
            avgPat = self.averagePattern(self.patterns,(i+half_skip,i+dwell+half_skip))
            avgPat = avgPat+1
            averagePatterns[count, :, :] = avgPat.astype('float32')
            count += 1
        # imsave(self.savepath+'/averageStack.tif', averagePatterns, shape=averagePatterns.shape, dtype='float32', imagej=True)

        # f = open(self.savepath+'info.txt','w+')
        # f.write('start:'+str(start))
        # f.write('dwell:'+str(dwell))
        # f.write('skip:'+str(skip))
        # f.close

        return averagePatterns
