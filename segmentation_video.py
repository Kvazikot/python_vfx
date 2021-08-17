# -*- coding: utf-8 -*-
# DeepLab Demo
# This demo will demostrate the steps to run deeplab semantic segmentation model on sample input images.

import os
from io import BytesIO
import cv2
import tarfile
import tempfile
from six.moves import urllib
from scipy.interpolate import UnivariateSpline 
from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
from glow import *

import tensorflow as tf

class DeepLabModel(object):
  """Class to load deeplab model and run inference."""

  INPUT_TENSOR_NAME = 'ImageTensor:0'
  OUTPUT_TENSOR_NAME = 'SemanticPredictions:0'
  INPUT_SIZE = 513
  FROZEN_GRAPH_NAME = 'frozen_inference_graph'

  def __init__(self, tarball_path):
    """Creates and loads pretrained deeplab model."""
    self.graph = tf.Graph()

    graph_def = None
    # Extract frozen graph from tar archive.
    tar_file = tarfile.open(tarball_path)
    for tar_info in tar_file.getmembers():
      if self.FROZEN_GRAPH_NAME in os.path.basename(tar_info.name):
        file_handle = tar_file.extractfile(tar_info)
        graph_def = tf.GraphDef.FromString(file_handle.read())
        break

    tar_file.close()

    if graph_def is None:
      raise RuntimeError('Cannot find inference graph in tar archive.')

    with self.graph.as_default():
      tf.import_graph_def(graph_def, name='')

    self.sess = tf.Session(graph=self.graph)

  def run(self, image):
    """Runs inference on a single image.

    Args:
      image: A PIL.Image object, raw input image.

    Returns:
      resized_image: RGB image resized from original input image.
      seg_map: Segmentation map of `resized_image`.
    """
    width, height = image.size
    resize_ratio = 1.0 * self.INPUT_SIZE / max(width, height)
    target_size = (int(resize_ratio * width), int(resize_ratio * height))
    resized_image = image.convert('RGB').resize(target_size, Image.ANTIALIAS)
    batch_seg_map = self.sess.run(
        self.OUTPUT_TENSOR_NAME,
        feed_dict={self.INPUT_TENSOR_NAME: [np.asarray(resized_image)]})
    seg_map = batch_seg_map[0]
    return resized_image, seg_map


def create_pascal_label_colormap():
  """Creates a label colormap used in PASCAL VOC segmentation benchmark.

  Returns:
    A Colormap for visualizing segmentation results.
  """
  colormap = np.zeros((256, 3), dtype=int)
  ind = np.arange(256, dtype=int)

  for shift in reversed(range(8)):
    for channel in range(3):
      colormap[:, channel] |= ((ind >> channel) & 1) << shift
    ind >>= 3

  return colormap


def label_to_color_image(label):
  """Adds color defined by the dataset colormap to the label.

  Args:
    label: A 2D array with integer type, storing the segmentation label.

  Returns:
    result: A 2D array with floating type. The element of the array
      is the color indexed by the corresponding element in the input label
      to the PASCAL color map.

  Raises:
    ValueError: If label is not of rank 2 or its value is larger than color
      map maximum entry.
  """
  if label.ndim != 2:
    raise ValueError('Expect 2-D input label')

  colormap = create_pascal_label_colormap()

  if np.max(label) >= len(colormap):
    raise ValueError('label value too large.')

  return colormap[label]


def vis_segmentation(image, seg_map):
  """Visualizes input image, segmentation map and overlay view."""
  plt.figure(figsize=(15, 5))
  grid_spec = gridspec.GridSpec(1, 4, width_ratios=[6, 6, 6, 1])

  plt.subplot(grid_spec[0])
  plt.imshow(image)
  plt.axis('off')
  plt.title('input image')

  plt.subplot(grid_spec[1])
  seg_image = label_to_color_image(seg_map).astype(np.uint8)
  plt.imshow(seg_image)
  plt.axis('off')
  plt.title('segmentation map')

  plt.subplot(grid_spec[2])
  plt.imshow(image)
  plt.imshow(seg_image, alpha=0.7)
  plt.axis('off')
  plt.title('segmentation overlay')

  unique_labels = np.unique(seg_map)
  ax = plt.subplot(grid_spec[3])
  plt.imshow(
      FULL_COLOR_MAP[unique_labels].astype(np.uint8), interpolation='nearest')
  ax.yaxis.tick_right()
  plt.yticks(range(len(unique_labels)), LABEL_NAMES[unique_labels])
  plt.xticks([], [])
  ax.tick_params(width=0.0)
  plt.grid('off')
  plt.show()


LABEL_NAMES = np.asarray([
    'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
    'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike',
    'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tv'
])

FULL_LABEL_MAP = np.arange(len(LABEL_NAMES)).reshape(len(LABEL_NAMES), 1)
FULL_COLOR_MAP = label_to_color_image(FULL_LABEL_MAP)

