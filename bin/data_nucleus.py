from __future__ import print_function
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np 
import os
import glob
import skimage.io as io
import skimage.transform as trans
import cv2


def adjustData(img,mask,flag_multi_class,num_class):
    if(flag_multi_class):
        img = img / 255
        mask = mask[:,:,:,0] if(len(mask.shape) == 4) else mask[:,:,0]
        new_mask = np.zeros(mask.shape + (num_class,))
        for i in range(num_class):
            #for one pixel in the image, find the class in mask and convert it into one-hot vector
            #index = np.where(mask == i)
            #index_mask = (index[0],index[1],index[2],np.zeros(len(index[0]),dtype = np.int64) + i) if (len(mask.shape) == 4) else (index[0],index[1],np.zeros(len(index[0]),dtype = np.int64) + i)
            #new_mask[index_mask] = 1
            new_mask[mask == i,i] = 1
        new_mask = np.reshape(new_mask,(new_mask.shape[0],new_mask.shape[1]*new_mask.shape[2],new_mask.shape[3])) if flag_multi_class else np.reshape(new_mask,(new_mask.shape[0]*new_mask.shape[1],new_mask.shape[2]))
        mask = new_mask
    elif(np.max(img) > 1):
        img = img / 255
        mask = mask /255
        mask[mask > 0.5] = 1
        mask[mask <= 0.5] = 0
    return (img,mask)



def trainGenerator(batch_size,train_path,image_folder,mask_folder,aug_dict,image_color_mode = "grayscale",
                    mask_color_mode = "grayscale",image_save_prefix  = "image",mask_save_prefix  = "mask",
                    flag_multi_class = False,num_class = 2,save_to_dir = None,target_size = (256,256),seed = 1):
    '''
    can generate image and mask at the same time
    use the same seed for image_datagen and mask_datagen to ensure the transformation for image and mask is the same
    if you want to visualize the results of generator, set save_to_dir = "your path"
    '''
    image_datagen = ImageDataGenerator(**aug_dict)
    mask_datagen = ImageDataGenerator(**aug_dict)
    image_generator = image_datagen.flow_from_directory(
        train_path,
        shuffle = False,
        classes = [image_folder],
        class_mode = None,
        color_mode = image_color_mode,
        target_size = target_size,
        batch_size = batch_size,
        save_to_dir = save_to_dir,
        save_prefix  = image_save_prefix,
        seed = seed)
    mask_generator = mask_datagen.flow_from_directory(
        train_path,
        shuffle = False,
        classes = [mask_folder],
        class_mode = None,
        color_mode = mask_color_mode,
        target_size = target_size,
        batch_size = batch_size,
        save_to_dir = save_to_dir,
        save_prefix  = mask_save_prefix,
        seed = seed)
    train_generator = zip(image_generator, mask_generator)
    for (img,mask) in train_generator:
        img,mask = adjustData(img,mask,flag_multi_class,num_class)
        yield (img,mask)



def testGenerator(test_path,num_image = 30,target_size = (256,256),flag_multi_class = False,as_gray = True):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')
    test_array = glob.glob(os.path.join(test_path, '*.png'))
    test_array.sort()
    # test_image_sizes = []
    for i in range(num_image):
        # img = io.imread(os.path.join(test_path,"%s*.png"%i),as_gray = as_gray)
        print('testarr[{}]: '.format(i), test_array[i])
        img = io.imread(test_array[i], as_gray = as_gray)
        img = img / 255
        img = trans.resize(img,target_size)
        img = np.reshape(img,img.shape+(1,)) if (not flag_multi_class) else img
        img = np.reshape(img,(1,)+img.shape)
        yield img

def test_generator_single_image_resize(test_image_path, target_size = (256,256), flag_multi_class = False,as_gray = True):

    img = io.imread(test_image_path, as_gray = as_gray)
    img = img / 255
    img = trans.resize(img,target_size)
    img = np.reshape(img,img.shape+(1,)) if (not flag_multi_class) else img
    img = np.reshape(img,(1,)+img.shape)
    yield img

def test_generator_single_image_resize_high_AR(test_image_path, pad_size, target_size = (256,256), flag_multi_class = False,as_gray = True):

    img = io.imread(test_image_path, as_gray = as_gray)
    img = img / 255
    
    # pad image to max square with zeros:
    img = pad_for_predict(img, pad_size)
    # resize padded image to network input target size:
    img = trans.resize(img,target_size)
    img = np.reshape(img,img.shape+(1,)) if (not flag_multi_class) else img
    img = np.reshape(img,(1,)+img.shape)
    yield img


