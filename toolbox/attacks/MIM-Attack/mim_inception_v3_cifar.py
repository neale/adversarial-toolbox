from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import keras
from keras import backend
from keras.datasets import cifar10
from keras.utils import np_utils
import numpy as np

import tensorflow as tf
from tensorflow.python.platform import app
from tensorflow.python.platform import flags

from cleverhans.attacks import fgsm
from cleverhans.attacks import MomentumIterativeMethod as MIM
from cleverhans.utils_keras import cnn_model
from cleverhans.utils_tf import model_train, model_eval, batch_eval
from cleverhans.utils_tf import model_argmax

FLAGS = flags.FLAGS

flags.DEFINE_string('train_dir', '/tmp', 'Directory storing the saved model.')
flags.DEFINE_string(
    'filename', 'cifar10.ckpt', 'Filename to save model under.')
flags.DEFINE_integer('nb_epochs', 10, 'Number of epochs to train model')
flags.DEFINE_integer('batch_size', 128, 'Size of training batches')
flags.DEFINE_float('learning_rate', 0.001, 'Learning rate for training')

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '1'
def data_cifar10():
    """
    Preprocess CIFAR10 dataset
    :return:
    """

    # These values are specific to CIFAR10
    img_rows = 32
    img_cols = 32
    nb_classes = 10

    # the data, shuffled and split between train and test sets
    (X_train, y_train), (X_test, y_test) = cifar10.load_data()

    if keras.backend.image_dim_ordering() == 'th':
        X_train = X_train.reshape(X_train.shape[0], 3, img_rows, img_cols)
        X_test = X_test.reshape(X_test.shape[0], 3, img_rows, img_cols)
    else:
        X_train = X_train.reshape(X_train.shape[0], img_rows, img_cols, 3)
        X_test = X_test.reshape(X_test.shape[0], img_rows, img_cols, 3)
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')
    X_train /= 255
    X_test /= 255
    print 'X_train shape:', X_train.shape
    print X_train.shape[0], 'train samples'
    print X_test.shape[0], 'test samples'

    # convert class vectors to binary class matrices
    Y_train = np_utils.to_categorical(y_train, nb_classes)
    Y_test = np_utils.to_categorical(y_test, nb_classes)
    return X_train, Y_train, X_test, Y_test


def main(argv=None):
    """
    CIFAR10 CleverHans tutorial
    :return:
    """

    # Set TF random seed to improve reproducibility
    tf.set_random_seed(1234)

    if not hasattr(backend, "tf"):
        raise RuntimeError("This tutorial requires keras to be configured"
                           " to use the TensorFlow backend.")

    if keras.backend.image_dim_ordering() != 'tf':
        keras.backend.set_image_dim_ordering('tf')

    # Create TF session and set as Keras backend session
    sess = tf.Session()
    keras.backend.set_session(sess)

    # Get CIFAR10 test data
    X_train, Y_train, X_test, Y_test = data_cifar10()

    assert Y_train.shape[1] == 10.
    label_smooth = .1
    Y_train = Y_train.clip(label_smooth / 9., 1. - label_smooth)

    # Define input TF placeholder
    x = tf.placeholder(tf.float32, shape=(None, 32, 32, 3))
    y = tf.placeholder(tf.float32, shape=(None, 10))

    # Define TF model graph
    model = cnn_model(img_rows=32, img_cols=32, channels=3)
    predictions = model(x)
    print "Defined TensorFlow model graph."

    def evaluate():
        # Evaluate the accuracy of the CIFAR10 model on legitimate test
        # examples
        eval_params = {'batch_size': FLAGS.batch_size}
        accuracy = model_eval(sess, x, y, predictions, X_test, Y_test,
                              args=eval_params)
        assert X_test.shape[0] == 10000, X_test.shape
        print 'Test accuracy on legitimate test examples: ' + str(accuracy)

    # Train an CIFAR10 model
    train_params = {
        'nb_epochs': FLAGS.nb_epochs,
        'batch_size': FLAGS.batch_size,
        'learning_rate': FLAGS.learning_rate
    }
    model_train(sess, x, y, predictions, X_train, Y_train,
                evaluate=evaluate, args=train_params)

    # Craft adversarial examples using Fast Gradient Sign Method (FGSM)
    # adv_x = fgsm(x, predictions, eps=0.3)

    mim = MIM(model, back='tf', sess=sess)
    mim_params = {'eps_iter': 0.06,
                  'eps': 0.3,
                  'nb_iter': 10,
                  'ord': 2,
                  'decay_factor': 1.0}


    adv_x = mim.generate(x, **mim_params)


    eval_params = {'batch_size': FLAGS.batch_size}
    X_test_adv, = batch_eval(sess, [x], [adv_x], [X_test], args=eval_params)
    assert X_test_adv.shape[0] == 10000, X_test_adv.shape
    accuracy = model_eval(sess, x, y, predictions, X_test_adv, Y_test,
                          args=eval_params)
    print 'Test accuracy on adversarial examples: ' + str(accuracy)

    from scipy.misc import imsave
    path = '/home/neale/repos/adversarial-toolbox/images/adversarials/mim/cifar/symmetric/'
    """
    for i, (real, adv) in enumerate(zip(X_test, X_test_adv)):
        imsave(path+'adv/adv_{}.png'.format(i), adv)
    """
    preds = model_argmax(sess, x, predictions, X_test_adv)
    print Y_test.shape
    print preds.shape
    count = 0
    for i in range(len(preds)):
        if np.argmax(Y_test[i]) == preds[i]:
            # imsave(path+'real/im_{}.png'.format(i), X_test[i])
            # imsave(path+'adv/adv_{}.png'.format(i), X_test_adv[i])
            count += 1
    print "saved ", count

if __name__ == '__main__':
    app.run()