# @title Select and download models {display-mode: "form"}

MODEL_NAME = 'mobilenetv2_coco_voctrainaug'  # @param ['mobilenetv2_coco_voctrainaug', 'mobilenetv2_coco_voctrainval', 'xception_coco_voctrainaug', 'xception_coco_voctrainval']

_DOWNLOAD_URL_PREFIX = 'http://download.tensorflow.org/models/'
_MODEL_URLS = {
    'mobilenetv2_coco_voctrainaug':
        'deeplabv3_mnv2_pascal_train_aug_2018_01_29.tar.gz',
    'mobilenetv2_coco_voctrainval':
        'deeplabv3_mnv2_pascal_trainval_2018_01_29.tar.gz',
    'xception_coco_voctrainaug':
        'deeplabv3_pascal_train_aug_2018_01_04.tar.gz',
    'xception_coco_voctrainval':
        'deeplabv3_pascal_trainval_2018_01_04.tar.gz',
}
_TARBALL_NAME = 'deeplab_model.tar.gz'

model_dir = tempfile.mkdtemp()
tf.gfile.MakeDirs(model_dir)

download_path = os.path.join(model_dir, _TARBALL_NAME)
print('downloading model, this might take a while...')
#urllib.request.urlretrieve(_DOWNLOAD_URL_PREFIX + _MODEL_URLS[MODEL_NAME],
#                           download_path)
print('download completed! loading DeepLab model...')

MODEL = DeepLabModel('deeplab_model.tar.gz')
print('model loaded successfully!')

# """## Run on sample images
#
# Select one of sample images (leave `IMAGE_URL` empty) or feed any internet image
# url for inference.
#
# Note that we are using single scale inference in the demo for fast computation,
# so the results may slightly differ from the visualizations in
# [README](https://github.com/tensorflow/models/blob/master/research/deeplab/README.md),
# which uses multi-scale and left-right flipped inputs.
# """

# @title Run on sample images {display-mode: "form"}

SAMPLE_IMAGE = 'image1.jpg'  # @param ['image1', 'image2', 'image3']
IMAGE_URL = 'https://raw.githubusercontent.com/tensorflow/models/master/research/deeplab/g3doc/img/image1.jpg'  #@param {type:"string"}

_SAMPLE_URL = ('https://github.com/tensorflow/models/blob/master/research/'
               'deeplab/g3doc/img/%s.jpg?raw=true')


def run_visualization(url):
  """Inferences DeepLab model and visualizes result."""
  try:
    # f = urllib.request.urlopen(url)
    # jpeg_str = f.read()
    # original_im = Image.open(BytesIO(jpeg_str))
    original_im = Image.open(SAMPLE_IMAGE)
  except IOError:
    print('Cannot retrieve image. Please check url: ' + url)
    return

  print('running deeplab on image %s...' % url)
  resized_im, seg_map = MODEL.run(original_im)

  vis_segmentation(resized_im, seg_map)


image_url = SAMPLE_IMAGE


#############################################################################

cap = cv2.VideoCapture('well_tempred_clavir.mp4')
#cap_bg = cv2.VideoCapture('/home/vova/Загрузки/bg.mp4')

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('well_tempred_clavir_with_bg.avi',fourcc, 30.0, (1280,960))
#out = cv2.VideoWriter('video1.avi', -1, 20.0, (640,480))

background = cv2.imread('spaceship.jpg')

  
# Creating kernel
kernel = np.ones((15, 15), np.uint8) 
# Using cv2.erode() method 
 
fr = 0
phaze = 0
freq_scaler = 10
enable_vfx = 1

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret==True:
        fr+=1
        #frame = cv2.flip(frame,0)
        im_pil = Image.fromarray(frame)
        resized_im, seg_map = MODEL.run(im_pil)
        numpy_image=np.float32(np.array(seg_map))        
        opencv_image=cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)    
        mask_or = cv2.resize(opencv_image, (frame.shape[1], frame.shape[0]))
        gray = cv2.cvtColor(mask_or, cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
        kernel = np.ones((15, 15), np.uint8) 
        mask = cv2.erode(mask, kernel)        

        background = cv2.resize(background, (frame.shape[1], frame.shape[0]))
        cv2.imwrite("background.png", background);
        cv2.imwrite("mask.png", mask);
        cv2.imwrite("frame.png", frame);
        
    

        phaze, final, enable_vfx = glow_vfx(frame, mask, background, phaze, fr, freq_scaler, enable_vfx)
        #final = cv2.resize(final, (1280,960))
        out.write(final)

        cv2.imshow("final", final)
      
        if cv2.waitKey(1) & 0xFF == ord('q'):
            out.release()
            break
    else:
        break

# Release everything if job is finished
cap.release()
out.release()
#cap_bg.release()
cv2.destroyAllWindows()
