#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from PHE_functions import make_pseudo
import os
import skimage.io as io

def main(args):

        # Read in the image
        dna1 = io.imread(args.DNA_image_1)
        dna2 = io.imread(args.DNA_image_2)
        ruth = io.imread(args.ruthenium)
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
        parser.add_argument('-ruth', '--ruthenium', type=str, help='input ruthenium image', required=True)
        parser.add_argument('-i', '--imagename', type=str, help='image identifier', required=True)
        parser.add_argument('-o', '--outdir', type=str, help='output directory', default='./', required=True)
        args = parser.parse_args()
        main(args)
