#!/usr/bin/env python

import imctools.io.mcdparser as mcdparser
import imctools.io.txtparser as txtparser
import imctools.io.ometiffparser as omeparser
import imctools.io.mcdxmlparser as meta
# from imctools.io.mcd import McdParser as mcdparser
# from imctools.io.txt import TxtParser as txtparser
# from imctools.io.ometiff import OmeTiffParser as omeparser
# from imctools.io.mcd import McdXmlParser as meta
import imctools as imt
import os
import glob, sys
import pandas as pd
import argparse
import numpy as np

def roi_valid(parser, roi_number):
    try:
        parser.get_imc_acquisition(roi_number)
        print(f'Roi {roi_number} valid')
        return True
    except:
        print(f'roi-{roi_number} Not valid acquisition.')
        return False

mccs_metals =[]
nuclear_metals = ['191Ir', '193Ir']
spillover_metals = [
    '141Pr',
    '142Nd',
    '143Nd',
    '144Nd',
    '144Sm',
    '145Nd',
    '146Nd',
    '147Sm',
    '148Nd',
    '149Sm',
    '150Nd',
    '150Sm',
    '151Eu',
    '152Sm',
    '153Eu',
    '154Sm',
    '155Gd',
    '156Gd',
    '158Gd',
    '159Tb',
    '160Gd',
    '161Dy',
    '162Dy',
    '163Dy',
    '164Dy',
    '165Ho',
    '166Er',
    '167Er',
    '168Er',
    '169Tm',
    '170Er',
    '171Yb',
    '172Yb',
    '173Yb',
    '174Yb',
    '175Lu',
    '176Yb']

counterstain_metals = ['100Ru',
    '141Pr',
    '142Nd',
    '143Nd',
    '144Nd',
    '144Sm',
    '145Nd',
    '146Nd',
    '147Sm',
    '148Nd',
    '149Sm',
    '150Nd',
    '150Sm',
    '151Eu',
    '152Sm',
    '153Eu',
    '154Sm',
    '155Gd',
    '156Gd',
    '158Gd',
    '159Tb',
    '160Gd',
    '161Dy',
    '162Dy',
    '163Dy',
    '164Dy',
    '165Ho',
    '166Er',
    '167Er',
    '168Er',
    '169Tm',
    '170Er',
    '171Yb',
    '172Yb',
    '173Yb',
    '174Yb',
    '175Lu',
    '176Yb',
    '99Ru']

def get_metal_dict(imc_ac):
    housekeeping_isotopes = ['100Ru', 
                             '80ArAr',
                        '131Xe',
                        '134Xe',
                        '80ArArArAr80Di',
                        '131XeXe131Di',
                        '134XeXe134Di']
    hi_corr = ['100Ru', 
               '80ArAr',
                '131Xe',
                '134Xe',
                '80ArAr',
                '131Xe',
                '134Xe']

    hi_dict = dict(zip(housekeeping_isotopes,hi_corr))

    metadata_metals = dict()
    for label in imc_ac.channel_labels:
        # add corrected housekeeping isotopes to metadata (for those taken from txt images):
        if label in hi_dict.keys():
                metadata_metals[hi_dict[label]] = ''
        elif '_' in label:
            split = label.split('_')
            metal = split[0]
            marker = '_'.join(split[1:])
            metadata_metals[metal] = marker
    return metadata_metals
    
def create_metals_df(metadata_metals, mcdpath):
    metals_df = pd.DataFrame(data=zip(metadata_metals.keys(), metadata_metals.values()), columns=['isotope', 'marker_label'])
    metals_df['mcd_path'] = mcdpath
    metals_df['mcd_filename'] = os.path.split(mcdpath)[1]
    
    return metals_df

def assign_to_group(x,metals):
    if x in metals:
        return 1
    else:
        return 0

def main(args):

    if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

    imc_img_path = args.imc_img

    # get file extension:
    path, ext = os.path.splitext(imc_img_path)
    img_id = '_'.join(path.split('/')[-3:])
    spath = os.path.join(args.outdir, f'{img_id}.csv')
    print(img_id)

    if ext == '.mcd':

        
        # create parser:
        parser = mcdparser.McdParser(imc_img_path)
        if parser.n_acquisitions > 0:
            roi_ids = parser.acquisition_ids
            # roi_number = roi_ids[0]
            for roi_number in roi_ids:
                if roi_valid(parser, roi_number):
                    imc_ac = parser.get_imc_acquisition(roi_number)
                    # get metals and their labels directly from mcd file:
                    metadata_metals = get_metal_dict(imc_ac)
                    metals_df = create_metals_df(metadata_metals=metadata_metals, mcdpath=imc_img_path)
                    metals_df.to_csv(spath)
                    break
                else:
                    continue
        else:
            print('No valid acquisitions found.')
            sys.exit(1)

    else:
        if ext == ".txt":
            parser = txtparser.TxtParser(imc_img_path)
            imc_ac = parser.get_imc_acquisition()
            # get metals and their labels directly from txt file:
            metadata_metals = get_metal_dict(imc_ac)
            metals_df = create_metals_df(metadata_metals=metadata_metals, mcdpath=imc_img_path)
            metals_df.to_csv(spath)
        elif ext == ".tiff" or ext == ".tif":
            parser = omeparser.OmetiffParser(imc_img_path)
        else:
            print("{}: Invalid input file type - should be txt, tiff, or mcd!".format(ext))
            sys.exit(1)
        
    metals = metals_df['isotope'].values
    fullstack_true = np.ones_like(metals)
    metadata = pd.DataFrame(data=list(zip(metals, fullstack_true)), columns= ['metal', 'full_stack'])
    metadata['mccs_stack'] = metadata['metal'].apply(lambda x: assign_to_group(x, mccs_metals))
    metadata['nuclear'] = metadata['metal'].apply(lambda x: assign_to_group(x, nuclear_metals))
    metadata['spillover'] = metadata['metal'].apply(lambda x: assign_to_group(x, spillover_metals))
    metadata['counterstain'] = metadata['metal'].apply(lambda x: assign_to_group(x, counterstain_metals))
    metadata_spath = os.path.join(args.outdir, f'metadata.csv')
    metadata.to_csv(metadata_spath, index=False)
    
    print('Done.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--imc_img', type=str, help='path to mcd/tiff/txt file')
    parser.add_argument('--outdir', type=str, help='path to output directory')
    args = parser.parse_args()
    main(args)