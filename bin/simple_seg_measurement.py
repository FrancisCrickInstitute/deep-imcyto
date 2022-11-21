#!/usr/bin/env python

import skimage.io as io
import skimage.measure as measure
from skimage.segmentation import clear_border
import numpy as np
import pandas as pd
import os, glob, sys, argparse
from sklearn.neighbors import NearestNeighbors

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


def calc_neighbours(measurements, n_neighbours=5):
    # calculate object neighbours based on cell centroid position
    coords = measurements[['centroid-x', 'centroid-y']].values
    nbrs = NearestNeighbors(n_neighbors=n_neighbours, algorithm='kd_tree').fit(coords)
    distances, indices = nbrs.kneighbors(coords)

    neighbour_labels = indices+1
    neighbour_columns=['label'] + [f'neighbour_{i}_label' for i in range(n_neighbours-1)]
    neighbour_df = pd.DataFrame(data=neighbour_labels, columns=neighbour_columns)
    distance_columns = [f'distance_neighbour_{i}' for i in range(n_neighbours-1)]
    distance_df = pd.DataFrame(data=distances[:,1:], columns=distance_columns)
    # merge result:
    nearest_neighbours = pd.merge(neighbour_df, distance_df,  left_index=True, right_index=True)
    return nearest_neighbours


def main(args):

    full_stack_paths = glob.glob(os.path.join(args.input_dir, '*.tiff'))

    stack, markers = read_channels(full_stack_paths)

    mask = io.imread(args.label_image_path)

    mask = clear_border(mask)

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

    # calculate nearest neighbours and save output:
    neighbours = calc_neighbours(measurements, n_neighbours=args.n_neighbours)
    fname, ext = os.path.splitext(args.output_file)
    nbr_fname = fname + f"_neighbours_{args.n_neighbours}" + ext
    output_path = os.path.join(args.output_dir, nbr_fname)
    neighbours.to_csv(output_path, index=False)
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run basic measurement of intensity properties of all multiplex channels.')
    parser.add_argument('--input_dir', type=str, help='Directory containing multiplexed images.')
    parser.add_argument('--output_dir', type=str, help='Directory to write output to.')
    parser.add_argument('--output_file', type=str, help='File to write output to.', default='Cells.csv')
    parser.add_argument('--label_image_path', type=str, help='Path to label image to use for cell segmentation.')
    parser.add_argument('--n_neighbours', type=int, help='Number of nearest neighbours to calculate.', default=5)
    args = parser.parse_args()
    main(args)