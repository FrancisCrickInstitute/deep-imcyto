import numpy as np
import pandas as pd
import skimage.io as io
import matplotlib.pyplot as plt
import cupy as cp
from tqdm import *
from cupy import in1d
from scipy.ndimage.morphology import distance_transform_edt
from scipy.ndimage.measurements import center_of_mass
from scipy.ndimage.morphology import binary_dilation
from skimage.exposure import rescale_intensity


def cp_center_of_mass(instance_mask):

    row_indices, col_indices = cp.nonzero(instance_mask)
    row_mean = cp.mean(row_indices)
    col_mean = cp.mean(col_indices)
    # print(row_mean)
    # print(col_mean)
    row_mean = row_mean.item()
    col_mean = col_mean.item()
    center_of_mass = [row_mean, col_mean]
    # print(center_of_mass)
    # print(cp.asnumpy(center_of_mass))
    # indices = cp.nonzero(instance_mask)
    # center_of_mass = cp.mean(indices, (0,1))
    return center_of_mass

#########################
# MASK_TO_DILATED_SUM() #
#########################

'''THIS FUNCTION TAKES A 16-BIT MASK (LABEL IMAGE) PRODUCED BY CELLPROFILER, USES GPU PROCESSING
VIA CUPY TO GENERATE AN INSTANCE MASK FROM EACH LABEL, THEN DILATES EVERY INSTANCE BY 1 PIXEL AND ADDS
TOGETHER THE RESULT OF ALL DILATED INSTANCES. THIS PRODUCED AN IMAGE HIGHLIGHTING BOUNDARY PIXELS 
BETWEEN INDIVIDUAL INSTANCES WHICH CAN BE THRESHOLDED AND (OPTIONALLY) FURTHER POSTPROCESSED TO
PROVIDE INPUT BOUNDARY MASKS FOR U-NET TRAINING. DILATION IS PERFORMED THROUGH RUN LENGTH ENCODING WHICH
AFFORDS AN ~20X SPEEDUP COMPARED TO STANDARD DILATION.'''

def instance_distance_transform(seg_mask_16bit):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255
        predict_mask = cp.asnumpy(predict_mask)
        DT = distance_transform_edt(predict_mask)

        # # get shape and shape transpose for run length encoding:
        # mask_shape = predict_mask.shape
        # transpose_shape = (predict_mask.T).shape

        # # perform run length encoding along x axis:
        # rle_x = rle_encode(predict_mask)

        # # dilate x run lengths:
        # dilate_x_rle = dilate_rle(rle_x)

        # # convert dilated run lengths back to mask:
        # dilated_x_mask = rle_decode_2(dilate_x_rle, mask_shape)

        # # perform run length encoding along y axis via matrix transpose:
        # rle_y = rle_encode(predict_mask.T)

        # # dilate x run lengths:
        # dilate_y_rle = dilate_rle(rle_y)

        #  # convert dilated run lengths back to mask:
        # dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

        # # take tranpose of mask to convert y runs to original reference frame:
        # dilated_y_mask = dilated_y_mask.T

        # # combine x and y rle dilations via logical OR:
        # dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

        # convert to float to prevent saturation during summation:
        DT = DT.astype("float")

        # sum dilated masks recursively:
        if (i == 0):
            # zeros = 
            sum_mask = DT
        else:
            sum_mask = sum_mask + DT
    
    return sum_mask.astype("uint8")

