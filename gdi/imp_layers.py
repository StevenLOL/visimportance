'''
This file contains the data loaders used for the GDI importance model.
All the required image operations are performed (format conversion, mean substraction, correct channel+dimension formatting)
For the required data, please see: https://github.com/cvzoya/visimportance/tree/master/data

For GDI training, jpg images are loaded from the GDI/gd_train/ directory (using the file listing in GDI/train.txt)
Importance maps (as labels) are loaded as png images from GDI/gd_imp_train/

For GDI validation, jpg images are loaded from the GDI/gd_val/ directory (using the file listing in GDI/valid.txt)
Importance maps (as labels) are loaded as png images from GDI/gd_imp_val/

Note that maindir is passed during initialization of each data loader to provide the path to the these data directories.
This gets specified at the top of the train.prototxt and val.prototxt files (see: param_str)
'''

import caffe

import numpy as np
from PIL import Image

import random

###############################################################################
# GDI Training data loader #
class GDIDataLayerImp(caffe.Layer):
    """
    Load (input image, label image) pairs from dataset
    one-at-a-time while reshaping the net to preserve dimensions.

    Use this to feed data to a fully convolutional network.
    """

    def setup(self, bottom, top):
        """
        Setup data layer according to parameters:

        - train_dir: path to training data
        - split: train / val / test
        - mean: tuple of mean values to subtract
        - randomize: load in random order (default: True)
        - seed: seed for randomization (default: None / current time)

        example

        params = dict(train_dir="/path/to/data",
            mean=(104.00698793, 116.66876762, 122.67891434),
            split="val")
        """
        # config
        params = eval(self.param_str)
        self.maindir = params['train_dir'] # the main directory where to find the data files
        self.split = params['split']
        self.mean = np.array(params['mean'])
        self.random = params.get('randomize', True)
        self.seed = params.get('seed', None)
        self.binarize = params['binarize']

        # two tops: data and label
        if len(top) != 2:
            raise Exception("Need to define two tops: data and label.")
        # data layers have no bottoms
        if len(bottom) != 0:
            raise Exception("Do not define a bottom.")

        # load indices for images and labels
        split_f  = '{}/GDI/{}.txt'.format(self.maindir,
                self.split) # train.txt should have file listing
        self.indices = open(split_f, 'r').read().splitlines()
        self.idx = 0

        # make eval deterministic
        if 'train' not in self.split:
            self.random = False

        # randomization: seed and pick
        if self.random:
            random.seed(self.seed)
            self.idx = random.randint(0, len(self.indices)-1)


    def reshape(self, bottom, top):
        # load image + label image pair
        self.data = self.load_image(self.indices[self.idx])
        self.label = self.load_label(self.indices[self.idx])
        # reshape tops to fit (leading 1 is for batch dimension)
        top[0].reshape(1, *self.data.shape)
        top[1].reshape(1, *self.label.shape)


    def forward(self, bottom, top):
        # assign output
        top[0].data[...] = self.data
        top[1].data[...] = self.label

        # pick next input
        if self.random:
            self.idx = random.randint(0, len(self.indices)-1)
        else:
            self.idx += 1
            if self.idx == len(self.indices):
                self.idx = 0


    def backward(self, top, propagate_down, bottom):
        pass


    def load_image(self, idx):
        """
        Load input image and preprocess for Caffe:
        - cast to float
        - switch channels RGB -> BGR
        - subtract mean
        - transpose to channel x height x width order
        """
        im = Image.open('{}/GDI/gd_train/{}.jpg'.format(self.maindir, idx)) # targets_gdesign
        in_ = np.array(im, dtype=np.float32)
        in_ = in_[:,:,::-1]
        in_ -= self.mean
        in_ = in_.transpose((2,0,1))
        return in_


    def load_label(self, idx):
        """
        Load label image as 1 x height x width integer array of label indices.
        The leading singleton dimension is required by the loss.
        """
        im = Image.open('{}/GDI/gd_imp_train/{}.png'.format(self.maindir, idx)) # gdi-official
        label = np.array(im, dtype=np.uint8) # values range from 0 to 255
        if self.binarize:
            label = label>255.0*2/3
        else:
            label = label/255.0
        label = label[np.newaxis, ...] # this is the depth axis (what is color channels for images; since it doesn't exist for grayscale maps, initialize a dimension)
        return label

