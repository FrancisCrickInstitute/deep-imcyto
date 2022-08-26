import sys
import argparse
import skimage.io as io
import pandas as pd
import re
import glob, os
import numpy as np
import scipy.optimize as spo

def sort_by_mass_number(metals):
    '''
    Sorts an iterable of metals in string format by mass number
    '''
    return sorted(metals, key=lambda x:int(re.search(r'\d+',x).group()))

def search_paths(paths, elem):
    for p in paths:
        if elem in p:
            return p

def compensate_image_ls(img, sm, method):
    """
    Compensate an img with dimensions (x, y, c) with a spillover matrix
    with dimensions (c, c) by first reshaping the matrix to the shape dat=(x*y,
    c) and the solving the linear system:
        comp * sm = dat -> comp = dat * inv(sm)

    Example: 
        >>> img = np.array([[[1,0.1],[0, 1], [1,0.1]],
                            [[0,1],[1,0.1], [2,0.2]]])
        >>> sm = np.array([[1,0.1],[0,1]])
        >>> compensate_image(sm, img)
        array([[[ 1.,  0.],
                [ 0.,  1.],
                [ 1.,  0.]],
               [[ 0.,  1.],
                [ 1.,  0.],
                [ 2.,  0.]]])

    Adapted for deepimcyto from correctspilloverapply.py cellprofiler plugin.
    """
    x, y ,c = img.shape
    dat = np.ravel(img, order='C')
    dat = np.reshape(dat,(x*y,c), order='C')
    if method == 'LS':
        compdat = np.linalg.lstsq(sm.T, dat.T)[0]
        compdat = compdat.T
    if method == 'NNLS':
        nnls = lambda x: spo.nnls(sm.T, x)[0]
        compdat = np.apply_along_axis(nnls,1, dat)
    compdat = compdat.ravel(order='C')
    comp_img = np.reshape(compdat, (x,y,c), order='C')
    return comp_img

def main(args):

    metadata = pd.read_csv(args.metadata)
    full_stack_paths = glob.glob(os.path.join(args.input_dir, f'*.{args.extension}'))
    spillover_metals = metadata[metadata['spillover'] == 1]['metal'].values
    sm = io.imread(args.spillover_matrix)

    # sort spillover metals by mass number:
    spillover_metals = sort_by_mass_number(spillover_metals)

    # search for spillover metals in full_stack_paths:
    spillover_paths = []
    labels = []
    for metal in spillover_metals:
        path = search_paths(full_stack_paths, metal)
        spillover_paths.append(path)
        label = os.path.basename(path)
        labels.append(label)

    # read the spillvoer channels into a stack in isotope order
    spillover_channels = []
    for path in spillover_paths:
        channel = io.imread(path)
        spillover_channels.append(channel)
    stack = np.concatenate(spillover_channels)
    stack = np.moveaxis(stack, 0, -1)

    # compensate the stack with the spillover matrix with desired method:
    compensated = compensate_image_ls(stack, sm, args.method)

    # save output compensated channels:
    outdir = args.outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        
    for i, label in enumerate(labels):
        print(i, label)
        comp_channel = compensated[:, :, i]
        comp_channel = np.squeeze(comp_channel)
        spath = os.path.join(outdir, label)
        io.imsave(spath, comp_channel)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Correct spillover of IMC images for Deep-imcyto')    
    parser.add_argument('--input', '-i', help='Input image directory', required=True)
    parser.add_argument('--outdir', '-o', help='Output image directory', required=True)
    parser.add_argument('--extension', '-e', help='file extension', default = '.tiff')
    parser.add_argument('--spillover_matrix', '-sm', help='Spillover image directory', required=True)
    parser.add_argument('--metadata', help='Metadata file indicating which IMC channels require spillover', required=True)
    parser.add_argument('--method', help='"LS" or "NNLS";  Method for correcting spillover: LeastSquares or NonNegativeLeastSquares', default = 'NNLS')
    args = parser.parse_args()
    main(args)