def COMS_instance_distance_transform(seg_mask_16bit):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    COMS = []

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255


        predict_mask = cp.asnumpy(predict_mask)
        
        # PRODUCE DISTANCE TRANSFORM OF INSTANCE:        
        DT = distance_transform_edt(predict_mask)
        
        # convert to float to prevent saturation during summation:
        DT = DT.astype("float")

        # sum dilated masks recursively:
        if (i == 0):
            # zeros = 
            DT_sum_mask = DT
        else:
            DT_sum_mask = DT_sum_mask + DT

        # PRODUCE CENTRE OF MASS OF INSTANCE ROUNDED TO NEAREST INTEGER:
        COM = np.rint(center_of_mass(predict_mask))
        COMS.append(COM)

    COMS_image = np.zeros(seg_mask_16bit.shape, dtype='int')
    print(COMS)
    COMS_rows = []
    COMS =  np.asarray(COMS, dtype = 'int')
    COMS_rows = COMS[:, 0]
    print('COMS shape: ', COMS.shape)
    print('COMS rows shape: ', COMS_rows.shape)
    COMS_cols = COMS[:, 1]
    # print(COMS_rows)
    # COMS_image = np.put(COMS_image, COMS, 255)
    COMS_image[COMS_rows, COMS_cols] = 255
    # print(COMS_rows, COMS_cols)
    
    # produce centres of mass orunded to nearest integer:
   
    # print(COMS)
    # COMS_image = binary_dilation(COMS_image)

    # Convert to RLE:
    COMS_image = cp.asarray(COMS_image)
    # get shape and shape transpose for run length encoding:
    # get shape and shape transpose for run length encoding:
    COMS_image_shape = COMS_image.shape
    transpose_shape = (COMS_image.T).shape

    
    # perform run length encoding along x axis:
    rle_x = rle_encode(COMS_image)

    # dilate x run lengths:
    dilate_x_rle = dilate_rle(rle_x)

    # convert dilated run lengths back to mask:
    dilated_x_mask = rle_decode_2(dilate_x_rle, COMS_image_shape)

    # perform run length encoding along y axis via matrix transpose:
    rle_y = rle_encode(COMS_image.T)

    # dilate x run lengths:
    dilate_y_rle = dilate_rle(rle_y)

        # convert dilated run lengths back to mask:
    dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

    # take tranpose of mask to convert y runs to original reference frame:
    dilated_y_mask = dilated_y_mask.T

    # combine x and y rle dilations via logical OR:
    dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

    # convert to float to prevent saturation during summation:
    dilated_mask = cp.asnumpy(dilated_mask)   
    # COMS_image = rescale_intensity(COMS_image)                                                                      
    
    return dilated_mask.astype("uint8"), DT_sum_mask.astype("uint8")

def large_object_COMS_instance_distance_transform(seg_mask_16bit, size):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    COMS = []

    DT = np.zeros([seg_mask_16bit.shape[0], seg_mask_16bit.shape[1]])
    DT_sum_mask = np.zeros([seg_mask_16bit.shape[0], seg_mask_16bit.shape[1]])

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255


        predict_mask = cp.asnumpy(predict_mask)

        if len(np.nonzero(predict_mask)[0]) > size:
        
            # PRODUCE DISTANCE TRANSFORM OF INSTANCE:        
            DT = distance_transform_edt(predict_mask)
            
            # convert to float to prevent saturation during summation:
            DT = DT.astype("float")

            # sum dilated masks recursively:
            if (i == 0):
                # zeros = 
                DT_sum_mask = DT
            else:
                DT_sum_mask = DT_sum_mask + DT

            # PRODUCE CENTRE OF MASS OF INSTANCE ROUNDED TO NEAREST INTEGER:
            COM = np.rint(center_of_mass(predict_mask))
            COMS.append(COM)

    COMS_image = np.zeros(seg_mask_16bit.shape, dtype='int')
    
    if len(COMS) > 0:
        print(COMS)
        COMS_rows = []
        COMS =  np.asarray(COMS, dtype = 'int')
        COMS_rows = COMS[:, 0]
        print('COMS shape: ', COMS.shape)
        print('COMS rows shape: ', COMS_rows.shape)
        COMS_cols = COMS[:, 1]
        # print(COMS_rows)
        # COMS_image = np.put(COMS_image, COMS, 255)
        COMS_image[COMS_rows, COMS_cols] = 255
        # print(COMS_rows, COMS_cols)
        
        # produce centres of mass orunded to nearest integer:
    
        # print(COMS)
        # COMS_image = binary_dilation(COMS_image)

        # Convert to RLE:
        COMS_image = cp.asarray(COMS_image)
        # get shape and shape transpose for run length encoding:
        # get shape and shape transpose for run length encoding:
        COMS_image_shape = COMS_image.shape
        transpose_shape = (COMS_image.T).shape

        
        # perform run length encoding along x axis:
        rle_x = rle_encode(COMS_image)

        # dilate x run lengths:
        dilate_x_rle = dilate_rle(rle_x)

        # convert dilated run lengths back to mask:
        dilated_x_mask = rle_decode_2(dilate_x_rle, COMS_image_shape)

        # perform run length encoding along y axis via matrix transpose:
        rle_y = rle_encode(COMS_image.T)

        # dilate x run lengths:
        dilate_y_rle = dilate_rle(rle_y)

            # convert dilated run lengths back to mask:
        dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

        # take tranpose of mask to convert y runs to original reference frame:
        dilated_y_mask = dilated_y_mask.T

        # combine x and y rle dilations via logical OR:
        dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

        # convert to float to prevent saturation during summation:
        dilated_mask = cp.asnumpy(dilated_mask)   
    # COMS_image = rescale_intensity(COMS_image)       
    else:
        dilated_mask = np.zeros(seg_mask_16bit.shape, dtype='uint8')                                                               
    
    return dilated_mask.astype("uint8"), DT_sum_mask.astype("uint8")