###############################################################################
# GDI Validation data loader #
class GDIValDataLayer(caffe.Layer):
    """
    Load (input image, label image) pairs 
    one-at-a-time while reshaping the net to preserve dimensions.

    Use this to feed data to a fully convolutional network.
    """

    def setup(self, bottom, top):
        """
        Setup data layer according to parameters:

        - val_dir: path to vaidation data dir
        - split: train / val /test
        - mean: tuple of mean values to subtract
        - randomize: load in random order (default: True)
        - seed: seed for randomization (default: None / current time)

        example

        params = dict(val_dir="/path/to/data",
            mean=(104.00698793, 116.66876762, 122.67891434),
            split="valid")
        """
        # config
        params = eval(self.param_str)
        self.maindir = params['val_dir'] # the main directory where to find the data files
        self.split = params['split']
        self.mean = np.array(params['mean'])
        self.random = params.get('randomize', True)
        self.seed = params.get('seed', None)
        self.binarize = params['binarize']

        # two tops: data and label
        if len(top) != 2:
            raise Exception("Need to define two tops: data and label.")
        # data layers have no bottoms
        if len(bottom) != 0:
            raise Exception("Do not define a bottom.")

        # load indices for images and labels
        split_f  = '{}/GDI/{}.txt'.format(self.maindir,
                self.split)
        self.indices = open(split_f, 'r').read().splitlines()
        self.idx = 0

        # make eval deterministic
        if 'train' not in self.split:
            self.random = False

        # randomization: seed and pick
        if self.random:
            random.seed(self.seed)
            self.idx = random.randint(0, len(self.indices)-1)


    def reshape(self, bottom, top):
        # load image + label image pair
        self.data = self.load_image(self.indices[self.idx])
        self.label = self.load_label(self.indices[self.idx])
        # reshape tops to fit (leading 1 is for batch dimension)
        top[0].reshape(1, *self.data.shape)
        top[1].reshape(1, *self.label.shape)


    def forward(self, bottom, top):
        # assign output
        top[0].data[...] = self.data
        top[1].data[...] = self.label

        # pick next input
        if self.random:
            self.idx = random.randint(0, len(self.indices)-1)
        else:
            self.idx += 1
            if self.idx == len(self.indices):
                self.idx = 0


    def backward(self, top, propagate_down, bottom):
        pass


    def load_image(self, idx):
        """
        Load input image and preprocess for Caffe:
        - cast to float
        - switch channels RGB -> BGR
        - subtract mean
        - transpose to channel x height x width order
        """
        im = Image.open('{}/GDI/gd_val/{}.jpg'.format(self.maindir, idx)) # targets_gdesign
        in_ = np.array(im, dtype=np.float32) 
        in_ = in_[:,:,::-1]
        in_ -= self.mean
        in_ = in_.transpose((2,0,1))
        return in_


    def load_label(self, idx):
        """
        Load label image as 1 x height x width integer array of label indices.
        The leading singleton dimension is required by the loss.
        """
    
        im = Image.open('{}/GDI/gd_imp_val/{}.png'.format(self.maindir, idx)) # gdi-official
        label = np.array(im, dtype=np.uint8) # values range from 0 to 255
        if self.binarize:
            label = label>255.0*2/3 # binarize the map
        else:
            label = label/255.0
        label = label[np.newaxis, ...] # this is the depth axis (what is color channels for images; since it doesn't exist for grayscale maps, initialize a dimension)
        return label
        