def testGeneratorPad(test_path,num_image = 30,target_size = (256,256),flag_multi_class = False,as_gray = True):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')
    test_array = glob.glob(os.path.join(test_path, '*.png'))
    test_array.sort()
    # test_image_sizes = []
    for i in range(num_image):
        # img = io.imread(os.path.join(test_path,"%s*.png"%i),as_gray = as_gray)
        print('testarr[{}]: '.format(i), test_array[i])
        img = io.imread(test_array[i], as_gray = as_gray)
        img = img / 255
        img = pad_for_predict(img, target_size)
        img = np.reshape(img,img.shape+(1,)) if (not flag_multi_class) else img
        img = np.reshape(img,(1,)+img.shape)
        yield img

    
def test_generator_single_image_pad(test_image_path, target_size = (256,256), flag_multi_class = False, as_gray = True):

    img = io.imread(test_image_path, as_gray = as_gray)
    img = img / 255
    img = pad_for_predict(img, target_size)
    img = np.reshape(img,img.shape+(1,)) if (not flag_multi_class) else img
    img = np.reshape(img,(1,)+img.shape)
    yield img

def pad_for_predict(image, target_size):
    padding = [target_size[0] - image.shape[0], target_size[1] - image.shape[1]]
    # pad TMA images to right and bottom, as tiling begins from top left:
    pad_im = np.pad(image, ((0, padding[0]), (0, padding[1])), 'constant', constant_values=(0))
    return pad_im

def get_image_shapes(test_path, num_image, suffix='*.png'):
    test_array = glob.glob(os.path.join(test_path, suffix))
    test_array.sort()
    test_image_shapes = []
    for i in range(num_image):
        img = io.imread(test_array[i])
        test_image_shapes.append(img.shape)
    return test_image_shapes

def resize_predictions(predict_path, save_path, num_image, original_sizes_list):

    # GET LIST OF IMAGES IN PREDICTION DIRECTORY AND SORT TO ENSURE FILENAME ORDER:
    predict_array = glob.glob(os.path.join(predict_path, '*.tif'))
    predict_array.sort()

    # LOOP OVER ALL IMAGES IN PREDICTION DIRECTORY:
    for i in range(num_image):

        # USE CV2 FOR IO BECAUSE SKIMAGE DOES NOT ALLOW RESIZE WITH NEAREST NEIGHBOUR INTERPOLATION:
        img = cv2.imread(predict_array[i], cv2.IMREAD_ANYDEPTH)
        
        # GET TARGET DIMENSIONS OF IMAGE:
        height = original_sizes_list[i][0]
        width = original_sizes_list[i][1]
        dim = (width, height)

        # RESIZE TO TARGET DIMS:
        print('RESIZING U-NET PREDICTION TO: ', dim)
        img = cv2.resize(img, dim, interpolation=cv2.INTER_NEAREST)

        # ENSURE 16-BIT:
        img.astype("uint16")

        # SAVE OUTPUT:
        filename = os.path.split(predict_array[i])[1]
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_resized.tif"), img)

def resize_predictions_png(predict_path, save_path, num_image, original_sizes_list):

    # GET LIST OF IMAGES IN PREDICTION DIRECTORY AND SORT TO ENSURE FILENAME ORDER:
    predict_array = glob.glob(os.path.join(predict_path, '*.png'))
    predict_array.sort()

    # LOOP OVER ALL IMAGES IN PREDICTION DIRECTORY:
    for i in range(num_image):

        # USE CV2 FOR IO BECAUSE SKIMAGE DOES NOT ALLOW RESIZE WITH NEAREST NEIGHBOUR INTERPOLATION:
        img = cv2.imread(predict_array[i], cv2.IMREAD_ANYDEPTH)
        
        # GET TARGET DIMENSIONS OF IMAGE:
        height = original_sizes_list[i][0]
        width = original_sizes_list[i][1]
        dim = (width, height)

        # RESIZE TO TARGET DIMS:
        print('RESIZING U-NET PREDICTION TO: ', dim)
        img = cv2.resize(img, dim, interpolation=cv2.INTER_NEAREST)

        # ENSURE 16-BIT:
        img.astype("uint16")

        # SAVE OUTPUT:
        filename = os.path.split(predict_array[i])[1]
        filename = filename.split('SUM_DNA_')[0]
        filename = filename + 'nuclei_mask.png'
        io.imsave(os.path.join(save_path, filename), img)

def resize_predictions_tiff(predict_path, save_path, num_image, original_sizes_list):

    # GET LIST OF IMAGES IN PREDICTION DIRECTORY AND SORT TO ENSURE FILENAME ORDER:
    predict_array = glob.glob(os.path.join(predict_path, '*.png'))
    predict_array.sort()

    # LOOP OVER ALL IMAGES IN PREDICTION DIRECTORY:
    for i in range(num_image):

        # USE CV2 FOR IO BECAUSE SKIMAGE DOES NOT ALLOW RESIZE WITH NEAREST NEIGHBOUR INTERPOLATION:
        img = cv2.imread(predict_array[i], cv2.IMREAD_ANYDEPTH)
        
        # GET TARGET DIMENSIONS OF IMAGE:
        height = original_sizes_list[i][0]
        width = original_sizes_list[i][1]
        dim = (width, height)

        # RESIZE TO TARGET DIMS:
        print('RESIZING U-NET PREDICTION TO: ', dim)
        img = cv2.resize(img, dim, interpolation=cv2.INTER_NEAREST)

        # ENSURE 16-BIT:
        img.astype("uint16")

        # SAVE OUTPUT:
        filename = os.path.split(predict_array[i])[1]
        filename = filename.split('SUM_DNA_')[0]
        filename = filename + 'nuclei_mask.tiff'
        io.imsave(os.path.join(save_path, filename), img)