def large_object_nuc_boundaries(seg_mask_16bit, size):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    large_nucs = []

    DT = np.zeros([seg_mask_16bit.shape[0], seg_mask_16bit.shape[1]])
    DT_sum_mask = np.zeros([seg_mask_16bit.shape[0], seg_mask_16bit.shape[1]])
    empty = np.zeros([seg_mask_16bit.shape[0], seg_mask_16bit.shape[1]])

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255


        predict_mask = cp.asnumpy(predict_mask)

        if len(np.nonzero(predict_mask)[0]) > size:
        
            large_nucs.append(predict_mask)

    # binary_nucs 
    if len(large_nucs) > 0:
        for i in range(len(large_nucs)):
            if i == 0:
                label_im = empty + large_nucs[i]    
            else:
                label_im = label_im + large_nucs[i]*(i+1)
    else:
        label_im = empty

    if len(large_nucs)>0:
        sum_binary = sum(large_nucs)
        sum_binary = np.asarray(sum_binary)
        print('sum_binary_shape: ', sum_binary.shape)
    else:
        sum_binary = empty

    return sum_binary.astype("uint8"), label_im.astype('uint16')

def make_COMS_mask(seg_mask_16bit):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    COMS = []

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255

        predict_mask = cp.asnumpy(predict_mask)

        # PRODUCE CENTRE OF MASS OF INSTANCE ROUNDED TO NEAREST INTEGER:
        COM = np.rint(center_of_mass(predict_mask))
        COMS.append(COM)

    COMS_image = cp.zeros(seg_mask_16bit.shape, dtype='int')
    # print(COMS)
    COMS_rows = []
    COMS =  cp.asarray(COMS, dtype = 'int')
    COMS_rows = COMS[:, 0]
    # print('COMS shape: ', COMS.shape)
    # print('COMS rows shape: ', COMS_rows.shape)
    COMS_cols = COMS[:, 1]
    # print(COMS_rows)
    # COMS_image = np.put(COMS_image, COMS, 255)
    COMS_image[COMS_rows, COMS_cols] = 255
    # print(COMS_rows, COMS_cols)
    
    # produce centres of mass orunded to nearest integer:
   
    # print(COMS)
    # COMS_image = binary_dilation(COMS_image)

    # Convert to RLE:
    # COMS_image = cp.asarray(COMS_image)
    # get shape and shape transpose for run length encoding:
    # get shape and shape transpose for run length encoding:
    COMS_image_shape = COMS_image.shape
    transpose_shape = (COMS_image.T).shape

    
    # perform run length encoding along x axis:
    rle_x = rle_encode(COMS_image)

    # dilate x run lengths:
    dilate_x_rle = dilate_rle(rle_x)

    # convert dilated run lengths back to mask:
    dilated_x_mask = rle_decode_2(dilate_x_rle, COMS_image_shape)

    # perform run length encoding along y axis via matrix transpose:
    rle_y = rle_encode(COMS_image.T)

    # dilate x run lengths:
    dilate_y_rle = dilate_rle(rle_y)

        # convert dilated run lengths back to mask:
    dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

    # take tranpose of mask to convert y runs to original reference frame:
    dilated_y_mask = dilated_y_mask.T

    # combine x and y rle dilations via logical OR:
    dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

    # convert to float to prevent saturation during summation:
    dilated_mask = cp.asnumpy(dilated_mask)   
    # COMS_image = rescale_intensity(COMS_image)                                                                      
    
    return dilated_mask.astype("uint8")

