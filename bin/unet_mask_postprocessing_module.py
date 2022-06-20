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



def mask_watershed(nuc_results_path, boundary_results_path, watershed_results_path, thresh_nuc, thresh_boundary):

    # locations of predicted images from nested unet segmentation:

    boundary_im_path = os.path.join(boundary_results_path, '*predict.png')
    nuc_im_path = os.path.join(nuc_results_path, '*predict.png')
    boundary_pred_ims = glob.glob(boundary_im_path)
    whole_nuc_pred_ims = glob.glob(nuc_im_path)

    print(boundary_results_path)
    print(nuc_results_path)
    print(watershed_results_path)
    print(boundary_pred_ims)
    print(whole_nuc_pred_ims)

    for image in range(len(boundary_pred_ims)):
        # read in images:
        boundary_im = io.imread(boundary_pred_ims[image])
        nuc_im = io.imread(whole_nuc_pred_ims[image])
        fname = os.path.split(os.path.splitext(boundary_pred_ims[image])[0])[1]

        # calculated threshold for mask image from prediction image:
        # thresh_boundary = threshold_otsu(boundary_im) * 0.2 # lower threshold for boundaries
        # thresh_nuc = threshold_otsu(nuc_im) # >95% confidence for nuclei
        # thresh_nuc = 255 * 0.95 # >95% confidence for nuclei
        
        # create binary images:
        binary_boundary = boundary_im > thresh_boundary
        binary_nuc = nuc_im > thresh_nuc

        # convert to uint16 for watershed:
        binary_boundary = img_as_uint(binary_boundary)
        binary_nuc = img_as_uint(binary_nuc)
        
        # perform watershed:
        watershed_im = watershed(binary_boundary, markers=None, connectivity=1, offset=None, mask=binary_nuc,
                compactness=0, watershed_line=False)
        watershed_im = img_as_uint(watershed_im)

        # save output:
        savename = os.path.join(watershed_results_path, '{}_watershed.tif'.format(fname))
        io.imsave(savename, watershed_im)

def prob_basin_watershed(nuc_results_path, boundary_results_path, COMS_results_path, watershed_results_path, thresh_nuc, thresh_COMS):
    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image.
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

        watershed_im = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=0, watershed_line=False)

        # convert to 16bit integer images:
        watershed_im = img_as_uint(watershed_im)

        # save output:
        savename = os.path.join(watershed_results_path, '{}_PBW_noline.png'.format(fname))
        io.imsave(savename, watershed_im)

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

def PBW_rm_small_obj_w_pp_open_dilate(nuc_results_path, boundary_results_path, COMS_results_path, watershed_results_path, thresh_nuc, thresh_COMS, min_obj_size=4):

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
        watershed_im = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=0, watershed_line=False)

        # remove small objects:
        small_obj_removed = remove_small_objects(watershed_im, min_size=min_obj_size)

        # convert to 16bit integer images:
        small_obj_removed = img_as_uint(small_obj_removed)

        selem = diamond(1)

        opened = opening(small_obj_removed, selem=None)

        # dilated = dilation(opened, selem = None)

        # save output:
        savename = os.path.join(watershed_results_path, '{}_PBW_rm_small_obj_w_pp_open.png'.format(fname))
        io.imsave(savename, opened)

def prob_basin_watershed_wline(nuc_results_path, boundary_results_path, COMS_results_path, watershed_results_path, thresh_nuc, thresh_COMS):

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

        watershed_im_wline = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=0, watershed_line=True)

        # convert to 16bit integer images:
        watershed_im_wline = img_as_uint(watershed_im_wline)

        # save output:
        savename = os.path.join(watershed_results_path, '{}_PBW_wline.png'.format(fname))
        io.imsave(savename, watershed_im_wline)

