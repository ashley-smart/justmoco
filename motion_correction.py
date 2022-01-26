"""
Motion correction script modified by TAC, original author MHT

For use with single-channel volumetric timeseries (i.e GCaMP only)
"""
import os
import sys
import time
import nibabel as nib
import numpy as np
import xml.etree.ElementTree as ET
from visanalysis.util import registration

t0 = time.time()

# first arg: path to image series base, without .suffix
#   e.g. /oak/stanford/groups/trc/data/Max/ImagingData/Bruker/20210611/TSeries-20210611-001
file_base_path = sys.argv[1]

print('Registering brain file from {}'.format(file_base_path))

# Load metadata from bruker .xml file
previous_dirs, last_dir = os.path.split(file_base_path)
# the os.path.split returns a tuple with everything in filepath in first set and then last component in second part, 
#but if last element is / then it returns nothing in second part of tuple
if not last_dir:
    previous_dirs, last_dir = os.path.split(previous_dirs)
metadata_path = os.path.join(file_base_path, last_dir + '.xml') 

def get_bruker_metadata(file_path):
    """
    Parse Bruker / PrairieView metadata from .xml file.

    file_path: .xml filepath
    returns
        metadata: dict
    """
    root = ET.parse(file_path).getroot()

    metadata = {}
    for child in list(root.find('PVStateShard')):
        if child.get('value') is None:
            for subchild in list(child):
                new_key = child.get('key') + '_' + subchild.get('index')
                new_value = subchild.get('value')
                metadata[new_key] = new_value

        else:
            new_key = child.get('key')
            new_value = child.get('value')
            metadata[new_key] = new_value

    metadata['version'] = root.get('version')
    metadata['date'] = root.get('date')
    metadata['notes'] = root.get('notes')
    
    # get frame times
    if root.find('Sequence').get('type') == 'TSeries Timed Element': # Plane time series
        frame_times = [float(fr.get('relativeTime')) for fr in root.find('Sequence').findall('Frame')]
        metadata['frame_times'] = frame_times
        metadata['sample_period'] = np.mean(np.diff(frame_times))

    elif root.find('Sequence').get('type') == 'TSeries ZSeries Element': # Volume time series
        middle_frame = int(len(root.find('Sequence').findall('Frame')) / 2)
        frame_times = [float(seq.findall('Frame')[middle_frame].get('relativeTime')) for seq in root.findall('Sequence') if len(seq) == len(root.findall('Sequence')[0])]
        #adding len(seq) above to check that it is a full sequence of the same length as the first sequence
        metadata['frame_times'] = frame_times
        metadata['sample_period'] = np.mean(np.diff(frame_times))

    # Get axis dims
    sequences = root.findall('Sequence')
    c_dim = len(sequences[0].findall('Frame')[0].findall('File')) # number of channels
    x_dim = metadata['pixelsPerLine']
    y_dim = metadata['linesPerFrame']

    if root.find('Sequence').get('type') == 'TSeries Timed Element': # Plane time series
        t_dim = len(sequences[0].findall('Frame'))
        z_dim = 1
    elif root.find('Sequence').get('type') == 'TSeries ZSeries Element': # Volume time series
        #t_dim = len(sequences)
        t_dim = len(frame_times) #len(sequences) will give wrong tdim if the last sequence is aborted and ignored
        z_dim = len(sequences[0].findall('Frame'))
    elif root.find('Sequence').get('type') == 'ZSeries': # Single Z stack (anatomical)
        t_dim = 1
        z_dim = len(sequences[0].findall('Frame'))
    else:
        print('!Unrecognized series type in PV metadata!')

    metadata['image_dims'] = [int(x_dim), int(y_dim), z_dim, t_dim, c_dim]

    

    return metadata





#metadata = registration.get_bruker_metadata(metadata_path)
metadata = get_bruker_metadata(metadata_path)     #to run my adjusted function                                                                                          
print('Loaded metadata from {}'.format(metadata_path))

# Load brain images
# ch1_brain_path = os.path.join(file_base_path, 'ch1_stitched.nii')
# ch2_brain_path = os.path.join(file_base_path, 'ch2_stitched.nii')

#for anat file test
ch1_brain_path = os.path.join(file_base_path, last_dir + '_channel_1_s0.nii')
ch2_brain_path = os.path.join(file_base_path, last_dir + '_channel_2_s0.nii')

ch1 = registration.get_ants_brain(ch1_brain_path, metadata, channel=0)
print('Loaded {}, shape={}'.format(ch1_brain_path, ch1.shape))
ch2 = registration.get_ants_brain(ch2_brain_path, metadata, channel=0)
print('Loaded {}, shape={}'.format(ch2_brain_path, ch2.shape))

# Register both channels to channel 1
merged = registration.registerToReferenceChannel_FilterTransforms(ch1, ch2, spatial_dims=len(ch1.shape) - 1)

# Register channel 1 to reference image drawn from first x frames
#merged = registration.registerOneChannelToSelf(ch1, spatial_dims=len(ch1.shape) - 1, reference_frames=20)


# Save registered, merged .nii
nifti1_limit = (2**16 / 2)
save_path = os.path.join(file_base_path, last_dir + '_reg.nii')
if np.any(np.array(merged.shape) >= nifti1_limit): # Need to save as nifti2
    nib.save(nib.Nifti2Image(merged, np.eye(4)), save_path)
else: # Nifti1 is OK
    nib.save(nib.Nifti1Image(merged, np.eye(4)), file_base_path + '_reg.nii')
print('Saved registered brain to {}. Total time = {:.1f}'.format(save_path, time.time()-t0))
