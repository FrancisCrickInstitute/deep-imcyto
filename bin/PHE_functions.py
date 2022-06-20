
import numpy as np
import cv2 
from skimage.util import img_as_uint, img_as_int, img_as_ubyte
from skimage.exposure import rescale_intensity, histogram
from skimage.morphology import disk, closing, diamond
from skimage.filters import gaussian
from skimage.filters.rank import median
from luts import load_DNA_lut, load_counterstain_lut, load_IHC_lut


def make_pseudo(dna_img1, dna_img2, counterstain_img):
    '''
    Input = raw tiff images.
    '''

    # ensure float for rescaling:
    counterstain_img = counterstain_img / counterstain_img.max()
    dna_img1 = dna_img1 / dna_img1.max()
    dna_img2 = dna_img2 / dna_img2.max()

    # cnvert to 16bit uint:
    ruth = img_as_uint(counterstain_img)
    dna1 = img_as_uint(dna_img1) 
    dna2 = img_as_uint(dna_img2)
            
    ##### DNA: BLUE #####
    # adjust contrast
    dna_adj = dna_preprocess(dna1,dna2,sat=0.1)
    #denoise - cannot do once rgb
    selem = disk(1)
    dna_denoised = median(dna_adj, selem)
    # change colour
    dna_denoised = np.uint8(dna_denoised)
    dna_lut = load_DNA_lut() #pd.read_csv('./luts/PURPLE_LUT.csv', usecols=['Red', 'Green', 'Blue'])
    # dna_lut = dna_lut.values # get as np array
    dna_bgr = apply_custom_colormap(dna_denoised, dna_lut)
    dna_bgr = img_as_int(dna_bgr)

    #### RUTHENIUM /TISSUE: PINK###### condense so not repeating code
    # adjust contrast
    ruth_adj = ruth_preprocess(ruth,sat=0.1)
    ruth_adj = median(ruth_adj, selem)
    # change colour
    ruth_adj = np.uint8(ruth_adj)
    ruth_lut = load_counterstain_lut() # pd.read_csv('./luts/MAGENTA_LUT.csv', usecols=['Red', 'Green', 'Blue'])
    # ruth_lut = ruth_lut.values # get as np array
    ruth_bgr = apply_custom_colormap(ruth_adj, ruth_lut)
    ruth_bgr = img_as_int(ruth_bgr)

    ## COMBINE
    pseud = image_calculator(dna_bgr, ruth_bgr)

    ## adjust final contrast:
    # pseud = adjust_contrast(pseud)

    pseud = pseud.astype('uint16')
    pseud = img_as_int(pseud)

    return pseud

def make_pseudo_IHC(dna_img1, dna_img2, counterstain_img, IHC_stain_img):
    '''
    Input = raw tiff images.
    '''
    ruth = img_as_uint(counterstain_img)
    dna1 = img_as_uint(dna_img1) 
    dna2 = img_as_uint(dna_img2)
    IHC_stain = img_as_uint(IHC_stain_img)
            
    ##### DNA: BLUE #####
    # adjust contrast
    dna_adj = dna_preprocess(dna1,dna2,sat=0.1)
    #denoise - cannot do once rgb
    selem = disk(1)
    dna_denoised = median(dna_adj, selem)
    # change colour
    dna_denoised = np.uint8(dna_denoised)
    dna_lut = load_DNA_lut() #pd.read_csv('./luts/PURPLE_LUT.csv', usecols=['Red', 'Green', 'Blue'])
    # dna_lut = dna_lut.values # get as np array
    dna_bgr = apply_custom_colormap(dna_denoised, dna_lut)
    dna_bgr = img_as_int(dna_bgr)

    #### RUTHENIUM /TISSUE: PINK###### condense so not repeating code
    # adjust contrast
    ruth_adj = ruth_preprocess(ruth,sat=0.1)
    ruth_adj = median(ruth_adj, selem)
    # change colour
    ruth_adj = np.uint8(ruth_adj)
    ruth_lut = load_counterstain_lut() # pd.read_csv('./luts/MAGENTA_LUT.csv', usecols=['Red', 'Green', 'Blue'])
    # ruth_lut = ruth_lut.values # get as np array
    ruth_bgr = apply_custom_colormap(ruth_adj, ruth_lut)
    ruth_bgr = img_as_int(ruth_bgr)

    #### IHC CHANNEL ####

    # adjust contrast
    IHC_adj = closing(IHC_stain, selem = np.array([[0,1,0], [1,1,1], [0,1,0]]))
    # IHC_adj = ruth_preprocess(IHC_stain,sat=0.1)
    IHC_adj = gaussian(IHC_adj, sigma=0.1)
    IHC_adj = ruth_preprocess(IHC_adj,sat=0.1)
    # change colour
    IHC_adj = np.uint8(IHC_adj)
    IHC_lut = load_IHC_lut() # pd.read_csv('./luts/MAGENTA_LUT.csv', usecols=['Red', 'Green', 'Blue'])
    # ruth_lut = ruth_lut.values # get as np array
    IHC_bgr = apply_custom_colormap(IHC_adj, IHC_lut)
    IHC_bgr = img_as_int(IHC_bgr)


    ## COMBINE
    pseud = image_calculator_list([dna_bgr, ruth_bgr, IHC_bgr])

    ## adjust final contrast:
    # pseud = adjust_contrast(pseud)

    pseud = pseud.astype('uint16')
    pseud = img_as_int(pseud)

    return pseud