def PBW_wline_rm_small_obj(nuc_results_path, boundary_results_path, COMS_results_path, watershed_results_path, thresh_nuc, thresh_COMS, min_obj_size=4):

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
        watershed_im_wline = watershed(prob_basins, labelled_COMS, connectivity=1, offset=None, mask=binary_nuc, compactness=0, watershed_line=True)

        # remove small objects:
        small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

        # convert to 16bit integer images:
        small_obj_removed = img_as_uint(small_obj_removed)

        # save output:
        savename = os.path.join(watershed_results_path, '{}_PBW_wline_smobj_rm.png'.format(fname))
        io.imsave(savename, small_obj_removed)

def multi_model_watershed(multi_model_results_path, watershed_results_path, thresh_nuc = 100, thresh_com = 150, min_obj_size=4, compactness = 10,
                            line = True):

    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image. This version includes a watershed line between objects.
    """

    boundary_path = os.path.join(multi_model_results_path, 'boundaries', '*predict.png')
    nuc_path = os.path.join(multi_model_results_path, 'edge_weighted_nuc', '*predict.png')
    com_path = os.path.join(multi_model_results_path, 'com', '*predict.png')
    com9_path = os.path.join(multi_model_results_path, 'com9', '*predict.png')
    graddisk1_path = os.path.join(multi_model_results_path, 'graddisk1', '*predict.png')
    graddisk2_path = os.path.join(multi_model_results_path, 'graddisk2', '*predict.png')
    graddisk3_path = os.path.join(multi_model_results_path, 'graddisk3', '*predict.png')

    boundary_ims = glob.glob(boundary_path)
    whole_nuc_ims = glob.glob(nuc_path)
    com_ims = glob.glob(com_path)
    com9_ims = glob.glob(com9_path)
    graddisk1_ims = glob.glob(graddisk1_path)
    graddisk2_ims = glob.glob(graddisk2_path)
    graddisk3_ims = glob.glob(graddisk3_path)

    boundary_ims.sort()
    whole_nuc_ims.sort()
    com_ims.sort()
    com9_ims.sort()
    graddisk1_ims.sort()
    graddisk2_ims.sort()
    graddisk3_ims.sort()

    print('\nData for probability basin watershed:')
    print(nuc_path)
    print(com9_path)
    print(graddisk1_path)
    print(graddisk2_path)
    print(graddisk3_path)
    # print(boundary_pred_ims)
    # print(whole_nuc_pred_ims)

    for image in range(len(boundary_ims)):
        # read in images:
        boundary_im = io.imread(boundary_ims[image]).astype('float32')
        nuc_im = io.imread(whole_nuc_ims[image]).astype('float32')
        com_im = io.imread(com_ims[image]).astype('float32')
        com9_im = io.imread(com9_ims[image]).astype('float32')
        graddisk1_im = io.imread(graddisk1_ims[image]).astype('float32')
        graddisk2_im = io.imread(graddisk2_ims[image]).astype('float32')
        graddisk3_im = io.imread(graddisk3_ims[image]).astype('float32')


        fname = os.path.split(os.path.splitext(boundary_ims[image])[0])[1]


        # create probability images:
        prob_boundaries = np.divide(boundary_im,255.).astype('float32')
        prob_nuc = np.divide(nuc_im,255.).astype('float32')
        prob_com = np.divide(com_im,255.).astype('float32')
        prob_com9 = np.divide(com9_im,255.).astype('float32')
        prob_gd1 = np.divide(graddisk1_im,255.).astype('float32')
        prob_gd2 = np.divide(graddisk2_im,255.).astype('float32')
        prob_gd3 = np.divide(graddisk3_im,255.).astype('float32')


        # add nucleus and internal gradient predictions:
        nuc_prob_sum = prob_nuc + prob_gd1 + prob_gd2 + prob_gd3
        # nuc_prob_sum = nuc_im + graddisk1_im + graddisk2_im + graddisk3_im

        # invert boundary image
        inverted_boundary_im = invert(prob_boundaries)

        prob_basins = np.multiply(nuc_prob_sum, inverted_boundary_im)


        # produce binary COMS image:
        binary_com = com_im > thresh_com
        binary_com = img_as_uint(binary_com)

        binary_com9 = com9_im > thresh_com
        binary_com9 = img_as_uint(binary_com9)

        # produce binary nucleus for masking watershed area:
        binary_nuc = nuc_im > thresh_nuc
        binary_nuc = img_as_uint(binary_nuc)

        # produce label markers for watershed from binary COMS image
        struct = [[0,1,0],[1,1,1], [0,1,0]]
        labelled_com = label(binary_com, structure=struct)[0]
        labelled_com9 = label(binary_com9, structure=struct)[0]

        # perform watershed:
        if line == True:

            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=True)

            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)
        
        else:
            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)
            
            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'no_line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)

            # save nuc sum:
            nuc_sum_out_dir = os.path.join(multi_model_results_path, 'mm_nuc_sum')
            if os.path.exists(nuc_sum_out_dir) != True:
                os.makedirs(nuc_sum_out_dir)
            
            savename = os.path.join(nuc_sum_out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            nuc_prob_sum = nuc_prob_sum.astype('uint16')
            nuc_prob_sum = img_as_uint(nuc_prob_sum)
            io.imsave(savename, nuc_prob_sum)

            # save prob basins:
            pbasin_out_dir = os.path.join(multi_model_results_path, 'mm_p_basins')
            if os.path.exists(pbasin_out_dir) != True:
                os.makedirs(pbasin_out_dir)
            
            savename = os.path.join(pbasin_out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            prob_basins = prob_basins.astype('uint16')
            prob_basins = img_as_uint(prob_basins)
            io.imsave(savename, prob_basins)

def multi_model_watershed_no_bounds(multi_model_results_path, watershed_results_path, thresh_nuc = 100, thresh_com = 150, min_obj_size=4, compactness = 10,
                            line = True):

    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image. This version includes a watershed line between objects.
    """

    boundary_path = os.path.join(multi_model_results_path, 'boundaries', '*predict.png')
    nuc_path = os.path.join(multi_model_results_path, 'edge_weighted_nuc', '*predict.png')
    com_path = os.path.join(multi_model_results_path, 'com', '*predict.png')
    com9_path = os.path.join(multi_model_results_path, 'com9', '*predict.png')
    graddisk1_path = os.path.join(multi_model_results_path, 'graddisk1', '*predict.png')
    graddisk2_path = os.path.join(multi_model_results_path, 'graddisk2', '*predict.png')
    graddisk3_path = os.path.join(multi_model_results_path, 'graddisk3', '*predict.png')

    boundary_ims = glob.glob(boundary_path)
    whole_nuc_ims = glob.glob(nuc_path)
    com_ims = glob.glob(com_path)
    com9_ims = glob.glob(com9_path)
    graddisk1_ims = glob.glob(graddisk1_path)
    graddisk2_ims = glob.glob(graddisk2_path)
    graddisk3_ims = glob.glob(graddisk3_path)

    boundary_ims.sort()
    whole_nuc_ims.sort()
    com_ims.sort()
    com9_ims.sort()
    graddisk1_ims.sort()
    graddisk2_ims.sort()
    graddisk3_ims.sort()

    print('\nData for probability basin watershed:')
    print(nuc_path)
    print(com9_path)
    print(graddisk1_path)
    print(graddisk2_path)
    print(graddisk3_path)
    # print(boundary_pred_ims)
    # print(whole_nuc_pred_ims)

    for image in range(len(boundary_ims)):
        # read in images:
        boundary_im = io.imread(boundary_ims[image])
        nuc_im = io.imread(whole_nuc_ims[image])
        com_im = io.imread(com_ims[image])
        com9_im = io.imread(com9_ims[image])
        graddisk1_im = io.imread(graddisk1_ims[image])
        graddisk2_im = io.imread(graddisk2_ims[image])
        graddisk3_im = io.imread(graddisk3_ims[image])


        fname = os.path.split(os.path.splitext(boundary_ims[image])[0])[1]


        # create probability images:
        prob_boundaries = np.divide(boundary_im,255.)
        prob_nuc = np.divide(nuc_im,255.)
        prob_com = np.divide(com_im,255.)
        prob_com9 = np.divide(com9_im,255.)
        prob_gd1 = np.divide(graddisk1_im,255.)
        prob_gd2 = np.divide(graddisk2_im,255.)
        prob_gd3 = np.divide(graddisk3_im,255.)


        # add nucleus and internal gradient predictions:
        nuc_prob_sum = prob_nuc + prob_gd1 + prob_gd2 + prob_gd3

        # invert boundary image
        inverted_boundary_im = invert(prob_boundaries)

        prob_basins = np.multiply(nuc_prob_sum, 1)


        # produce binary COMS image:
        binary_com = com_im > thresh_com
        binary_com = img_as_uint(binary_com)

        binary_com9 = com9_im > thresh_com
        binary_com9 = img_as_uint(binary_com9)

        # produce binary nucleus for masking watershed area:
        binary_nuc = nuc_im > thresh_nuc
        binary_nuc = img_as_uint(binary_nuc)

        # produce label markers for watershed from binary COMS image
        struct = [[0,1,0],[1,1,1], [0,1,0]]
        labelled_com = label(binary_com, structure=struct)[0]
        labelled_com9 = label(binary_com9, structure=struct)[0]

        # perform watershed:
        if line == True:

            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=True)

            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)
        
        else:
            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)
            
            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'no_line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)