def cp_make_COMS_mask(seg_mask_16bit):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    COMS = []

    # generate set of instance masks as numpy array:
    for i in tqdm(range(len(predict_labels)), ascii=True):    

        # make 8bit mask to house instance mask:
        predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

        # turn unique predict labels in instance mask:
        predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255

        # predict_mask = cp.asnumpy(predict_mask)

        # PRODUCE CENTRE OF MASS OF INSTANCE ROUNDED TO NEAREST INTEGER:
        COM = cp_center_of_mass(predict_mask)
        COMS.append(COM)

    COMS_image = cp.zeros(seg_mask_16bit.shape, dtype='int')
    # print(COMS)
    COMS_rows = []
    COMS = cp.asarray(COMS)
    COMS = (cp.rint(COMS)).astype('int')
    # print(COMS)
    COMS_rows = COMS[:, 0]
    # print('COMS shape: ', COMS.shape)
    # print('COMS rows shape: ', COMS_rows.shape)
    COMS_cols = COMS[:, 1]
    # print(COMS_rows)
    # COMS_image = np.put(COMS_image, COMS, 255)
    COMS_image[COMS_rows, COMS_cols] = 255
    # print(COMS_rows, COMS_cols)
    
    # produce centres of mass orunded to nearest integer:
   
    # print(COMS)
    # COMS_image = binary_dilation(COMS_image)

    # Convert to RLE:
    # COMS_image = cp.asarray(COMS_image)
    # get shape and shape transpose for run length encoding:
    # get shape and shape transpose for run length encoding:
    COMS_image_shape = COMS_image.shape
    transpose_shape = (COMS_image.T).shape

    
    # perform run length encoding along x axis:
    rle_x = rle_encode(COMS_image)

    # dilate x run lengths:
    dilate_x_rle = dilate_rle(rle_x)

    # convert dilated run lengths back to mask:
    dilated_x_mask = rle_decode_2(dilate_x_rle, COMS_image_shape)

    # perform run length encoding along y axis via matrix transpose:
    rle_y = rle_encode(COMS_image.T)

    # dilate x run lengths:
    dilate_y_rle = dilate_rle(rle_y)

        # convert dilated run lengths back to mask:
    dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

    # take tranpose of mask to convert y runs to original reference frame:
    dilated_y_mask = dilated_y_mask.T

    # combine x and y rle dilations via logical OR:
    dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

    # convert to float to prevent saturation during summation:
    dilated_mask = cp.asnumpy(dilated_mask)   
    # COMS_image = rescale_intensity(COMS_image)                                                                      
    
    return dilated_mask.astype("uint8")

def mask_to_dilated_sum(seg_mask_16bit):

    seg_mask_16bit = cp.asarray(seg_mask_16bit, dtype='uint16')

    # get values of labels used for unique mask instances:
    predict_labels = cp.unique(seg_mask_16bit)

    # remove zero value corresponding to background:
    predict_labels = predict_labels[1:]

    # define new np array to hold predicted instance masks:
    pred_array_size = (seg_mask_16bit.shape[0], seg_mask_16bit.shape[1], len(predict_labels))
    print(pred_array_size)

    if len(predict_labels) > 0:
        # generate set of instance masks as numpy array:
        for i in tqdm(range(len(predict_labels)), ascii=True):    

            # make 8bit mask to house instance mask:
            predict_mask = cp.zeros(seg_mask_16bit.shape[:2], dtype = "uint8")

            # turn unique predict labels in instance mask:
            predict_mask[in1d(seg_mask_16bit, predict_labels[i]).reshape(predict_mask.shape)] = 255

            # get shape and shape transpose for run length encoding:
            mask_shape = predict_mask.shape
            transpose_shape = (predict_mask.T).shape

            # perform run length encoding along x axis:
            rle_x = rle_encode(predict_mask)

            # dilate x run lengths:
            dilate_x_rle = dilate_rle(rle_x)

            # convert dilated run lengths back to mask:
            dilated_x_mask = rle_decode_2(dilate_x_rle, mask_shape)

            # perform run length encoding along y axis via matrix transpose:
            rle_y = rle_encode(predict_mask.T)

            # dilate x run lengths:
            dilate_y_rle = dilate_rle(rle_y)

            # convert dilated run lengths back to mask:
            dilated_y_mask = rle_decode_2(dilate_y_rle, transpose_shape)

            # take tranpose of mask to convert y runs to original reference frame:
            dilated_y_mask = dilated_y_mask.T

            # combine x and y rle dilations via logical OR:
            dilated_mask = cp.logical_or(dilated_x_mask, dilated_y_mask)

            # convert to float to prevent saturation during summation:
            dilated_mask = dilated_mask.astype("float")

            # sum dilated masks recursively:
            if (i == 0):
                # zeros = 
                sum_mask = dilated_mask
            else:
                sum_mask = sum_mask + dilated_mask
    else:
        sum_mask = np.zeros(seg_mask_16bit.shape[:2])
        
    return sum_mask

