# TOOL FOR POSTPROCESSING NUCLEI PREDICTION IMAGES FROM NESTED U-NET
# OR U-NET SEGMENTATIONS WHERE NUCLEI AND TOUCHING REGIONS HAVE BEEN
# PREDICTED AS TWO SEPARATE PROBABILITY MAP IMAGES
# 
# prediction folders must contain same number of images with identical naming conventions
# to ensure each nuclear mask is watershed with the correct boundary prediction
# 
# contact: alastair.magness@crick.ac.uk
# to do: turn into an importable function module for direct use with 
# U-net

import glob, os
import skimage.io as io
import numpy as np
from skimage.morphology import watershed, remove_small_objects, opening, dilation, diamond
from scipy.ndimage.morphology import distance_transform_edt
from skimage.util import img_as_uint, invert, img_as_float32
from skimage.filters import threshold_otsu, gaussian
from scipy.ndimage import label

import numpy as np
import cupy as cp
from tqdm import *
from cupy import in1d
from skimage.morphology import closing, remove_small_objects
from skimage.util import img_as_ubyte, img_as_uint, img_as_float32


def PBW_rm_small_obj(nuc_results_path, boundary_results_path, COMS_results_path, watershed_results_path, thresh_nuc, thresh_COMS, min_obj_size=4, compactness=10):

    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image. This version includes a watershed line between objects.
    """

    # locations of predicted images from nested unet segmentation:

    boundary_im_path = os.path.join(boundary_results_path, '*predict.png')
    nuc_im_path = os.path.join(nuc_results_path, '*predict.png')
    COMS_im_path = os.path.join(COMS_results_path, '*predict.png')
    boundary_pred_ims = glob.glob(boundary_im_path)
    whole_nuc_pred_ims = glob.glob(nuc_im_path)
    COMS_pred_ims = glob.glob(COMS_im_path)

    print('\nData for probability basin watershed:')
    print(boundary_results_path)
    print(nuc_results_path)
    print(watershed_results_path)
    print(COMS_results_path)
    # print(boundary_pred_ims)
    # print(whole_nuc_pred_ims)

    for image in range(len(boundary_pred_ims)):
        # read in images:
        boundary_im = io.imread(boundary_pred_ims[image])
        nuc_im = io.imread(whole_nuc_pred_ims[image])
        COMS_im = io.imread(COMS_pred_ims[image])
        fname = os.path.split(os.path.splitext(boundary_pred_ims[image])[0])[1]

        # invert boundary image
        inverted_boundary_im = invert(boundary_im)

        # divide by 255 to produce probability image:
        prob_boundary_im = np.divide(inverted_boundary_im,255.)
        
        # do the same for the whole nucleus image
        prob_nuc_im = np.divide(nuc_im, 255.)
        
        # multiply nuclear probability image and inverse boundary to produce an image of nuclear regions
        # separated at points where there is a high probability of there being a boundary:
        nuclear_islands = np.multiply(prob_nuc_im, prob_boundary_im)
        
        # produce probability basins for watershed by inverting this image:
        prob_basins = invert(nuclear_islands)

        # produce binary COMS image:
        binary_COMS = COMS_im > thresh_COMS
        binary_COMS = img_as_uint(binary_COMS)

        # produce binary nucleus for masking watershed area:
        binary_nuc = nuc_im > thresh_nuc
        binary_nuc = img_as_uint(binary_nuc)

        # produce label markers for watershed from binary COMS image
        struct = [[0,1,0],[1,1,1], [0,1,0]]
        labelled_COMS = label(binary_COMS, structure=struct)[0]

        # perform watershed:
        watershed_im = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)

        # remove small objects:
        small_obj_removed = remove_small_objects(watershed_im, min_size=min_obj_size)

        # save as 16bit tiff if less than 2^16 gray values, 32 bit if not:
        if np.amax(small_obj_removed) <= 65536:
            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            savename = os.path.join(watershed_results_path, '{}_PBW_noline_smobj_rm.tiff'.format(fname))
            io.imsave(savename, small_obj_removed)
        else:
            # convert to 32bit float images:
            small_obj_removed = img_as_float32(small_obj_removed)

            #save as tiff
            savename = os.path.join(watershed_results_path, '{}_PBW_noline_smobj_rm.tiff'.format(fname))
            io.imsave(savename, small_obj_removed)

def PBW_image(boundary_im, nuc_im, COMS_im, thresh_COMS, thresh_nuc, min_obj_size=4, compactness=0):

    # invert boundary image
    inverted_boundary_im = invert(boundary_im)

    # divide by 255 to produce probability image:
    prob_boundary_im = np.divide(inverted_boundary_im,255.)

    # do the same for the whole nucleus image
    prob_nuc_im = np.divide(nuc_im, 255.)

    # multiply nuclear probability image and inverse boundary to produce an image of nuclear regions
    # separated at points where there is a high probability of there being a boundary:
    nuclear_islands = np.multiply(prob_nuc_im, prob_boundary_im)

    # produce probability basins for watershed by inverting this image:
    prob_basins = invert(nuclear_islands)

    # produce binary COMS image:
    binary_COMS = COMS_im > thresh_COMS
    binary_COMS = img_as_uint(binary_COMS)

    # produce binary nucleus for masking watershed area:
    binary_nuc = nuc_im > thresh_nuc
    binary_nuc = img_as_uint(binary_nuc)

    # produce label markers for watershed from binary COMS image
    struct = [[0,1,0],[1,1,1], [0,1,0]]
    labelled_COMS = label(binary_COMS, structure=struct)[0]

    # perform watershed:
    watershed_im = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)

    # remove small objects:
    small_obj_removed = remove_small_objects(watershed_im, min_size=min_obj_size)
    
    return small_obj_removed

def instance_closing(seg_mask, strel = None):

    print('segmaskdtype: ', seg_mask.dtype)
    print('maxgray = ', np.amax(seg_mask), 'unique: ', len(np.unique(seg_mask)))
    if (seg_mask.dtype == 'uint16'):
        seg_mask = cp.asarray(seg_mask, dtype='uint16')
    else:
        seg_mask = cp.asarray(seg_mask, dtype='float32')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask.shape[0], seg_mask.shape[1], len(predict_labels))
    print(pred_array_size)

    # define empty image:
    empty = cp.zeros([seg_mask.shape[0], seg_mask.shape[1]])
    print('empty shape initial: ', empty.shape)

    # pad predict labels and empty to rpevent negative padding for instnaces:
    image_pad = 10

    # pad empty image and 16bit mask so closing on edges with padded instance works:
    empty = cp.pad(empty, (image_pad, image_pad), 'constant', constant_values=0)
    print('empty shape pad: ', empty.shape)

    seg_mask = cp.pad(seg_mask, (image_pad, image_pad), mode='constant', constant_values=0)
    print('seg_mask shape pad: ', seg_mask.shape)

    if len(predict_labels>0):

        # generate set of instance masks as numpy array:
#         for i in tqdm(range(len(predict_labels)), ascii=True):  
        for i, lbl in tqdm(enumerate(predict_labels), ascii=True):

            # make 8bit mask to house instance mask:
            predict_mask = cp.zeros(seg_mask.shape[:2], dtype = "uint8")

            # turn unique predict labels in instance mask:
            predict_mask[in1d(seg_mask, lbl).reshape(predict_mask.shape)] = 255

            # get nonzero indices:
            nuc_indices = cp.nonzero(predict_mask)

            # get bounding box of instance:
            min_rows = cp.amin(nuc_indices[0]) #.min()
            max_rows = cp.amax(nuc_indices[0]) + 1 #.max()
            min_cols = cp.amin(nuc_indices[1]) #.min()
            max_cols = cp.amax(nuc_indices[1]) + 1 #.max()

            # create instance:
            instance = predict_mask[min_rows:max_rows,min_cols:max_cols]
            
            # instance padding:
            instance_pad = 5

            # pad to allow closing:
            pad_instance = cp.pad(instance, (instance_pad, instance_pad), 'constant', constant_values=0)

            # convert to numpy:
            pad_instance = cp.asnumpy(pad_instance)

            pad_instance = img_as_ubyte(pad_instance)

            # perform closing:
            instance_closed = closing(pad_instance, strel)

            #convert back to cupy:
            instance_closed = cp.asarray(instance_closed)

            # define padding:
            before_rows = int(min_rows - instance_pad)
            after_rows = int(seg_mask.shape[0] - (max_rows + instance_pad))

            before_cols = int(min_cols - instance_pad)
            after_cols = int(seg_mask.shape[1] - (max_cols + instance_pad))

            # pad to original image dimensions:
            pad_closed = cp.pad(instance_closed, ((before_rows, after_rows), (before_cols, after_cols)), 'constant', constant_values=0)

            # convert to float to prevent saturation during summation:
            pad_closed = pad_closed.astype("float")

            # reconstruct label image:
            if i == 0:
                pad_closed = cp.where(pad_closed, 1, 0)
                label_im = empty + pad_closed
            else:
                # label_im = label_im + np.where(opened, i, 0)
                open_label = cp.where(pad_closed, lbl, 0)
                label_im = cp.where(label_im, label_im, open_label)
    else:
        label_im = empty


    # unpad and convert to numpy::
    label_im = label_im[image_pad:-image_pad, image_pad:-image_pad]
    label_im = cp.asnumpy(label_im)

    print('maxgray = ', np.amax(label_im), 'unique: ', len(np.unique(label_im)))
    if ((np.amax(label_im) <= 65536) or (len(np.unique(label_im)) <= 65536)):
        label_im = label_im.astype('uint16')
        label_im = remove_small_objects(label_im, min_size=4)
        instance_closed_im = img_as_uint(label_im)

    else:
        label_im = label_im.astype('uint32')
        label_im = remove_small_objects(label_im, min_size=4)
        instance_closed_im = img_as_float32(label_im)

    return instance_closed_im