def geneTrainNpy(image_path,mask_path,flag_multi_class = False,num_class = 2,image_prefix = "image",mask_prefix = "mask",image_as_gray = True,mask_as_gray = True):
    image_name_arr = glob.glob(os.path.join(image_path,"%s*.png"%image_prefix))
    image_name_arr.sort()
    image_arr = []
    mask_arr = []
    for index,item in enumerate(image_name_arr):
        img = io.imread(item,as_gray = image_as_gray)
        img = np.reshape(img,img.shape + (1,)) if image_as_gray else img
        mask = io.imread(item.replace(image_path,mask_path).replace(image_prefix,mask_prefix),as_gray = mask_as_gray)
        mask = np.reshape(mask,mask.shape + (1,)) if mask_as_gray else mask
        img,mask = adjustData(img,mask,flag_multi_class,num_class)
        image_arr.append(img)
        mask_arr.append(mask)
    image_arr = np.array(image_arr)
    mask_arr = np.array(mask_arr)
    return image_arr,mask_arr


def labelVisualize(num_class,color_dict,img):
    img = img[:,:,0] if len(img.shape) == 3 else img
    img_out = np.zeros(img.shape + (3,))
    for i in range(num_class):
        img_out[img == i,:] = color_dict[i]
    return img_out / 255



def saveResult(save_path,test_path, npyfile,flag_multi_class = False,num_class = 2):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')
    test_array = glob.glob(os.path.join(test_path, '*.png'))
    test_array.sort()
    for i,item in enumerate(npyfile):
        filename = os.path.split(test_array[i])[1]
        img = labelVisualize(num_class,COLOR_DICT,item) if flag_multi_class else item[:,:,0]
        # img =img.astype('uint8')
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_predict.png"),img)
        # save original:
        original = io.imread(test_array[i])
        io.imsave(os.path.join(save_path, filename), original)

def save_single_image_result(save_path,test_path, npyfile,flag_multi_class = False,num_class = 2):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')

    for i,item in enumerate(npyfile):
        filename = os.path.split(test_path)[1]
        img = labelVisualize(num_class,COLOR_DICT,item) if flag_multi_class else item[:,:,0]
        # img =img.astype('uint8')
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_predict.png"),img)
        # save original:
        original = io.imread(test_path)
        io.imsave(os.path.join(save_path, filename), original)

def save_single_image_result_resize(save_path,test_path, target_size, npyfile, flag_multi_class = False,num_class = 2):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')

    for i,item in enumerate(npyfile):
        filename = os.path.split(test_path)[1]
        img = labelVisualize(num_class,COLOR_DICT,item) if flag_multi_class else item[:,:,0]
        img = trans.resize(img,target_size)
        # img =img.astype('uint8')
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_predict.png"),img)
        # save original:
        original = io.imread(test_path)
        io.imsave(os.path.join(save_path, filename), original)

def save_single_image_result_unpad(save_path,test_path, target_size, npyfile,flag_multi_class = False,num_class = 2):
    # test_array = glob.glob('/camp/lab/swantonc/working/Alastair/training_datasets/u-net/256x256_nucleus_train/non_excl_test_2/*.png')

    for i,item in enumerate(npyfile):
        filename = os.path.split(test_path)[1]
        img = labelVisualize(num_class,COLOR_DICT,item) if flag_multi_class else item[:,:,0]
        img = img[:target_size[0], :target_size[1]]
        # img =img.astype('uint8')
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_predict.png"),img)
        # save original:
        original = io.imread(test_path)
        io.imsave(os.path.join(save_path, filename), original)

def save_single_image_result_high_AR(save_path,test_path, pad_size, target_size, npyfile, flag_multi_class = False,num_class = 2):

    # invert padding and resizing before saving
    for i,item in enumerate(npyfile):
        filename = os.path.split(test_path)[1]
        img = labelVisualize(num_class,COLOR_DICT,item) if flag_multi_class else item[:,:,0]

        # resize to max_square
        img = trans.resize(img,pad_size)
        # unpad:
        img = img[:target_size[0], :target_size[1]]
        # img =img.astype('uint8')
        io.imsave(os.path.join(save_path, os.path.splitext(filename)[0] + "_predict.png"),img)
        # save original:
        original = io.imread(test_path)
        io.imsave(os.path.join(save_path, filename), original)