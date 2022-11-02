#!/usr/bin/env python

import skimage.io as io
import skimage.measure as measure
import numpy as np
import pandas as pd
import os, glob, sys, argparse

def read_channels(paths):
    stack = []
    markers = []
    for p in paths:
        channel = io.imread(p)
        stack.append(channel)
        markername = os.path.splitext(os.path.split(p)[1])[0]
        markers.append(markername)
    stack = np.moveaxis(stack, 0, -1)
    stack = np.squeeze(stack)
    return stack, markers

def main(args):

    full_stack_paths = glob.glob(os.path.join(args.input_dir, '*.tiff'))

    stack, markers = read_channels(full_stack_paths)

    print("stack shape:", stack.shape)

    mask = io.imread(args.label_image_path)

    print("mask shape:", mask.shape)

    properties = ['label', 'area', 'eccentricity', 'perimeter', 'mean_intensity']
    measurements = measure.regionprops_table(label_image=mask, 
                            intensity_image=stack, 
                            properties=properties)
    measurements = pd.DataFrame(measurements)
    
    intensity_named = ['mean_intensity_'+ elem for elem in markers]
    intensity_numbered = [f'mean_intensity-{i}' for i in range(len(markers))]
    rename_dict = dict(zip(intensity_numbered,intensity_named))
    measurements = measurements.rename(columns=rename_dict)
    output_path = os.path.join(args.output_dir, args.output_file)
    measurements.to_csv(output_path, index=False)
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run basic measurement of intensity properties of all multiplex channels.')
    parser.add_argument('--input_dir', type=str, help='Directory containing multiplexed images.')
    parser.add_argument('--output_dir', type=str, help='Directory to write output to.')
    parser.add_argument('--output_file', type=str, help='File to write output to.', default='Cells.csv')
    parser.add_argument('--label_image_path', type=str, help='Path to label image to use for cell segmentation.')
    args = parser.parse_args()
    main(args)