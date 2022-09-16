#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from PHE_functions import make_pseudo
import os, glob
import skimage.io as io
import numpy as np

def main(args):

        # Read in the image
        dna1 = io.imread(args.DNA_image_1)
        dna2 = io.imread(args.DNA_image_2)
        
        counterstain_imagelist = glob.glob(os.path.join(args.counterstain_dir, f'*{args.img_type}'))
        images = []
        for path in counterstain_imagelist:
                img = io.imread(path)
                images.append(img)
        images = np.asarray(images)
        print(images.shape)
        stack = np.concatenate(images)
        stack = np.moveaxis(stack, 0, -1)
        ruth = np.sum(stack, axis=-1)

        pseudo = make_pseudo(dna1, dna2, ruth) # Make the pseudo-H&E image

        # make output path
        out = args.outdir
        if not os.path.exists(out):
                os.makedirs(out)

        savepath = os.path.join(out, f'{args.imagename}.png')

        # Save the image
        io.imsave(savepath, pseudo)


if __name__ == "__main__":
        parser = argparse.ArgumentParser(description='Make pseudo H&E image from input DNA and ruthenium IMC tiff images.')
        parser.add_argument('-dna1', '--DNA_image_1', type=str, help='input DNA image 1', required=True)
        parser.add_argument('-dna2', '--DNA_image_2', type=str, help='input DNA image 2', required=True)
        parser.add_argument('-c_dir', '--counterstain_dir', type=str, help='directory containing counterstain image channels', required=True)
        parser.add_argument('-i', '--imagename', type=str, help='image identifier', required=True)
        parser.add_argument('-o', '--outdir', type=str, help='output directory', default='./', required=True)
        parser.add_argument('-type', '--img_type', type=str, help='image type', default='.tiff')
        args = parser.parse_args()
        main(args)
