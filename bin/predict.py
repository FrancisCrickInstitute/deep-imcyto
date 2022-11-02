#!/usr/bin/env python

import os, sys, glob
from math import ceil
import argparse

import numpy as np
import pandas as pd
from tensorflow.keras.backend import clear_session
from skimage.morphology import diamond
from skimage.util import img_as_float32, img_as_uint
import skimage.io as io

from anomaly_detection import process_anomalies, reprocess_unlikely_labels
from data_nucleus import *
from nested_unet import *
from unet_mask_postprocessing_module import (PBW_rm_small_obj, instance_closing)

from pickle import load

####################
# ~~~~ CONFIG ~~~~ #
####################

class configuration(object):

    def __init__(self, args):

        # GET CURRENT WORKING DIRECTORY:
        self.WORKING_DIR = os.getcwd()

        # IMAGE_PATH TO TEST IMAGES:
        self.TEST_IMAGE = args.image

        # POSTPROCESSING WATERSHED THRESHOLDS:
        self.NUCLEUS_CONFIDENCE = 0.5
        self.COMS_CONFIDENCE = 0.5
        self.COMS_CONFIDENCE_LOW = 0.125 # lower confidence for re-segmenting low likelihood regions
        self.THRESH_NUC = self.NUCLEUS_CONFIDENCE * 255
        self.THRESH_COM = self.COMS_CONFIDENCE * 255
        self.THRESH_COM_LOW = self.COMS_CONFIDENCE_LOW * 255
        self.MIN_OBJ_SIZE = 4
        self.WATERSHED_LINE = False
        self.COMPACTNESS = 0
        
        # OUTPUT DIRECTORIES:
        self.ROOT_OUT_DIR = args.outdir
        self.BOUNDARY_RESULTS_DIR = '{}/raw/boundaries/'.format(self.ROOT_OUT_DIR)
        self.EDGE_WEIGHTED_NUC_RESULTS_DIR = '{}/raw/edge_weighted_nuc/'.format(self.ROOT_OUT_DIR)
        self.COM_RESULTS_DIR = '{}/raw/com/'.format(self.ROOT_OUT_DIR)
        self.PBW_WATERSHED_RESULTS_DIR = '{}/raw/pbw_wshed_nc_{}_cc_{}_mos_{}_c_{}/'.format(self.ROOT_OUT_DIR, self.NUCLEUS_CONFIDENCE, self.COMS_CONFIDENCE, self.MIN_OBJ_SIZE, self.COMPACTNESS)
        self.MSE_RESULTS_DIR = '{}/raw/AE_error/'.format(self.ROOT_OUT_DIR)
        self.PP_OUT_DIR = '{}/postprocess_predictions'.format(self.ROOT_OUT_DIR)

        # PREFIX OF WEIGHTS FILE:
        self.WEIGHTS_DIR = args.weights

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

    LARGE_IMAGE_LIST = []
 
    # RUN PREDICTION ON INPUT IMAGE:
    if (CONFIG.TEST_IMAGE != None):

        # get image shape prior to prediction:
        IMG = io.imread(CONFIG.TEST_IMAGE)
        IMG_SHAPE = IMG.shape
        MAX_IM_DIM = np.amax(IMG_SHAPE)
        PAD_SIZE = (ceil(MAX_IM_DIM/256)) * 256
        PAD_SHAPE = (PAD_SIZE,PAD_SIZE,1)
        GEN_TARGET_SIZE = PAD_SHAPE[:2]

        if PAD_SIZE <= 2560:
            """ 
            # process imag.es small enough to fit into memory:
            """

            print('max image dimension: ', MAX_IM_DIM)
            print('PAD_SHAPE: ', PAD_SHAPE)
            print('GEN_TARGET_SIZE: ', GEN_TARGET_SIZE)
            
            # PREDICT TOUCHING BOUNDARIES :
            predict_feature_pad(CONFIG.BOUNDARY_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.BOUNDARY_RESULTS_DIR, IMG_SHAPE)

            # PREDICT EDGE-WEIGHTED NUCLEI:
            predict_feature_pad(CONFIG.WHOLE_NUCLEUS_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR, IMG_SHAPE)

            # PREDICT COM:
            predict_feature_pad(CONFIG.COM_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.COM_RESULTS_DIR, IMG_SHAPE)

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
            LARGE_IMAGE_LIST.append(CONFIG.TEST_IMAGE)

            # PREDICT TOUCHING BOUNDARIES :
            predict_feature_resize(CONFIG.BOUNDARY_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.BOUNDARY_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

            # PREDICT EDGE-WEIGHTED NUCLEI:
            predict_feature_resize(CONFIG.WHOLE_NUCLEUS_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

            # PREDICT COM:
            predict_feature_resize(CONFIG.COM_WEIGHTS, PAD_SHAPE, CONFIG.TEST_IMAGE, GEN_TARGET_SIZE, CONFIG.COM_RESULTS_DIR, MAX_SQUARE, IMG_SHAPE)

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
        '''
        [1] Perform instance level closing to refine nuclear shapes.
        [2] Remove anomalous (usually undersegmented) nuclei with deep autoencoder model trained on ground truth nuclear
            morphology stats.
        [3] Re-segment anomalous regions with looser centre of mass criterion in order to tackle undersegmentation.
        '''
        # Autoencoder params:
        scaler_path = os.path.join(CONFIG.WEIGHTS_DIR, 'nuclear_morph_scaler.pkl')
        morph_scaler = load(open(scaler_path, 'rb'))
        AE_weights = os.path.join(CONFIG.WEIGHTS_DIR, 'AE_weights.hdf5')

        ## image lists for postprocessing:
        watershed_list = glob.glob('{}/*.tiff'.format(CONFIG.PBW_WATERSHED_RESULTS_DIR))
        nuc_list = glob.glob('{}/*predict.png'.format(CONFIG.EDGE_WEIGHTED_NUC_RESULTS_DIR))
        bound_list = glob.glob('{}/*predict.png'.format(CONFIG.BOUNDARY_RESULTS_DIR))
        com_list = glob.glob('{}/*predict.png'.format(CONFIG.COM_RESULTS_DIR))
        
        # sort:
        watershed_list.sort()
        nuc_list.sort()
        bound_list.sort()
        com_list.sort()

        # 
        for i in range(len(watershed_list)):
            
            ## read necessary images:
            watershed_im = io.imread(watershed_list[i])
            nuc_im = io.imread(nuc_list[i])
            boundary_im = io.imread(bound_list[i])
            com_im = io.imread(com_list[i])

            ## construct filename:
            fname = os.path.split(watershed_list[i])[1]
            imagename = fname.split('_predict')[0]
            fname = imagename + '_nuclear_mask.tiff'

            # Perform instance closing:
            diamond_selem = diamond(1)
            closed_im = instance_closing(watershed_im, strel = diamond_selem)

            # Remove anomalies:
            mask_refined, error_img, _ = process_anomalies(closed_im, AE_weights, morph_scaler, save_error_image = True, outdir = CONFIG.MSE_RESULTS_DIR, imagename = imagename)

            # if any elements of the error array are greater than the error cutoff (==1), reprocess the regions that have this large error, else use this refinec mask as the final one:
            if np.any(error_img > 1):
                mask_final = reprocess_unlikely_labels(mask_refined, error_img, boundary_im, nuc_im, com_im, CONFIG.THRESH_COM_LOW, CONFIG.THRESH_NUC, AE_weights, morph_scaler, randomise = True)
            else:
                mask_final = mask_refined

            # Save final prostprocessed mask:
            save_path = os.path.join(CONFIG.PP_OUT_DIR, fname)

            # save as 16bit tiff if less than 2^16 gray values, 32 bit if not:
            if np.amax(mask_final) <= 65536:

                # convert to 16bit integer images:
                mask_final = img_as_uint(mask_final)

                # save output:
                io.imsave(save_path, mask_final)

            else:
                # convert to 32bit float images:
                mask_final = img_as_float32(mask_final)

                #save as tiff
                io.imsave(save_path, mask_final)

if __name__ == "__main__":
    
    """
    # ys.argv[3] = IMC panel
    # sys.argv[4] = REGEX to match images to predict on (if desired; use wildcard (*) to predict on all)
    # sys.argv[5] = path to weights directory
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('--image', type=str, default=None, help='Path to image to predict on')
    parser.add_argument('--weights', type=str, default=None, help='Path to weights directory')
    parser.add_argument('--outdir', type=str, default=None, help='Path to output directory')
    args = parser.parse_args()

    # create configuration based on input args:
    CONFIG = configuration(args)

    # run main with config:
    main(CONFIG)
