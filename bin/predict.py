#!/usr/bin/env python

import os, sys, glob
from math import ceil

import numpy as np
import pandas as pd
from tensorflow.keras.backend import clear_session
from skimage.morphology import diamond
from skimage.util import img_as_float32, img_as_uint
import skimage.io as io

from cupy_instance_closing_crop import instance_closing
from data_nucleus import *
from nested_unet import *
from unet_mask_postprocessing_module import (PBW_rm_small_obj,
                                             multi_model_watershed)


####################
# ~~~~ CONFIG ~~~~ #
####################

class configuration(object):

    def __init__(self, IMAGE_PATH, ROOT_OUT, PANEL, IMAGEREGEX, WEIGHTS_PATH):

        # GET CURRENT WORKING DIRECTORY:
        self.WORKING_DIR = os.getcwd()

        # IMC PANEL:    
        self.PANEL = PANEL

        # IMAGE SUBSET (I.E. PREDICT ON ONLY IMAGES MATCHING REGEX); if 'all' use wildcard:
        if IMAGEREGEX == 'all':
            self.PREDICTION_SUBSET = '*'
        else:
            self.PREDICTION_SUBSET = IMAGEREGEX

        # IMAGE_PATH TO TEST IMAGES:
        self.TEST_PATH = IMAGE_PATH

        # POSTPROCESSING WATERSHED THRESHOLDS:
        self.NUCLEUS_CONFIDENCE = 0.5
        self.COMS_CONFIDENCE = 0.5
        self.THRESH_NUC = self.NUCLEUS_CONFIDENCE * 255
        self.THRESH_COM = self.COMS_CONFIDENCE * 255
        self.MIN_OBJ_SIZE = 4
        self.WATERSHED_LINE = False
        self.COMPACTNESS = 0
        
        # OUTPUT DIRECTORIES:
        self.ROOT_OUT_DIR = f'{ROOT_OUT}/{PANEL}'
        self.BOUNDARY_RESULTS_DIR = '{}/raw/boundaries/'.format(self.ROOT_OUT_DIR)
        self.EDGE_WEIGHTED_NUC_RESULTS_DIR = '{}/raw/edge_weighted_nuc/'.format(self.ROOT_OUT_DIR)
        self.COM_RESULTS_DIR = '{}/raw/com/'.format(self.ROOT_OUT_DIR)
        self.PBW_WATERSHED_RESULTS_DIR = '{}/raw/pbw_wshed_nc_{}_cc_{}_mos_{}_c_{}/'.format(self.ROOT_OUT_DIR, self.NUCLEUS_CONFIDENCE, self.COMS_CONFIDENCE, self.MIN_OBJ_SIZE, self.COMPACTNESS)
        self.PP_OUT_DIR = '{}/postprocess_predictions'.format(self.ROOT_OUT_DIR)

        # PREFIX OF WEIGHTS FILE:
        self.WEIGHTS_DIR = WEIGHTS_PATH

        # DEFINE WEIGHTS PATHS FOR PREDICTIONS OF NUCLEI AND TOUCHING BOUNDARIES:
        self.BOUNDARY_WEIGHTS = os.path.join(self.WEIGHTS_DIR, 'boundaries.hdf5')
        self.WHOLE_NUCLEUS_WEIGHTS = os.path.join(self.WEIGHTS_DIR, 'nucleus_edge_weighted.hdf5')
        self.COM_WEIGHTS = os.path.join(self.WEIGHTS_DIR, 'com.hdf5')

        # PREDICT ONLY A SINGLE IMAGE AT A TIME AS WE EXPLICITELY TREAT IMAGES OF DIFFERENT SIZES DIFFERENTLY TO MINIMISE WARPING:
        self.N_IMAGES = 1

    def display(self):
            """Display Configuration values."""
            print("\n~~~~~CONFIG~~~~~")
            for a in dir(self):
                if not a.startswith("__") and not callable(getattr(self, a)):
                    print("{:30} {}".format(a, getattr(self, a)))
            print("\n")

def predict_feature_pad(weights, input_size, image, target_size, results_dir, image_shape):
    model = nested_unet(pretrained_weights = weights, input_size = input_size)
    testGene = test_generator_single_image_pad(image, target_size = target_size)
    results = model.predict_generator(testGene,1,verbose=1)
    save_single_image_result_unpad(results_dir, image, image_shape, results)

def predict_feature_resize(weights, input_size, image, target_size, results_dir, PAD_SIZE,image_shape):
    model = nested_unet(pretrained_weights = weights, input_size = input_size)
    testGene = test_generator_single_image_resize_high_AR(image, pad_size = PAD_SIZE, target_size = target_size)
    results = model.predict_generator(testGene,1,verbose=1)
    save_single_image_result_high_AR(results_dir, image, PAD_SIZE, image_shape, results)
    

##################
# ~~~~ MAIN ~~~~ #
##################

