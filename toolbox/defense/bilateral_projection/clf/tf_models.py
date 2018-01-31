import numpy as np
import tensorflow as tf

from nets import resnet_v2
from nets import inception_v3
from nets import inception_v4
from nets import inception_resnet_v2

slim = tf.contrib.slim
ckpt_dir = 'nets/checkpoints/'
CKPT_LOADED = False


class InceptionV3Model(object):
    def __init__(self, sess=None):
        self._name = 'inception_v3'
        self.sess = sess
        self.num_classes = 1001
        self.image_size = 299
        self.num_channels = 3
        self.built = False
        self.ckpt_loaded = False
        self.input = tf.placeholder(tf.float32, (None, 299, 299, 3))

    def __call__(self, x_input):
        
        reuse = True if self.built else None
        with slim.arg_scope(inception_v3.inception_v3_arg_scope()):
            logits, end_points = inception_v3.inception_v3(
                    x_input, num_classes=self.num_classes, is_training=False,
                    reuse=reuse)
            self.built = True
        self.end_points = end_points
        self.logits = logits
        output = end_points['Predictions']
        probs = output.op.inputs[0]
        return probs

    def _build(self):
        reuse = True if self.built else None
        with slim.arg_scope(inception_v3.inception_v3_arg_scope()):
            logits, end_points = inception_v3.inception_v3(
                    self.input, num_classes=self.num_classes, is_training=False,
                    reuse=reuse)
            self.built = True
        self.end_points = end_points
        self.logits = logits
        if not self.ckpt_loaded:
            saver = tf.train.Saver(slim.get_model_variables())
            saver.restore(self.sess, ckpt_dir + 'inception_v3.ckpt')
            self.ckpt_loaded = True

    def _free(self):
        self.sess.close()

    def predict(self, x_input, sess=None):
        if self.sess is None:
            self.sess = sess
        logits = self.logits
        output = self.end_points['Predictions']
        prob_vals, logit_vals = self.sess.run([output, logits], 
                feed_dict={self.input: x_input})

        return prob_vals


class InceptionV4Model(object):
    def __init__(self, sess=None):
        self._name = 'inception_v4'
        self.sess = sess
        self.num_classes = 1001
        self.image_size = 299
        self.num_channels = 3
        self.built = False
        self.ckpt_loaded = False
        self.input = tf.placeholder(tf.float32, (None, 299, 299, 3))

    def __call__(self, x_input):

        self._build(x_input)
        output = self.end_points['Predictions']
        probs = output.op.inputs[0]
        return probs

    def _build(self, x_input=None):
        reuse = True if self.built else None
        if x_input is None:
            x_input = self.input
        with slim.arg_scope(inception_v4.inception_v4_arg_scope()):
            logits, end_points = inception_v4.inception_v4(
                    x_input, num_classes=self.num_classes, is_training=False,
                    reuse=reuse)
            self.built = True
        self.end_points = end_points
        self.logits = logits
        if not self.ckpt_loaded:
            saver = tf.train.Saver(slim.get_model_variables())
            saver.restore(self.sess, ckpt_dir + 'inception_v4.ckpt')
            self.ckpt_loaded = True

    def _free(self):
        self.sess.close()

    def predict(self, x_input, sess=None):
        if self.sess is None:
            self.sess = sess
        logits = self.logits
        output = self.end_points['Predictions']
        prob_vals, logit_vals = self.sess.run([output, logits], 
                feed_dict={self.input: x_input})

        return prob_vals


class InceptionResNetModel(object):
    def __init__(self, sess=None):
        self._name = 'inception_resnet_v2'
        self.sess = sess
        self.num_classes = 1001
        self.image_size = 299
        self.num_channels = 3
        self.built = False
        self.ckpt_loaded = False
        self.input = tf.placeholder(tf.float32, (None, 299, 299, 3))

    def __call__(self, x_input):
        
        self._build(x_input)
        output = self.end_points['Predictions']
        probs = output.op.inputs[0]
        return probs

    def _build(self, x_input=None):
        reuse = True if self.built else None
        if x_input is None:
            x_input = self.input
        with slim.arg_scope(inception_resnet_v2.inception_resnet_v2_arg_scope()):
            logits, end_points = inception_resnet_v2.inception_resnet_v2(
                    x_input, num_classes=self.num_classes, is_training=False,
                    reuse=reuse)
            self.built = True
        self.end_points = end_points
        self.logits = logits
        if not self.ckpt_loaded:
            saver = tf.train.Saver(slim.get_model_variables())
            saver.restore(self.sess, ckpt_dir + 'inception_resnet_v2.ckpt')
            self.ckpt_loaded = True

    def _free(self):
        self.sess.close()

    def predict(self, x_input, sess=None):
        if not self.sess:
            self.sess = sess
        logits = self.logits
        output = self.end_points['Predictions']
        prob_vals, logit_vals = self.sess.run([output, logits], 
                feed_dict={self.input: x_input})

        return prob_vals


class ResNetV2Model(object):
    def __init__(self, sess=None):
        self._name = 'resnet_v2'
        self.sess = sess
        self.num_classes = 1001
        self.image_size = 299
        self.num_channels = 3
        self.built = False
        self.ckpt_loaded = False
        self.input = tf.placeholder(tf.float32, (None, 299, 299, 3))

    def __call__(self, x_input):
        self._build(x_input)
        output = self.end_points['predictions']
        probs = output.op.inputs[0]
        return probs

    def _build(self, x_input=None):
        reuse = True if self.built else None
        if x_input is None:
            x_input = self.input
        with slim.arg_scope(resnet_v2.resnet_arg_scope()):
            logits, end_points = resnet_v2.resnet_v2_101(
                    x_input, num_classes=self.num_classes, is_training=False,
                    reuse=reuse)
            self.built = True
        self.end_points = end_points
        self.logits = logits
        if not self.ckpt_loaded:
            saver = tf.train.Saver(slim.get_model_variables())
            saver.restore(self.sess, ckpt_dir + 'resnet_v2_101.ckpt')
            self.ckpt_loaded = True

    def _free(self):
        self.sess.close()

    def predict(self, x_input, sess=None):
        if not self.sess:
            self.sess = sess
        logits = self.logits
        output = self.end_points['predictions']
        prob_vals, logit_vals = self.sess.run([output, logits], 
                feed_dict={self.input: x_input})

        return prob_vals
