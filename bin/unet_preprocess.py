#!/usr/bin/env python

from email import parser
import glob, os
import numpy as np
import skimage.io as io
from skimage.exposure import rescale_intensity, histogram
from skimage.util import img_as_uint, img_as_int
import sys
import argparse


def main(args):
   
    print('\n~~~INPUT CONFIG~~~')
    print('DNA image 1 path: ', args.dna1)
    print('DNA 2 path: ', args.dna2)
    print('percentage saturated pixels: ', args.sat)
    print('\n')

    # load DNA images:
    print('\n Performing preprocessing...')

    # read in images:
    im1 = io.imread(args.dna1)
    im2 = io.imread(args.dna2)

    # perform preprocessing:
    preprocessed = preprocess(im1, im2, args.sat)
    savename = f'{args.imagename}.png'
    save_im(args.outdir, preprocessed, savename)

    print('\nDone.')
    

def get_scan_paths(directory):
    directory_names = glob.glob(os.path.join(directory, '*/*/full_stack/'))
    return directory_names

def print_list(alist):
    for i in range(len(alist)):
        print(alist[i])

def load_dna_ims(full_stack_directory):
    dnalist = glob.glob(os.path.join(full_stack_directory, '*DNA*.tiff'))
    dnalist.sort()
    print_list(dnalist)
    dna1 = io.imread(dnalist[0])
    dna2 = io.imread(dnalist[1])
    return dna1, dna2

def savename_construct(path):
    splitpath = path.split('/')
    savename = '{}-{}_SUM_DNA.png'.format(splitpath[-4], splitpath[-3])
    # print(savename)
    return savename

def save_im(outdir, im, fname):
    if os.path.exists(outdir) != True:
        os.makedirs(outdir)
    save_path = os.path.join(outdir, fname)
    print('\nSaving contrast adjusted image to: {}'.format(save_path))
    io.imsave(save_path, im)

def preprocess(dna1, dna2, sat=0.1):
    # add channels to increase signal:
    add = add_ims(dna1, dna2).astype('uint16')
    # remove singleton dimension:
    add = np.squeeze(add)
    # change bit depth:
    _16bit = img_as_uint(add)
    # adjust contrast:
    adjusted = adjust_contrast(_16bit, sat)
    return img_as_int(adjusted)

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

def add_ims(im1, im2):
    summed = np.add(im1, im2)
    return summed

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Preprocess DNA images for use in UNET')
    parser.add_argument('--dna1', type=str, help='path to first DNA image')
    parser.add_argument('--dna2', type=str, help='path to second DNA image')
    parser.add_argument('--outdir', type=str, help='path to output directory')
    parser.add_argument('--sat', type=float, help='saturation level for contrast adjustment', default=0.1)
    parser.add_argument('--imagename', type=str, help='name of image to be saved', default='test')
    args = parser.parse_args()

    main(args)