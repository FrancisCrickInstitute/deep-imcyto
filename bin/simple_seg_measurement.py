#!/usr/bin/env python

import skimage.io as io
import skimage.measure as measure
from skimage.segmentation import clear_border
import numpy as np
import pandas as pd
import os, glob, sys, argparse
from sklearn.neighbors import NearestNeighbors
from sklearn import preprocessing
import matplotlib.gridspec as gridspec
import math
import matplotlib.pyplot as plt
import seaborn as sns

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
    return df, prop_named


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

def plot_channels(measurements_norm, image_shape, marker_measurements, prop, outdir='.'):
    nchannels = len(marker_measurements)
    height, width = image_shape[0], image_shape[1]
    num =  width / height
    ncols  = 7
    nrows = math.ceil(nchannels/7)
    
    fig = plt.figure(constrained_layout=True, figsize=(int(width/40),int(height/40)))
    gs = gridspec.GridSpec(nrows=nrows, ncols=ncols, figure=fig)


    for i, m in enumerate(marker_measurements):
        if i ==0:
            ax0 = fig.add_subplot(gs[i])
#             ax0.set_aspect(num)
            g = sns.scatterplot(data=measurements_norm, x='centroid-x', y='centroid-y', hue=m, size=1, ax=ax0, palette='magma')
            ax0.axis('off')
            ax0.get_legend().remove()
            ax0.set_title(m)
        else:
            ax = fig.add_subplot(gs[i], sharex=ax0, sharey=ax0)
            g = sns.scatterplot(data=measurements_norm, x='centroid-x', y='centroid-y', hue=m, size=1, ax=ax, palette='magma')
            ax.axis('off')
#             ax.set_aspect(num)
            ax.get_legend().remove()
            ax.set_title(m)

    # plt.legend(loc="lower left", mode = "expand", ncol = 3)
    handles, labels = ax.get_legend_handles_labels()
    legend = fig.legend(handles[:-1], labels[:-1], loc='upper center', ncol = 10, 
               labelspacing=2, bbox_to_anchor=(0.5, 1.075), 
                        title=f"Normalised cell marker intensity {prop}", 
                        fontsize=18, frameon=False, markerscale=5, scatterpoints=10)
    legend.get_title().set_fontsize('18') 
        
    spath = os.path.join(outdir, f'normalised_marker_intensity_{prop}.png')
    plt.savefig(spath, bbox_inches='tight')


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
    measurements, mean_properties_ids = rename_properties(measurements, 'mean_intensity', markers)
    measurements, std_properties_ids = rename_properties(measurements, 'std_intensity', markers)
    measurements, median_properties_ids = rename_properties(measurements, 'median_intensity', markers)
    
    # save measurements to csv:
    output_path = os.path.join(args.output_dir, args.output_file)
    measurements.to_csv(output_path, index=False)

    # calculate nearest neighbours and save output:
    neighbours = calc_neighbours(measurements, n_neighbours=args.n_neighbours)
    fname, ext = os.path.splitext(args.output_file)
    nbr_fname = fname + f"_neighbours_{args.n_neighbours}" + ext
    output_path = os.path.join(args.output_dir, nbr_fname)
    neighbours.to_csv(output_path, index=False)

    # make a summary spatial plot of each marker channel:
    x = measurements[mean_properties_ids].values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    measurements_norm = measurements
    measurements_norm[mean_properties_ids] = x_scaled
    plot_channels(measurements_norm, mask.shape, mean_properties_ids, 'mean', outdir='.')

    x = measurements[std_properties_ids].values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    measurements_norm = measurements
    measurements_norm[std_properties_ids] = x_scaled
    plot_channels(measurements_norm, mask.shape, std_properties_ids, 'standard_deviation', outdir='.')

    x = measurements[median_properties_ids].values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    measurements_norm = measurements
    measurements_norm[median_properties_ids] = x_scaled
    plot_channels(measurements_norm, mask.shape, median_properties_ids, 'median', outdir='.')
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run basic measurement of intensity properties of all multiplex channels.')
    parser.add_argument('--input_dir', type=str, help='Directory containing multiplexed images.')
    parser.add_argument('--output_dir', type=str, help='Directory to write output to.')
    parser.add_argument('--output_file', type=str, help='File to write output to.', default='Cells.csv')
    parser.add_argument('--label_image_path', type=str, help='Path to label image to use for cell segmentation.')
    parser.add_argument('--n_neighbours', type=int, help='Number of nearest neighbours to calculate.', default=5)
    args = parser.parse_args()
    main(args)