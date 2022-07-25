import numpy as np
import cupy as cp
from tqdm import *
from cupy import in1d
from skimage.morphology import closing, remove_small_objects
from skimage.util import img_as_ubyte, img_as_uint, img_as_float32
from rle_dilation_module_2 import *

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
        for i in tqdm(range(len(predict_labels)), ascii=True):    

            # make 8bit mask to house instance mask:
            predict_mask = cp.zeros(seg_mask.shape[:2], dtype = "uint8")

            # turn unique predict labels in instance mask:
            predict_mask[in1d(seg_mask, predict_labels[i]).reshape(predict_mask.shape)] = 255

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
                label_im = empty + pad_closed
            else:
                # label_im = label_im + np.where(opened, i, 0)
                open_label = cp.where(pad_closed, i, 0)
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