def thresholded_mm_watershed(multi_model_results_path, watershed_results_path, thresh_nuc = 100, thresh_com = 150, min_obj_size=4, compactness = 10,
                            line = True):

    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image. This version includes a watershed line between objects.
    """

    boundary_path = os.path.join(multi_model_results_path, 'boundaries', '*predict.png')
    nuc_path = os.path.join(multi_model_results_path, 'edge_weighted_nuc', '*predict.png')
    com_path = os.path.join(multi_model_results_path, 'com', '*predict.png')
    com9_path = os.path.join(multi_model_results_path, 'com9', '*predict.png')
    graddisk1_path = os.path.join(multi_model_results_path, 'graddisk1', '*predict.png')
    graddisk2_path = os.path.join(multi_model_results_path, 'graddisk2', '*predict.png')
    graddisk3_path = os.path.join(multi_model_results_path, 'graddisk3', '*predict.png')

    boundary_ims = glob.glob(boundary_path)
    whole_nuc_ims = glob.glob(nuc_path)
    com_ims = glob.glob(com_path)
    com9_ims = glob.glob(com9_path)
    graddisk1_ims = glob.glob(graddisk1_path)
    graddisk2_ims = glob.glob(graddisk2_path)
    graddisk3_ims = glob.glob(graddisk3_path)

    boundary_ims.sort()
    whole_nuc_ims.sort()
    com_ims.sort()
    com9_ims.sort()
    graddisk1_ims.sort()
    graddisk2_ims.sort()
    graddisk3_ims.sort()

    print('\nData for probability basin watershed:')
    print(nuc_path)
    print(com9_path)
    print(graddisk1_path)
    print(graddisk2_path)
    print(graddisk3_path)
    # print(boundary_pred_ims)
    # print(whole_nuc_pred_ims)

    for image in range(len(boundary_ims)):
        # read in images:
        boundary_im = io.imread(boundary_ims[image])
        nuc_im = io.imread(whole_nuc_ims[image])
        com_im = io.imread(com_ims[image])
        com9_im = io.imread(com9_ims[image])
        graddisk1_im = io.imread(graddisk1_ims[image])
        graddisk2_im = io.imread(graddisk2_ims[image])
        graddisk3_im = io.imread(graddisk3_ims[image])


        fname = os.path.split(os.path.splitext(boundary_ims[image])[0])[1]


        # create probability images:
        prob_boundaries = np.divide(boundary_im,255.)
        prob_nuc = np.divide(nuc_im,255.)
        prob_com = np.divide(com_im,255.)
        prob_com9 = np.divide(com9_im,255.)
        prob_gd1 = np.divide(graddisk1_im,255.)
        prob_gd2 = np.divide(graddisk2_im,255.)
        prob_gd3 = np.divide(graddisk3_im,255.)


        # theshold to high probability prediction >0.5
        prob_nuc = prob_nuc > 0.5
        prob_gd1 = prob_gd1 > 0.5
        prob_gd2 = prob_gd2 > 0.5
        prob_gd3 = prob_gd3 > 0.5
        prob_boundaries = prob_boundaries > 0.5

        # add nucleus and internal gradient predictions:
        nuc_prob_sum = prob_nuc + prob_gd1 + prob_gd2 + prob_gd3


        # invert boundary image
        inverted_boundary_im = invert(prob_boundaries)

        prob_basins = np.multiply(nuc_prob_sum, inverted_boundary_im)


        # produce binary COMS image:
        binary_com = com_im > thresh_com
        binary_com = img_as_uint(binary_com)

        binary_com9 = com9_im > thresh_com
        binary_com9 = img_as_uint(binary_com9)

        # produce binary nucleus for masking watershed area:
        binary_nuc = nuc_im > thresh_nuc
        binary_nuc = img_as_uint(binary_nuc)

        # produce label markers for watershed from binary COMS image
        struct = [[0,1,0],[1,1,1], [0,1,0]]
        labelled_com = label(binary_com, structure=struct)[0]
        labelled_com9 = label(binary_com9, structure=struct)[0]

        # perform watershed:
        if line == True:

            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=True)

            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_thresh_mm_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)
        
        else:
            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)
            
            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'no_line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_thresh_mm_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)

def multi_model_watershed_v2(multi_model_results_path, watershed_results_path, thresh_nuc = 100, thresh_com = 150, min_obj_size=4, compactness = 10,
                            line = True):

    """
    Produces a watershed segmentation from probability basins that are made directly from U-net probability maps
    of nucleus and boundary regions of an image. Watershed is seeded from U-net predictions of the centres of mass
    of all the nuclei in the image. This version includes a watershed line between objects.
    """

    boundary_path = os.path.join(multi_model_results_path, 'boundaries', '*predict.png')
    nuc_path = os.path.join(multi_model_results_path, 'edge_weighted_nuc', '*predict.png')
    com_path = os.path.join(multi_model_results_path, 'com', '*predict.png')
    com9_path = os.path.join(multi_model_results_path, 'com9', '*predict.png')
    graddisk1_path = os.path.join(multi_model_results_path, 'graddisk1', '*predict.png')
    graddisk2_path = os.path.join(multi_model_results_path, 'graddisk2', '*predict.png')
    graddisk3_path = os.path.join(multi_model_results_path, 'graddisk3', '*predict.png')

    boundary_ims = glob.glob(boundary_path)
    whole_nuc_ims = glob.glob(nuc_path)
    com_ims = glob.glob(com_path)
    com9_ims = glob.glob(com9_path)
    graddisk1_ims = glob.glob(graddisk1_path)
    graddisk2_ims = glob.glob(graddisk2_path)
    graddisk3_ims = glob.glob(graddisk3_path)

    boundary_ims.sort()
    whole_nuc_ims.sort()
    com_ims.sort()
    com9_ims.sort()
    graddisk1_ims.sort()
    graddisk2_ims.sort()
    graddisk3_ims.sort()

    print('\nData for probability basin watershed:')
    print(nuc_path)
    print(com9_path)
    print(graddisk1_path)
    print(graddisk2_path)
    print(graddisk3_path)
    # print(boundary_pred_ims)
    # print(whole_nuc_pred_ims)

    for image in range(len(boundary_ims)):
        # read in images:
        boundary_im = io.imread(boundary_ims[image]).astype('float32')
        nuc_im = io.imread(whole_nuc_ims[image]).astype('float32')
        com_im = io.imread(com_ims[image]).astype('float32')
        com9_im = io.imread(com9_ims[image]).astype('float32')
        graddisk1_im = io.imread(graddisk1_ims[image]).astype('float32')
        graddisk2_im = io.imread(graddisk2_ims[image]).astype('float32')
        graddisk3_im = io.imread(graddisk3_ims[image]).astype('float32')


        fname = os.path.split(os.path.splitext(boundary_ims[image])[0])[1]


        # create probability images:
        prob_boundaries = np.divide(boundary_im,255.).astype('float32')
        prob_nuc = np.divide(nuc_im,255.).astype('float32')
        prob_com = np.divide(com_im,255.).astype('float32')
        prob_com9 = np.divide(com9_im,255.).astype('float32')
        prob_gd1 = np.divide(graddisk1_im,255.).astype('float32')
        prob_gd2 = np.divide(graddisk2_im,255.).astype('float32')
        prob_gd3 = np.divide(graddisk3_im,255.).astype('float32')

        invert_prob_com = -prob_com

        # add nucleus and internal gradient predictions:
        nuc_prob_sum = sum([prob_nuc, prob_gd1, prob_gd2, prob_gd3, invert_prob_com])
        # nuc_prob_sum = nuc_im + graddisk1_im + graddisk2_im + graddisk3_im

        # invert boundary image
        inverted_boundary_im = invert(prob_boundaries)

        prob_basins = np.multiply(nuc_prob_sum, inverted_boundary_im)
        prob_basins = gaussian(prob_basins, sigma=0.4)

        # produce binary COMS image:
        binary_com = com_im > thresh_com
        binary_com = img_as_uint(binary_com)

        binary_com9 = com9_im > thresh_com
        binary_com9 = img_as_uint(binary_com9)

        # produce binary nucleus for masking watershed area:
        binary_nuc = nuc_im > thresh_nuc
        binary_nuc = img_as_uint(binary_nuc)

        # produce label markers for watershed from binary COMS image
        struct = [[0,1,0],[1,1,1], [0,1,0]]
        labelled_com = label(binary_com, structure=struct)[0]
        labelled_com9 = label(binary_com9, structure=struct)[0]

        # perform watershed:
        if line == True:

            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=True)

            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_multi_model_smobj_rm.png'.format(fname))
            io.imsave(savename, small_obj_removed)
        
        else:
            watershed_im_wline = watershed(prob_basins, labelled_com, connectivity=1, offset=None, mask=binary_nuc, compactness=compactness, watershed_line=False)
            
            # remove small objects:
            small_obj_removed = remove_small_objects(watershed_im_wline, min_size=min_obj_size)

            # convert to 16bit integer images:
            small_obj_removed = img_as_uint(small_obj_removed)

            # save output:
            out_dir = os.path.join(watershed_results_path, 'no_line')
            if os.path.exists(out_dir) != True:
                os.makedirs(out_dir)

            savename = os.path.join(out_dir, '{}_mm_v2.png'.format(fname))
            io.imsave(savename, small_obj_removed)

            # save nuc sum:
            nuc_sum_out_dir = os.path.join(multi_model_results_path, 'mm_nuc_sum_v2')
            if os.path.exists(nuc_sum_out_dir) != True:
                os.makedirs(nuc_sum_out_dir)
            
            savename = os.path.join(nuc_sum_out_dir, '{}_mm_v2.png'.format(fname))
            savename = os.path.join(nuc_sum_out_dir, '{}_mm_v2.png'.format(fname))
            # nuc_prob_sum = nuc_prob_sum * 65535
            nuc_prob_sum = nuc_prob_sum.astype('uint16')
            nuc_prob_sum = img_as_uint(nuc_prob_sum)
            io.imsave(savename, nuc_prob_sum)

            # save prob basins:
            pbasin_out_dir = os.path.join(multi_model_results_path, 'mm_p_basins_v2')
            if os.path.exists(pbasin_out_dir) != True:
                os.makedirs(pbasin_out_dir)
            
            savename = os.path.join(pbasin_out_dir, '{}_mm_v2.png'.format(fname))
            # prob_basins = prob_basins * 65535
            prob_basins = prob_basins.astype('uint16')
            prob_basins = img_as_uint(prob_basins)
            io.imsave(savename, prob_basins)