def adjust_contrast(img, saturation=0.1):

    if len(img.shape) == 2:
        # get min and max for contrast adjustment:
        hmin, hmax = get_min_and_max(img, saturation)
        # rescale intensity:
        rescaled = rescale_intensity(img, in_range=(hmin, hmax))
        return rescaled
        # img = np.expand_dims(img, axis=2) # add channel axis to single channel images if not existing

    else:
        nchannels = img.shape[2]
        if nchannels > 1:

            for i in range(nchannels):
                # get min and max for contrast adjustment:
                hmin, hmax = get_min_and_max(np.squeeze(img[:,:,i]), saturation)
                # rescale intensity:
                img[:,:,i] = rescale_intensity(img[:,:,i], in_range=(hmin, hmax))
            return img


    # else:
    #     # get min and max for contrast adjustment:
    #     hmin, hmax = get_min_and_max(img, saturation)
    #     # rescale intensity:
    #     rescaled = rescale_intensity(img, in_range=(hmin, hmax))
    #     return rescaled

def get_min_and_max(im, saturated):

    """Python port function of the java code used within Fiji/ImageJ for contrast adjustment based on a proportion of saturated pixels.
    """
    # get image histogram:
    hist = histogram(im, source_range='dtype')
    hsize = len(hist[0])
    # print('hsize: ', hsize)

    if (saturated>0.0):
        # threshold of saturated pixels that must not be exceed [input is given as percentage]:
        threshold = ((im.shape[0] * im.shape[1])*saturated)/200.0 # intuition says this should be 100, but java source is 200; kept as 200 for concordance
    else:
        threshold = 0
   
    # Perform loops to find adjusted min and max of histogram
    i = -1
    found = False
    count = 0
    maxindex = hsize#-1

    # loop forwards from low end of histogram to find bottom value of adjusted histogram:
    while (found == False and i<maxindex):
        i+=1
        count += hist[0][i]
        found = count>threshold

    hmin = i

    # re-initialise counters for reverse loop:
    found = False
    i = hsize
    count = 0

    # loop backwards from top end of histogram to find max value of adjusted histogram:
    while (found == False and i>0):
        i-=1
        count += hist[0][i]
        found = count>threshold

    hmax = i

    return hmin, hmax

def add_ims(im1, im2):
    summed = np.add(im1, im2)
    return summed

def dna_preprocess(dna1, dna2, sat=0.1):
    # add channels to increase signal:
    add = add_ims(dna1, dna2).astype('uint16')
    # remove singleton dimension:
    add = np.squeeze(add)
    # change bit depth:
    _16bit = img_as_uint(add)
    # adjust contrast:
    adjusted = adjust_contrast(_16bit, sat)
    return img_as_int(adjusted)

def ruth_preprocess(ruth, sat=0.1):

    # remove singleton dimension:
    ruth = np.squeeze(ruth)

    # change bit depth:
    _16bit = img_as_uint(ruth)
    # adjust contrast:
    adjusted = adjust_contrast(_16bit, sat)
    return img_as_int(adjusted)

def apply_custom_colormap(image_gray, fiji_lut):
    assert image_gray.dtype == np.uint8, 'must be np.uint8 image'
    # convert 3 channel RGB to 1 channel grayscale
    if image_gray.ndim == 3: image_gray = image_gray.squeeze(-1) #remove last dimension i.e. that specifying 3 channels

    # Obtain linear color range
    color_range = fiji_lut # No need to convert the fijilut from float [0,1] => [0,255]

    # color_range = np.squeeze(np.dstack([color_range[:,0], color_range[:,1], color_range[:,2]]), 0)  # RGB i.e all rows, column 0 (R) 1 (G) or 2 (B)
    
    # Apply colormap for each channel individually
    channels = [cv2.LUT(image_gray, color_range[:,i]) for i in range(3)]
    return np.dstack(channels).astype('uint8')


def image_calculator(img1, img2):
    # get mean of R,G,B channels:
    img1_r = img1[:,:,0]
    img2_r = img2[:,:,0]
    mean_r = np.mean([img1_r, img2_r], axis=0) #axis = 0???
    img1_g = img1[:,:,1]
    img2_g = img2[:,:,1]
    mean_g = np.mean([img1_g, img2_g],axis=0)
    img1_b = img1[:,:,2]
    img2_b = img2[:,:,2]
    mean_b = np.mean([img1_b, img2_b],axis=0)

    # recombine:
    mean_img = np.dstack((mean_r, mean_g, mean_b))

    return mean_img

def image_calculator_list(img_list):
    # get mean of R,G,B channels:
    r = []
    g = []
    b = []
    for img in img_list:
        img_r = img[:,:,0]
        img_g = img[:,:,1]
        img_b = img[:,:,2]
        r.append(img_r)
        g.append(img_g)
        b.append(img_b)

    mean_r = np.mean(r, axis=0) #axis = 0???
    mean_g = np.mean(g,axis=0)
    mean_b = np.mean(b,axis=0)

    # recombine:
    mean_img = np.dstack((mean_r, mean_g, mean_b))

    return mean_img