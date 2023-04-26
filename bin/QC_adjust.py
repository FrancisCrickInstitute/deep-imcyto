#!/usr/bin/env python

import skimage.io as io
from skimage.util import img_as_uint
import numpy as np
import os, glob
import matplotlib.pyplot as plt
from skimage.exposure import rescale_intensity, histogram
from skimage.util import img_as_uint, img_as_int
from tqdm import *
from skimage.filters import rank
import argparse

def median_filter(img):
    selem = np.array([[0,1,0], [1,1,1], [0,1,0]])
    img = img_as_int(img)
    result = rank.median(img, selem=selem)
    return result

def adjust_contrast(im, saturation=0.1):
    # get min and max for contrast adjustment:
    hmin, hmax = get_min_and_max(im, saturation)
    # rescale intensity:
    rescaled = rescale_intensity(im, in_range=(hmin, hmax))
    return rescaled

def get_min_and_max(im, saturated):

    """Python port function of the java code used within Fiji/ImageJ for contrast adjustment based on a proportion of saturated pixels.
    """
    # get image histogram:
    hist = histogram(im, source_range='dtype')
    hsize = len(hist[0])
    # print('hsize: ', hsize)

    if (saturated>0.0):
        # threshold of saturated pixels that must not be exceed [input is given as percentage]:
        threshold = ((im.shape[0] * im.shape[1])*saturated)/200.0 # intuition says this should be 100, but java source is 200; kept as 200 for concordance
    else:
        threshold = 0
    
    # Perform loops to find adjusted min and max of histogram
    i = -1
    found = False
    count = 0
    maxindex = hsize#-1

    # loop forwards from low end of histogram to find bottom value of adjusted histogram:
    while (found == False and i<maxindex):
        i+=1
        count += hist[0][i]
        found = count>threshold

    hmin = i

    # re-initialise counters for reverse loop:
    found = False
    i = hsize
    count = 0

    # loop backwards from top end of histogram to find max value of adjusted histogram:
    while (found == False and i>0):
        i-=1
        count += hist[0][i]
        found = count>threshold

    hmax = i

    return hmin, hmax

def main(args):

    imglist = glob.glob(os.path.join(args.input, f'*.{args.format}'))

    imglist.sort()

    root_out = args.outdir

    for path in tqdm(imglist, ascii=True):

        print(path)
        
        # normalise
        img = io.imread(path)
        img = np.squeeze(img)
        img = img_as_uint(img.astype('uint16'))
        norm = adjust_contrast(img)
        _, fname = os.path.split(path)

        norm = img_as_uint(norm)


        if args.save_intermediates:
            normdir = os.path.join(root_out, "contrast_adjusted")
            print('Contrast_adjusted image destination:', normdir)
            if not os.path.exists(normdir):
                os.makedirs(normdir)
            norm_fname = fname.replace('.tiff', '_contrast_adjusted.png')
            io.imsave(os.path.join(normdir, norm_fname), norm)

        # filter:
        filtered = median_filter(norm)
        fdir = os.path.join(root_out, "CA_median_filtered")
        print('Filtered image destination:', fdir)
        if not os.path.exists(fdir):
            os.makedirs(fdir)
        filtered_fname = fname.replace('.tiff', '_camf.png')
        io.imsave(os.path.join(fdir, filtered_fname), filtered)

    print('Done!')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Adjust contrast and median filter images.')
    parser.add_argument('--input', type=str, help='Input directory')
    parser.add_argument('--format', type=str, help='Image format', default='tiff')
    parser.add_argument('--save_intermediates', type=bool, help='Save intermediate images', default=False)
    parser.add_argument('--outdir', type=str, help='Output directory', default='./QC_visualisations')
    args = parser.parse_args()
    main(args)