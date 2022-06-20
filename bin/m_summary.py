from nested_unet import *
from data_nucleus import *

WEIGHT_PREFIX = 'sequential_pipe_gt'
BOUNDARY_WEIGHTS = '/camp/lab/swantonc/working/Alastair/deep_learning_models/U-net/nested_unet/necrosis_free/multi_model/sequential_pipe_gt_frozen_layers/frozen_expand/weights/{}_boundaries.hdf5'.format(WEIGHT_PREFIX)
IM_SHAPE = (256,256,1)
model = nested_unet(pretrained_weights = BOUNDARY_WEIGHTS, input_size = IM_SHAPE)

model.summary()