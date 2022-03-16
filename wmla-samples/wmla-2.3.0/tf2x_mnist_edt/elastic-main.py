################################################################################
# Licensed Materials - Property of IBM
# 5725-Y38
# @ Copyright IBM Corp. 2020 All Rights Reserved
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
################################################################################

'''Trains a simple convnet on the MNIST dataset.

Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.

Adapted from: https://github.com/keras-team/keras/blob/master/examples/mnist_cnn.py
'''
# based on commit 71d9083
from __future__ import print_function
import os
import argparse
from pathlib import PurePath

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import tensorflow as tf
from fabric_model import FabricModel
from edtcallback import EDTLoggerCallback

parser = argparse.ArgumentParser(description='Keras MNIST Example')
parser.add_argument('--batch-size', type=int, default=128, metavar='N',
                    help='input batch size for training (default: 128)')
parser.add_argument('--epochs', type=int, default=12, metavar='N',
                    help='number of epochs to train (default: 12)')
parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                    help='learning rate (default: 0.01)')
args = parser.parse_args()
print(args)

data_dir = os.environ.get("DATA_DIR", "/tmp")
result_dir = os.environ.get("RESULT_DIR", "/tmp")
print("data_dir=%s, result_dir=%s" % (data_dir, result_dir))
os.makedirs(data_dir, exist_ok=True)

num_classes = 10
max_num_workers = 16

# input image dimensions
img_rows, img_cols = 28, 28

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data(path=str(PurePath(data_dir, "mnist.npz")))

x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = tf.keras.utils.to_categorical(y_train, num_classes)
y_test = tf.keras.utils.to_categorical(y_test, num_classes)


def get_dataset():
    print("In mnist_cnn get_dataset")
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
    return (train_datagen.flow(x_train, y_train, batch_size=args.batch_size),
            test_datagen.flow(x_test, y_test, batch_size=args.batch_size))


model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Conv2D(32, kernel_size=(3, 3),
                                 activation='relu',
                                 input_shape=input_shape))
model.add(tf.keras.layers.Conv2D(64, (3, 3), activation='relu'))
model.add(tf.keras.layers.MaxPooling2D(pool_size=(2, 2)))
model.add(tf.keras.layers.Dropout(0.25))
model.add(tf.keras.layers.Flatten())
model.add(tf.keras.layers.Dense(128, activation='relu'))
model.add(tf.keras.layers.Dropout(0.5))
model.add(tf.keras.layers.Dense(num_classes, activation='softmax'))

edt_m = FabricModel(model,
                    get_dataset,
                    loss_function="categorical_crossentropy",
                    optimizer=tf.keras.optimizers.Adam(lr=args.lr),
                    driver_logger=EDTLoggerCallback())
edt_m.train(args.epochs, args.batch_size, max_num_workers)