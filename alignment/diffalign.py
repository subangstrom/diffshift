import cv2
import numpy as np
import scipy
import scipy.optimize
from matplotlib import pylab as plt
from scipy import signal
from skimage import io
from skimage.transform import AffineTransform, warp
from skimage.transform import rotate


class diffalign:

    def __init__(self,filepath,deterctorsize):

        images = io.imread(filepath)
        self.images = np.array([p for p in images[::-1]])
        self.size = self.images.shape
        self.num_patterns = int(np.sqrt(self.size[0]))
        self.deterctorsize = deterctorsize

    def select_images(self,indexs):
        alignImages = np.zeros([len(indexs),self.size[1],self.size[2]])

        for num,index in enumerate(indexs,start = 0):
            alignImages[num,:,:] = self.images[int(index),:,:]

        # self.alignImages = alignImages

        return alignImages


    def expandImages(self,images,width):

        Size = images.shape
        num_patterns = int(np.sqrt(Size[0]))
        size = 2*width+num_patterns*Size[1]
        expanded_images = np.zeros([Size[0],size,size])
        counter = 0

        for image in images:
            holdingPattern = np.zeros([size,size])
            row = int(width + (num_patterns-1-counter%num_patterns)*self.size[1])
            column = int(width + int(counter/num_patterns)*Size[1])
            holdingPattern[row:row+Size[1],column:column+Size[1]] = image
            expanded_images[counter] = holdingPattern
            counter += 1

        return expanded_images

    def displaypatterns(self):

        expandedImages = self.expandImages(self.images,10)
        combined = self.subpixelstitch(expandedImages,0,0,0,0,0)

        plt.figure()
        plt.imshow(np.log(combined))
        plt.show()
        return combined

    def indexPatterns(self):

        counter = 0

        for i in range(1,self.num_patterns+1):
            for j in range(1,self.num_patterns+1):

                x = (i-1)*self.size[1] + self.size[1]/2
                y = (self.num_patterns-j)*self.size[2] + self.size[2]/2

                plt.text(x,y,str(counter))
                counter = counter + 1

    def pixel_align(self,index):

        center = np.log(self.images[index].astype(np.float64))
        top = np.log(self.images[index+1].astype(np.float64))
        left = np.log(self.images[index-self.num_patterns,:,:].astype(np.float64))

        corr = signal.correlate2d(top, center, boundary='symm', mode='same')
        y, x = np.unravel_index(np.argmax(corr), corr.shape)

        overlapy0 = self.size[1] - 1 - y + self.size[1]/2
        shiftx0 = self.size[1]/2 - x

        corr = signal.correlate2d(left, center, boundary='symm', mode='same')
        y, x = np.unravel_index(np.argmax(corr), corr.shape)

        overlapx0 = self.size[1] - 1 - x + self.size[1]/2
        shifty0 = self.size[1]/2 - y

        return overlapx0,overlapy0,shiftx0,shifty0

    def subpixelshift_rotate(self,image,vector,rotation):

        transform = AffineTransform(translation=vector)
        shifted = warp(image, transform, mode='wrap',order = 1, preserve_range=True)
        shifted = shifted.astype(image.dtype)
        shifted_rotated = rotate(shifted,rotation,order=1,mode='constant', cval=0.0)

        ones = shifted_rotated > 0
        ones = ones.astype('uint8')
        kernel = np.ones((5,5),np.uint8)
        erosion = cv2.erode(ones,kernel,iterations = 1)

        return_image = shifted_rotated*erosion

        return return_image

    def caldifference_X_sub(self,image1,image2,range_x,range_y):
        imsize = image1.shape[0]
        residual = (image1[imsize-range_x:imsize,range_y:imsize-range_y]-image2[imsize-range_x:imsize,range_y:imsize-range_y])/image1[imsize-range_x:imsize,range_y:imsize-range_y]*100
        return residual

    def caldifference_Y_sub(self,image1,image2,range_x,range_y):
        imsize = image1.shape[0]
        residual = (image1[range_x:imsize-range_x,imsize-range_y:]-image2[range_x:imsize-range_x,imsize-range_y:])/image1[range_x:imsize-range_x,imsize-range_y:]*100
        return residual

    def fit_overlapxy_shiftxy(self,index,overlapx0,overlapy0,shiftx0,shifty0,range_x,range_y):

        center = self.images[index].astype(np.float64)

        top = self.images[index+1].astype(np.float64)
        bottom = self.images[index-1].astype(np.float64)

        right = self.images[index+self.num_patterns,:,:].astype(np.float64)
        left = self.images[index-self.num_patterns,:,:].astype(np.float64)

        def errfun(overlapxy_shiftxy):

            vector = [overlapxy_shiftxy[2],overlapxy_shiftxy[1]]
            # vector = [0,overlapxy_shiftxy[1]]

            center_shiftedrotated = self.subpixelshift_rotate(center,vector,0)
            top_rotated = self.subpixelshift_rotate(top,[0,0],0)
            bottom_shiftedrotated = self.subpixelshift_rotate(bottom,vector,0)
            center_rotated = self.subpixelshift_rotate(center,[0,0],0)

            residual_top = self.caldifference_X_sub(center_shiftedrotated,top_rotated,range_x,range_y)
            residual_bottom = self.caldifference_X_sub(bottom_shiftedrotated,center_rotated,range_x,range_y)

            residualx = np.append(np.ravel(residual_top),np.ravel(residual_bottom))

            vector = [overlapxy_shiftxy[0],overlapxy_shiftxy[3]]
            # vector = [overlapxy_shiftxy[0],0]

            center_shiftedrotated = self.subpixelshift_rotate(center,vector,0)
            left_rotated = self.subpixelshift_rotate(left,[0,0],0)
            right_shiftedrotated = self.subpixelshift_rotate(right,vector,0)
            center_rotated = self.subpixelshift_rotate(center,[0,0],0)

            residual_left = self.caldifference_Y_sub(center_shiftedrotated,left_rotated,range_y,range_x)
            residual_right = self.caldifference_Y_sub(right_shiftedrotated,center_rotated,range_y,range_x)

            residualy = np.append(np.ravel(residual_left),np.ravel(residual_right))

            error = np.append(residualx,residualy)

            return error

        overlapxy_shiftxy = scipy.optimize.leastsq(errfun, [overlapx0,overlapy0,shiftx0,shifty0])

        return overlapxy_shiftxy


    def subpixelstitch(self,expandedImages,overlap_x,overlap_y,shiftx,shifty,rotation):

        n = np.zeros((expandedImages.shape[1],expandedImages.shape[2]),dtype='float32')
        combined = np.zeros((expandedImages.shape[1],expandedImages.shape[2]),dtype='float32')

        num_patterns = int(np.sqrt(expandedImages.shape[0]))

        for counter,image in enumerate(expandedImages,start = 0):

            row = int(num_patterns-1-counter%num_patterns)
            column = int(counter/num_patterns)

            vector = [overlap_x*column + shiftx*row, overlap_y*row + shifty*column]
            processed = self.subpixelshift_rotate(image,vector,rotation)

            combined += processed
            n += processed != 0


        combined=combined*(1/n*(n>0))

        return combined

    def calculate_residual(self,pattern1,pattern2):

        mask = np.zeros(pattern1.shape,dtype='float32')
        residual =pattern1 - pattern2

        mask += pattern1 != 0
        mask += pattern2 != 0
        mask = mask > 1

        residual = np.divide(residual, pattern1, out=np.zeros_like(residual), where=pattern1!=0)*mask

        return residual



    def get_residuals(self,expandedImages,overlapx,overlapy,shiftx,shifty,rotation):

        num_patterns = int(np.sqrt(expandedImages.shape[0]))
        processed_images = np.zeros(expandedImages.shape)
        residuals = np.zeros(expandedImages[0].shape)
        n = np.zeros(expandedImages[0].shape,dtype='float32')

        for counter,image in enumerate(expandedImages,start = 0):

            row = int(num_patterns-1-counter%num_patterns)
            column = int(counter/num_patterns)

            vector = [overlapx*column + shiftx*row, overlapy*row+shifty*column]

            processed = self.subpixelshift_rotate(image,vector,rotation)
            processed_images[counter,:,:] = processed



        for location in range(num_patterns*(num_patterns-1)):

            index_left = int(location)
            index_right = int(location + num_patterns)
            index_down = int(location/num_patterns + location%num_patterns*num_patterns)
            index_top = int(index_down + 1)

            residualx = self.calculate_residual(processed_images[index_left],processed_images[index_right])
            residualy = self.calculate_residual(processed_images[index_down],processed_images[index_top])

            residual = residualx + residualy
            residuals += residual

            n += residualx != 0
            n += residualy != 0

        residuals = residuals*(1/n*(n>0))

        return residuals
