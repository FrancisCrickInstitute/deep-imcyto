import skimame.io as io
from scipy.ndimage import maximum_filter
import numpy as np
import argparse
import glob, os

# from smoothmultichannel:

def clip_hot_pixels(img, hp_filter_shape, hp_threshold):
    '''
    Function to clip hot pixels from an image. This is the static method from
    the CellProfiler module smoothmultichannel.py. (Bodenmiller et al.)
    '''
    if hp_filter_shape[0] % 2 != 1 or hp_filter_shape[1] % 2 != 1:
        raise ValueError("Invalid hot pixel filter shape: %s" % str(hp_filter_shape))
    hp_filter_footprint = np.ones(hp_filter_shape)
    hp_filter_footprint[int(hp_filter_shape[0] / 2), int(hp_filter_shape[1] / 2)] = 0
    max_img = maximum_filter(img, footprint=hp_filter_footprint, mode='reflect')
    hp_mask = img - max_img > hp_threshold
    img = img.copy()
    img[hp_mask] = max_img[hp_mask]
    return img



def main(args):

    # params:
    filter_size = args.filter_size
    hot_pixel_threshold = args.hot_pixel_threshold
    hp_filter_shape = (filter_size, filter_size)

    # get list of images:
    imagelist = glob.glob(os.path.join(args.input_dir,f'*{args.file_exension}'))

    # process images:
    for path in imagelist:
        
        # read image and clip hot pixels:
        img = io.imread(path)
        fname = os.path.basename(path)
        clipped = clip_hot_pixels(img, hp_filter_shape, hot_pixel_threshold)
        
        # save to output dir:
        io.imsave(os.path.join(args.output_dir,fname), clipped)

    print('Done.')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Preprocess a directory of images with hot pixel removal")
    parser.add_argument("input_dir", help="Input folder")
    parser.add_argument("output_dir", help="Output folder")
    parser.add_argument("--filter_size", help="Size of the filter to use for hot pixel removal", type=int, default=3)
    parser.add_argument("--hot_pixel_threshold", help="Threshold for hot pixel removal", type=int, default=50)
    parser.add_argument("--file_extension", help="File extension of the input images", default=".tif")
    args = parser.parse_args()
    
    main(args)