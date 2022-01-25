"""
Motion correction script modified by TAC, original author MHT

For use with single-channel volumetric timeseries (i.e GCaMP only)
"""
import os
import sys
import time
import nibabel as nib
import numpy as np
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

metadata = registration.get_bruker_metadata(metadata_path)
print('Loaded metadata from {}'.format(metadata_path))

# Load brain images
# ch1_brain_path = os.path.join(file_base_path, 'ch1_stitched.nii')
# ch2_brain_path = os.path.join(file_base_path, 'ch2_stitched.nii')

#for anat file test
ch1_brain_path = os.path.join(file_base_path, last_dir + '_channel_1_s0.nii')
ch2_brain_path = os.path.join(file_base_path, last_dir + '_channe2_1_s0.nii')

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
