import glob
import sys, os

import numpy as np
import pandas as pd
import skimage.io as io
import tensorflow as tf
from skimage.measure import regionprops, regionprops_table
from skimage.morphology import diamond
from skimage.segmentation import relabel_sequential
from skimage.util import map_array, img_as_uint, img_as_float32
from tensorflow import keras
from tensorflow.keras.callbacks import (EarlyStopping, ModelCheckpoint,
                                        TensorBoard)
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.metrics import categorical_accuracy
from sklearn.preprocessing import StandardScaler
from skimage.util import map_array, img_as_uint,img_as_float32
from unet_mask_postprocessing_module import PBW_image, instance_closing

def simple_autoencoder(input_features, pretrained_weights = None, learning_rate=1e-4):
    
    drop = 0.1

    model = Sequential()

    model.add(Dense(input_features, input_dim=input_features, activation='relu'))

    model.add(Dropout(drop))

    model.add(Dense(input_features//2, activation='relu'))

    model.add(Dropout(drop))

    model.add(Dense(input_features//4, activation='relu'))

    model.add(Dropout(drop))

    model.add(Dense(input_features//2, activation='relu'))

    model.add(Dropout(drop))

    model.add(Dense(input_features, activation='softmax'))

    # model.add(Dense(1, activation='sigmoid'))
    # model.compile(loss='binary_crossentropy', optimizer = Adam(lr = learning_rate), metrics=['accuracy'])
    model.compile(loss='MSLE', 
                optimizer = 'adam', 
                metrics=['MSE'])

    if(pretrained_weights):
        model.load_weights(pretrained_weights)

    model.summary()

    return model

def anomaly_detect(mask, model, model_features, region_properties, scaler, batch_size=256):
    '''
    Detect morphologically suspect nuclei from simple morph features.
    '''
    
    test_measure = regionprops_table(mask, properties=region_properties)
    test_measure_df = pd.DataFrame(test_measure)
    
    # predict on data
    model.predict(test_measure_df[model_features].values)
    X_scaled = scaler.transform(test_measure_df[model_features].values)
    results = model.predict(X_scaled, batch_size=batch_size)
    
    # get errors:
    reconstruction_errors = tf.keras.losses.msle(results, X_scaled)

    if results.shape[0] != 1:
        results = np.squeeze(results)
        
    # create dataframe with prediction errors:
    test_measure_df  = test_measure_df.reset_index()
    test_measure_df.loc[:, 'autoencoder_prediction_MSE'] = pd.Series(reconstruction_errors.numpy())
    return test_measure_df

def remove_anomalous_labels(AE_results, mask, threshold = 1):
    high_error_df = AE_results[AE_results['autoencoder_prediction_MSE'] > threshold]
    high_error_labels = high_error_df['label'].values
    logicalmask = np.isin(mask, high_error_labels.tolist())
    modmask = np.where(logicalmask==0, mask, 0)
    return modmask

def process_anomalies(mask, model_weights, scaler, save_error_image = False, outdir = None, imagename = None):
    '''
    Find morphologically suspect nuclear masks with autoencoder based anomaly detection.
    ------
    Params:
        mask: label image to be processed
        model: instantiated autoencoder model
        scaler: sklearn scaler object, trained on GT data (trained scaler loaded via pickle)
    '''
    # properties to measure per label
    test_properties = ['centroid', 'label', 'area',
             'eccentricity',
             'euler_number',
             'extent',
             'feret_diameter_max',
             'moments_hu',
             'perimeter',
             'perimeter_crofton',
             'solidity']
    # features for autoencoder:
    features = ['area',
             'eccentricity',
             'euler_number',
             'extent',
             'feret_diameter_max',
             'moments_hu-0',
             'moments_hu-1',
             'moments_hu-2',
             'moments_hu-3',
             'moments_hu-4',
             'moments_hu-5',
             'moments_hu-6',
             'perimeter',
             'perimeter_crofton',
             'solidity']

    n_features = len(features)
    model = simple_autoencoder(n_features, model_weights)
    results = anomaly_detect(mask, model, features, test_properties, scaler)
    mask_refined = remove_anomalous_labels(results, mask)

    error_img = map_array(mask, results['label'].values, results['autoencoder_prediction_MSE'].values)
    error_img = img_as_float32(error_img)
        
    if save_error_image == True:
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        
        spath = os.path.join(outdir, f'{imagename}_AE_error.tiff')
        io.imsave(spath, error_img)


    return mask_refined, error_img, results

def reprocess_unlikely_labels(mask, error_mask, boundary_im, nuc_im, com_im, com_thresh_lower, thresh_nuc, model_weights, scaler, randomise = False):
    
    # create waterhed image with lower com limit
    watershed_im = PBW_image(boundary_im=boundary_im, nuc_im=nuc_im, COMS_im=com_im, thresh_COMS=com_thresh_lower, thresh_nuc=thresh_nuc)

    # get watershed labels with lower coms limit, restricted to high error areas of original watershed:
    high_error_iter = np.where(error_mask>1, watershed_im, 0)
    
    # perform anomaly detection on this new iteration of watershed:
    processed, error_mask_2, _ = process_anomalies(high_error_iter, model_weights, scaler)
    
    # remove unlikely labels from the second iteration of watershed entirely:
    processed = np.where(error_mask_2>1, 0, processed)
    
    # do instance closing on resultant label image:
    diamond_selem = diamond(1)
    processed = instance_closing(processed, diamond_selem)
    
    # relabel so that labels are sequential integers
    relab, fw, inv = relabel_sequential(processed)

    # add the maximum label value from the good part of the original watershed mask to these labels:
    relab_add = np.where(relab>0, relab+np.amax(mask), 0)

    # join the second iteration of watershed into the original watershed:
    joined_mask = np.where(mask==0, relab_add, mask)
    
    if randomise == True:
        joined_mask = randomise_labels(joined_mask)
    
    return joined_mask

def randomise_labels(mask):
    new_labels = np.arange(1,len(np.unique(mask)))
    np.random.seed(42)
    np.random.shuffle(new_labels)
    old_labels = np.unique(mask[mask>0])

    reordered_label_img = map_array(mask, old_labels, new_labels)
    if np.amax(reordered_label_img) <= 65535:
        reordered_label_img = img_as_uint(reordered_label_img)
    else:
        reordered_label_img = reordered_label_img / np.amax(reordered_label_img)
        reordered_label_img = img_as_float32(reordered_label_img)
        
    return reordered_label_img
