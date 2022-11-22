#!/usr/bin/env python

import skimage.io as io
import numpy as np
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries
import os

def make_overlay(image, nuc, cell, nuc_bound, outdir, imagename):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    width = image.shape[1]
    height = image.shape[0]
    fig, ax = plt.subplots(1,1, dpi=1, figsize=(width, height))
    ax.imshow(image, cmap='gray')
    # ax.imshow(phe)
    ax.imshow(nuc, alpha=0.3, cmap='tab20', interpolation="nearest")
    ax.imshow(cell, alpha=0.25, cmap='tab20', interpolation="nearest")
    ax.imshow(nuc_bound, alpha=0.2, cmap='Reds', interpolation="nearest")

    plt.axis('off')
    plt.tight_layout()

    spath = os.path.join(outdir, imagename + '_segmentation_overlay.png')
    plt.savefig(spath, bbox_inches = 'tight', pad_inches = 0)

def main(args):

    nuc_label = io.imread(args.nuclear_segmentation)
    cell_label = io.imread(args.cell_segmentation)
    image = io.imread(args.image)
    nuc_boundaries = find_boundaries(nuc_label, connectivity=1, mode='inner')

    masked_nuc = np.ma.masked_where(nuc_label == 0, nuc_label)
    masked_cell = np.ma.masked_where(cell_label == 0, cell_label)
    masked_nuc_bound = np.ma.masked_where(nuc_boundaries == 0, nuc_boundaries)

    make_overlay(image, masked_nuc, masked_cell, masked_nuc_bound, args.outdir, args.imagename)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--nuclear_segmentation', type=str, required=True)
    parser.add_argument('--cell_segmentation', type=str, required=True)
    parser.add_argument('--image', type=str, required=True)
    parser.add_argument('--outdir', type=str, required=True)
    parser.add_argument('--imagename', type=str, required=True)
    args = parser.parse_args()
    main(args)