def rle_encode(img):
    '''
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    '''
    pixels = img.flatten()
    zero = cp.asarray([0])
    pixels = cp.concatenate([zero, pixels, zero])
    # pixels = cp.concatenate([[0], pixels, [0]])
    runs = cp.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    # return ' '.join(str(x) for x in runs)
    return runs

def dilate_rle(rle_img):
    dilated_runs = cp.zeros(rle_img.shape, dtype = "int")
    # print('dil_runs_shape: ', dilated_runs.shape[0])
    for i in range(0, dilated_runs.shape[0], 2):
        # print(i)
        # print(rle_img[i], rle_img[i+1])
        # print(rle_img[i], rle_img[i] - 1)
        dilated_runs[i] = rle_img[i] - 1
        dilated_runs[i+1] = rle_img[i+1] + 2
    return dilated_runs

def erode_rle(rle_img):
    # remove run lengths <3 from cupy array:

    for i in range(len(rle_img.shape) - 1, -1, -2):
        if (rle_img[i] < 3):
            del(rle_img[i-1 : i])
            # rle_img[i-1 : i] = 0

    eroded_runs = cp.zeros(rle_img.shape, dtype = "int")
    # print('dil_runs_shape: ', dilated_runs.shape[0])
    for i in range(0, eroded_runs.shape[0], 2):
        # print(i)
        # print(rle_img[i], rle_img[i+1])
        # print(rle_img[i], rle_img[i] - 1)
        eroded_runs[i] = rle_img[i] + 1
        eroded_runs[i+1] = rle_img[i+1] - 2
    return ' '.join(str(x) for x in eroded_runs)

def rle_decode(mask_rle, shape):
    '''
    mask_rle: run-length as string formated (start length)
    shape: (height,width) of array to return 
    Returns numpy array, 1 - mask, 0 - background
    '''
    # s = mask_rle.split()
    starts = cp.zeros(mask_rle.shape[0], dtype = "int")
    lengths = cp.zeros(mask_rle.shape[0], dtype = "int")
    for i in range(0, mask_rle.shape[0], 2):

        starts[i], lengths[i] = mask_rle[i], mask_rle[i+1]
        # print(starts, lengths)
    starts -= 1
    ends = starts + lengths
    # img = np.zeros(shape[0] * shape[1], dtype=np.uint8)

    # for lo, hi in zip(starts, ends):
    #     img[lo:hi] = 1
    return starts, ends, lengths #img.reshape(shape)

def rle_decode_2(mask_rle, shape=(768, 768)):
    # print('rle_decode(mask_rle = ', mask_rle)
    '''
    mask_rle: run-length as string formated (start length)
    shape: (height,width) of array to return
    Returns numpy array, 1 - mask, 0 - background

    '''
    s = mask_rle.split()
    starts, lengths = [cp.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = cp.zeros(shape[0]*shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo:hi] = 255
    return img.reshape(shape)  # Needed to align to RLE direction

# img_path = '/camp/lab/swantonc/working/Alastair/training_datasets/u-net/full_res_touching_nuclei_masks/20191120_Run4_F/P1_TMA001_R_20190508_roi_1_nuclei_boundary_mask.png'

# img = cp.asarray(io.imread(img_path))
# # img.flatten()
# # img.squeeze()

# img_shape = img.shape
# transpose_shape = (img.T).shape

# rle_img_x = rle_encode(img)
# dilated_x = dilate_rle(rle_img_x)
# imaged_x = rle_decode_2(dilated_x, img_shape)

# rle_img_y = rle_encode(img.T)
# dilated_y = dilate_rle(rle_img_y)
# imaged_y = rle_decode_2(dilated_y, transpose_shape)
# imaged_y = imaged_y.T
# # print('starts shape: ', starts.shape)
# # starts.squeeze()
# # ends.squeeze()
# # lengths.squeeze()

# # for i in range(200):
# #     print(starts[i])
# imaged_x = cp.asnumpy(imaged_x)
# imaged_y = cp.asnumpy(imaged_y)
# io.imsave('rledilated_x4.png', imaged_x)
# io.imsave('rledilated_y4.png', imaged_y)
# print(rle_img)
# print(rle_img.shape)
# print(len(rle_img))

# for i in range(0, 100, 2):
#         print(rle_img[i], rle_img[i+1], dilated[i], dilated[i+1])

# print(dilated)