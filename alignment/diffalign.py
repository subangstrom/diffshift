import cv2
import numpy as np
import scipy
import scipy.optimize
from matplotlib import pylab as plt
from skimage import io
from skimage.transform import AffineTransform, warp



class diffalign:

    def __init__(self, filepath):

        images = io.imread(filepath)
        self.images = np.array([p for p in images[::-1]])
        self.size = self.images.shape
        self.num_patterns = int(np.sqrt(self.size[0]))
        self.deterctorsize = self.size[1]

    def select_images(self, indexs):
        # this function is used to select a set of sub-patterns for alignment:

        alignImages = np.zeros([len(indexs), self.size[1], self.size[2]])

        for num, index in enumerate(indexs, start=0):
            alignImages[num, :, :] = self.images[int(index), :, :]

        return alignImages

    def expandImages(self, images, width, overlap=0.1):
        # this function zeropad all the sub-patterns to the size of the final image with a extra width at the edge
        # width: is the extra width at the edge of the final image
        # overlap: an esitimation of the overlap percent between sub-patterns

        size = images.shape
        num_patterns = int(np.sqrt(size[0]))
        finalsize = 2 * width + int(num_patterns * size[1] * (1-overlap) + size[1] * overlap)
        expanded_images = np.zeros([size[0], finalsize, finalsize])
        counter = 0

        for image in images:
            holdingPattern = np.zeros([finalsize, finalsize])

            holdingPattern[width:width + size[1], width:width + size[1]] = image
            expanded_images[counter] = holdingPattern
            counter += 1

        return expanded_images

    def displaypatterns(self):

        expandedImages = self.expandImages(self.images, self.num_patterns+5, overlap=0)
        v = self.deterctorsize + 1
        combined = self.subpixelstitch(expandedImages, [v, 0], [0, v])

        plt.figure()
        plt.imshow(np.log(combined))
        plt.show()
        return combined

    def indexPatterns(self):

        counter = 0

        for i in range(1, self.num_patterns + 1):
            for j in range(1, self.num_patterns + 1):
                x = (i - 1) * self.size[1] + self.size[1] / 2
                y = (self.num_patterns - j) * self.size[2] + self.size[2] / 2

                plt.text(x, y, str(counter))
                counter = counter + 1

    def subpixelshift(self, image, vector):

        transform = AffineTransform(translation=[-vector[0],-vector[1]])
        shifted = warp(image, transform, mode='wrap', order=1, preserve_range=True)
        shifted = shifted.astype(image.dtype)

        ones = shifted > 0
        ones = ones.astype('uint8')
        kernel = np.ones((5, 5), np.uint8)
        erosion = cv2.erode(ones, kernel, iterations=1)

        return_image = shifted * erosion

        return return_image

    def caldifference_X_sub(self, image1, image2, range_x, range_y):
        imsize = image1.shape[0]
        residual = (image1[imsize - range_x:imsize, range_y:imsize - range_y] - image2[imsize - range_x:imsize, range_y:imsize - range_y]) / image1[imsize - range_x:imsize, range_y:imsize - range_y] * 100
        return residual

    def caldifference_Y_sub(self, image1, image2, range_x, range_y):
        imsize = image1.shape[0]
        residual = (image1[range_x:imsize - range_x, imsize - range_y:] - image2[range_x:imsize - range_x, imsize - range_y:]) / image1[range_x:imsize - range_x, imsize - range_y:] * 100
        return residual

    def fit_v1_v2(self, index, v1_0, v2_0, range_x, range_y):

        center = self.images[index].astype(np.float64)

        top = self.images[index + 1].astype(np.float64)
        bottom = self.images[index - 1].astype(np.float64)

        right = self.images[index + self.num_patterns, :, :].astype(np.float64)
        left = self.images[index - self.num_patterns, :, :].astype(np.float64)

        def errfun(x):

            vector1 = [x[0], x[1]]

            center_shifted = self.subpixelshift(center, vector1)
            right_shifted = self.subpixelshift(right, vector1)

            residual_left = self.caldifference_Y_sub(center_shifted, left, range_y, range_x)
            residual_right = self.caldifference_Y_sub(right_shifted, center, range_y, range_x)

            residualy = np.append(np.ravel(residual_left), np.ravel(residual_right))

            vector2 = [x[2], x[3]]

            center_shifted = self.subpixelshift(center, vector2)
            bottom_shifted = self.subpixelshift(bottom, vector2)

            residual_top = self.caldifference_X_sub(center_shifted, top, range_x, range_y)
            residual_bottom = self.caldifference_X_sub(bottom_shifted, center, range_x, range_y)

            residualx = np.append(np.ravel(residual_top), np.ravel(residual_bottom))

            error = np.append(residualx, residualy)

            return error

        v1xy_v2xy = scipy.optimize.leastsq(errfun, [v1_0[0], v1_0[1], v2_0[0], v2_0[1]])

        return v1xy_v2xy

    def subpixelstitch(self, expandedImages, v1, v2):

        n = np.zeros((expandedImages.shape[1], expandedImages.shape[2]), dtype='float32')

        combined = np.zeros((expandedImages.shape[1], expandedImages.shape[2]), dtype='float32')

        num_patterns = int(np.sqrt(expandedImages.shape[0]))

        for counter, image in enumerate(expandedImages, start=0):
            row = int(num_patterns-1-counter % num_patterns)
            column = int(counter / num_patterns)

            vector = [v1[0] * column + v2[0] * row, v2[1] * row + v1[1] * column]
            processed = self.subpixelshift(image, vector)
            combined += processed
            n += processed != 0

        combined = combined*(1/n*(n > 0))*(n > 0)

        return combined
