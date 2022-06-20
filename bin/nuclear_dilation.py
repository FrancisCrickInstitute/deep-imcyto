#!/usr/bin/env python

import skimage.io as io
from skimage.segmentation import expand_labels
import argparse
import os

def main(args):
    """
    Main function
    """
    # Load image
    img = io.imread(args.input_mask)
    # Perform nuclear dilation
    labels = expand_labels(img, args.radius)

    outdir = args.output_directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    fname = os.path.split(args.input_mask)[1]
    outname = os.path.join(outdir, fname.replace(f'.{args.input_format}', f'_nuclear_dilation.{args.output_format}'))

    # Save result
    io.imsave(outname, labels)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_mask', type=str, default='../data/test.png', help='Input image')
    parser.add_argument('--output_directory', type=str, default='./', help='Output image')
    parser.add_argument('--radius', type=int, default=5, help='Radius of the nuclear dilation')
    parser.add_argument('--input_format', type=str, default='tiff', help='Input image format', required=False)
    parser.add_argument('--output_format', type=str, default='tiff', help='Output image format', required=False)
    args = parser.parse_args()
    main(args)