def main(CONFIG):

    # PRINT CONFIG VALUES:
    CONFIG.display()

    # MAKE RESULTS DIRECTORIES:
    all_results_dirs = [CONFIG.BOUNDARY_RESULTS_DIR, 
                        CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR,
                        CONFIG.COM_RESULTS_DIR,
                        CONFIG.PBW_WATERSHED_RESULTS_DIR,
                        CONFIG.PP_OUT_DIR]

    for results_dir in all_results_dirs:
        if (os.path.exists(results_dir) != True):
            os.makedirs(results_dir)


    ##################
    # ~~~~ MAIN ~~~~ #
    ##################

    IMAGE_LIST = glob.glob(os.path.join(CONFIG.TEST_PATH, '{}*.png'.format(CONFIG.PREDICTION_SUBSET)))
    IMAGE_LIST.sort()
    LARGE_IMAGE_LIST = []

    # GET ORIGINAL TEST IMAGE SIZES:
    test_image_shapes = get_image_shapes(CONFIG.TEST_PATH, len(IMAGE_LIST), suffix='{}*.png'.format(CONFIG.PREDICTION_SUBSET))
 
    # LOOP THROUGH IMAGES AND PREDICT:
    for i in range(len(IMAGE_LIST)):

        # get image shape prior to prediction:
        IMG = io.imread(IMAGE_LIST[i])
        IMG_SHAPE = IMG.shape
        MAX_IM_DIM = np.amax(IMG_SHAPE)
        PAD_SIZE = (ceil(MAX_IM_DIM/256)) * 256
        PAD_SHAPE = (PAD_SIZE,PAD_SIZE,1)
        GEN_TARGET_SIZE = PAD_SHAPE[:2]

        if PAD_SIZE <= 2560:
            """ 
            # process images small enough to fit into memory:
            """

            print('max image dimension: ', MAX_IM_DIM)
            print('PAD_SHAPE: ', PAD_SHAPE)
            print('GEN_TARGET_SIZE: ', GEN_TARGET_SIZE)
            
            # PREDICT TOUCHING BOUNDARIES :
            predict_feature_pad(CONFIG.BOUNDARY_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.BOUNDARY_RESULTS_DIR, IMG_SHAPE)

            # PREDICT EDGE-WEIGHTED NUCLEI:
            predict_feature_pad(CONFIG.WHOLE_NUCLEUS_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR, IMG_SHAPE)

            # PREDICT COM:
            predict_feature_pad(CONFIG.COM_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.COM_RESULTS_DIR, IMG_SHAPE)

            clear_session()

        else:
            """ 
            # deal with very large images by padding to square (max_dim, max_dim) then resizing to 2560x2560
            # to avoid extreme distortion of aspect ratio with simple resize:
            """
            
            # square size to pad to:
            MAX_SQUARE = (MAX_IM_DIM, MAX_IM_DIM)

            PAD_SHAPE = (2560,2560,1)
            GEN_TARGET_SIZE = PAD_SHAPE[:2]

            print('max image dimension: ', MAX_IM_DIM)
            print('Image size will exceed available memory. Padding to {}x{} for minimum distortion.'.format(MAX_IM_DIM, MAX_IM_DIM))
            print('Resizing to 2560x2560 pixels for prediction.')
            print('PAD_SHAPE: ', PAD_SHAPE)
            print('GEN_TARGET_SIZE: ', GEN_TARGET_SIZE)
            LARGE_IMAGE_LIST.append(IMAGE_LIST[i])

            # PREDICT TOUCHING BOUNDARIES :
            predict_feature_resize(CONFIG.BOUNDARY_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.BOUNDARY_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

            # PREDICT EDGE-WEIGHTED NUCLEI:
            predict_feature_resize(CONFIG.WHOLE_NUCLEUS_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

            # PREDICT COM:
            predict_feature_resize(CONFIG.COM_WEIGHTS, PAD_SHAPE, IMAGE_LIST[i], GEN_TARGET_SIZE, CONFIG.COM_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

            clear_session()

    # SAVE LARGE IMAGE LIST TO CSV:
    large_img_df = pd.DataFrame(LARGE_IMAGE_LIST)
    large_im_save_path = os.path.join(CONFIG.ROOT_OUT_DIR, 'LARGE_IMAGES.csv')
    large_img_df.to_csv(large_im_save_path)

    # DO "PROBABILITY BASIN" WATERSHED, REMOVING SMALL OBJECTS:
    PBW_rm_small_obj(CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR, CONFIG.BOUNDARY_RESULTS_DIR, CONFIG.COM_RESULTS_DIR, CONFIG.PBW_WATERSHED_RESULTS_DIR, CONFIG.THRESH_NUC, CONFIG.THRESH_COM, min_obj_size=CONFIG.MIN_OBJ_SIZE, compactness = CONFIG.COMPACTNESS)


    #############################################
    # PERFORM POSTPROCESSING of WATERSHED IMAGE #
    #############################################

    predict_list = glob.glob('{}/{}*.tiff'.format(CONFIG.PBW_WATERSHED_RESULTS_DIR, CONFIG.PREDICTION_SUBSET))
    predict_list.sort()

    for i in range(len(predict_list)):
        predict_im = io.imread(predict_list[i])
        diamond_selem = diamond(1)
        closed_im = instance_closing(predict_im, strel = diamond_selem)
        fname = os.path.split(predict_list[i])[1]
        fname = fname.split('SUM_DNA_')[0]
        fname = fname + 'nuclear_mask.tiff'
        save_path = os.path.join(CONFIG.PP_OUT_DIR, fname)

        # save as 16bit tiff if less than 2^16 gray values, 32 bit if not:
        if np.amax(closed_im) <= 65536:

            # convert to 16bit integer images:
            closed_im = img_as_uint(closed_im)

            # save output:
            io.imsave(save_path, closed_im)

        else:
            # convert to 32bit float images:
            closed_im = img_as_float32(closed_im)

            #save as tiff
            io.imsave(save_path, closed_im)

if __name__ == "__main__":
    
    """
    # ys.argv[3] = IMC panel
    # sys.argv[4] = REGEX to match images to predict on (if desired; use wildcard (*) to predict on all)
    # sys.argv[5] = path to weights directory
    """

    # create configuration based on input args:
    CONFIG = configuration(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    # run main with config:
    main(CONFIG)
