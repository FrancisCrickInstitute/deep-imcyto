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

## Property function definitions:
def median_intensity(regionmask, intensity):
    return np.median(intensity[regionmask], axis=0)

def std_intensity(regionmask, intensity):
    return np.std(intensity[regionmask], axis=0)

def rename_properties(df, prop, markers):
    prop_named = [f'{prop}_'+ elem for elem in markers]
    prop_numbered = [f'{prop}-{i}' for i in range(len(markers))]
    rename_dict = dict(zip(prop_numbered,prop_named))
    df = df.rename(columns=rename_dict)
    return df

def main(args):

    full_stack_paths = glob.glob(os.path.join(args.input_dir, '*.tiff'))

    stack, markers = read_channels(full_stack_paths)

    print("stack shape:", stack.shape)

    mask = io.imread(args.label_image_path)

    print("mask shape:", mask.shape)

    # measure properties for all regions of label image:
    properties = ['label', 
                'centroid', 
                'area', 
                'eccentricity', 
                'solidity',
                'perimeter', 
                'minor_axis_length',
                'major_axis_length',
                'mean_intensity'] 

    measurements = measure.regionprops_table(label_image=mask, 
                            intensity_image=stack, 
                            properties=properties, 
                            extra_properties=(median_intensity,std_intensity))
    measurements = pd.DataFrame(measurements)
    
    # convert row,col centroids to x, y centroids:
    measurements['centroid-x'] = measurements['centroid-1']
    measurements['centroid-y'] =  measurements['centroid-0'].max() - measurements['centroid-0']
    
    # rename numeric columns to channel names:
    measurements = rename_properties(measurements, 'mean_intensity', markers)
    measurements = rename_properties(measurements, 'std_intensity', markers)
    measurements = rename_properties(measurements, 'median_intensity', markers)
    
    # save measurements to csv:
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