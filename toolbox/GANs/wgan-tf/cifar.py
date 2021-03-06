import os, sys
sys.path.append(os.getcwd())
import time
import numpy as np
import tensorflow as tf
import matplotlib

import tflib
from tflib.cifar10 import load
from tflib.save_images import save_images
from tflib.inception_score import get_inception_score
import tflib.plot as plot
import tflib.data_gen as data_gen
import generators
import discriminators
import keras.backend as K
from sklearn.utils import shuffle
import argparse

DATA_DIR = 'images/cifar-10-batches-py'

MODE = 'wgan-gp' # Valid options are dcgan, wgan, or wgan-gp
DIM = 128 # This overfits substantially; you're probably better off with 64
LAMBDA = 10 # Gradient penalty lambda hyperparameter
CRITIC_ITERS = 5 # How many critic iterations per generator iteration
GEN_ITERS = 1 # how many generator iterations per disc iteration (old DCGAN hack)
BATCH_SIZE = 32 # Batch size
BATCH_SIZE_ADV = 32 # Batch size
ITERS = 100000 # How many generator iterations to train for
OUTPUT_DIM = 3072 # Number of pixels in CIFAR10 (3*32*32)
TRAIN_DETECTOR = False
SAVE_ITERS = [1, 10000, 20000, 50000, 100000]
SAVE_NAME = "detector_wgan-gp"
tflib.print_model_settings(locals().copy())


def load_args():

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-s', '--save_dir', default='default_dir', type=str, help='save_dir')
    parser.add_argument('-z', '--z', default=128,type=int, help='noise sample width')
    parser.add_argument('-t', '--tf_trial_name', default=0,type=str, help='tensorboard trial')
    args = parser.parse_args()
    return args


args = load_args()

# detector = discriminators.InitDetector()
D = discriminators.DCifar
G = generators.GCifar

# Here we grab samples from G and push them through D1 and D2
real_data_int = tf.placeholder(tf.int32, shape=[BATCH_SIZE, OUTPUT_DIM])
real_data = 2*((tf.cast(real_data_int, tf.float32)/255.)-.5)
gen_data = G(BATCH_SIZE, DIM, OUTPUT_DIM, args.z)
y = tf.placeholder(tf.float32, shape=[BATCH_SIZE])

"""
We need to make a decision regarding two distributions,
We constrain our manifold to only include images from the union on sets P1 and P2
P1 being the set of natural images that could come from Cifar
P2 being the set of adversarial images that can fool our detector
"""
# disc_nat  = detector(real_data)
# disc_adv  = detector(gen_data)

disc_real = D(real_data, DIM)
disc_fake = D(gen_data, DIM)

g_params = tflib.params_with_name('G')
d1_params = tflib.params_with_name('D1')

# Standard WGAN loss on G and first discriminator
gen_cost = -tf.reduce_mean(disc_fake)
d1_cost  =  tf.reduce_mean(disc_fake) - tf.reduce_mean(disc_real)

""" Gradient penalty """
alpha = tf.random_uniform(
    shape=[BATCH_SIZE,1],
    minval=0.,
    maxval=1.
)
# calculate two sided loss term, mean( sqrt( sum ( gradx^2 ) ) )
differences = gen_data - real_data
interpolates = real_data + (alpha*differences)

gradients = tf.gradients(D(interpolates, DIM), [interpolates])[0]
tf.summary.histogram("interpolated gradients", gradients)
grads = tf.gradients(gen_cost, tf.trainable_variables())
grads = list(zip(grads, tf.trainable_variables()))

slopes = tf.sqrt(tf.reduce_sum(tf.square(gradients), reduction_indices=[1]))
gradient_penalty = tf.reduce_mean((slopes-1.)**2)
d1_cost += LAMBDA*gradient_penalty

gen_optim = tf.train.AdamOptimizer(learning_rate=1e-4, beta1=0.5, beta2=0.9).minimize(
                                      gen_cost, var_list=g_params)
d1_optim = tf.train.AdamOptimizer(learning_rate=1e-4, beta1=0.5, beta2=0.9).minimize(
                                       d1_cost, var_list=d1_params)
# we dont want to train the detector, just load weights
# d2_optim = tf.train.AdamOptimizer(learning_rate=1e-4, beta1=0.5, beta2=0.9).minimize(d2_cost)

d1_summ  = tf.summary.scalar("d1 cost", d1_cost)
# d2_summ  = tf.summary.scalar("d2 cost", d2_cost)
gen_summ = tf.summary.scalar("gen cost", gen_cost)

fixed_noise_z = tf.constant(np.random.normal(size=(args.z, args.z)).astype('float32'))
fixed_noise_samples_z = G(args.z, DIM, OUTPUT_DIM, args.z, noise=fixed_noise_z)


def generate_image(i, save, save_dir, random=False):
    if random == True:
        random_noise_z = tf.constant(np.random.normal(size=(args.z, args.z)).astype('float32'))
        random_noise_samples_z = G(args.z, DIM, OUTPUT_DIM, args.z, noise=random_noise_z)
        samples = session.run(random_noise_samples_z)
    else:
        samples = session.run(fixed_noise_samples_z)
    samples = ((samples+1.)*(255./2)).astype('int32')
    save_images(samples.reshape((args.z, 3, 32, 32)), 'samples_{}'.format(i), args.save_dir)

# For calculating inception score
samples_100 = G(100, DIM, OUTPUT_DIM, args.z)


def test_inception():
    all_samples = []
    for i in xrange(10):
        all_samples.append(session.run(samples_100))
    all_samples = np.concatenate(all_samples, axis=0)
    all_samples = ((all_samples+1.)*(255./2)).astype('int32')
    all_samples = all_samples.reshape((-1, 3, 32, 32)).transpose(0,2,3,1)
    return get_inception_score(list(all_samples))


def load_saver(load=False):
    saver = tf.train.Saver()
    if load == True:
    	saver = tf.train.import_meta_graph('./models/vanilla_wgan-gp_20000_steps.meta')
    	saver.restore(session, './models/vanilla_wgan-gp_50000_steps')
    return saver


def inf_train_gen1():
    while True:
        for images, targets in train_gen1():
            yield (images, targets)


def inf_train_gen2():
    while True:
        for images, targets in train_gen2():
            yield (images, targets)


def inf_train_gen_adv():
    while True:
        for images, targets in train_gen_adv():
            yield (images, targets)


# Adversarial dataset generators
x = np.load('images/lbfgs_adv.npy')
train_gen_adv, dev_gen_adv = data_gen.adv_load(x, BATCH_SIZE)
# Vanilla Cifar generators
train_gen1, dev_gen1 = load(BATCH_SIZE, data_dir=DATA_DIR)
train_gen2, dev_gen2 = load(BATCH_SIZE, data_dir=DATA_DIR)

# configure tf
config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.9
args = load_args()
summaries_dir = './board'
summary_op = tf.summary.merge_all()

# train loop
with tf.Session(config=config) as session:
    train_writer = tf.summary.FileWriter(summaries_dir + '/train/'+args.save_dir+'/'+args.tf_trial_name,
                                         session.graph)
    test_writer = tf.summary.FileWriter(summaries_dir + '/test')

    session.run(tf.global_variables_initializer())
    gen1 = inf_train_gen1()  # yields double in the beginning
    gen2 = inf_train_gen2()
    gen_adv = inf_train_gen_adv()
    saver = load_saver()

    # for iteration in range(500):
        # generate_random_image(iteration, args.save_dir)

    for iteration in xrange(ITERS):
        start_time = time.time()
        # Train generator
        if iteration > 0:
            for i in xrange(GEN_ITERS):
                _ = session.run(gen_optim)

        # Train critic
        for i in xrange(CRITIC_ITERS):
            if TRAIN_DETECTOR:
		data, labels = data_gen.mix_real_adv(gen_adv, gen2)
                d1_cost_, d2_cost_, _, _ = session.run([d1_cost, d2_cost, d1_optim, d2_optim],
				                       feed_dict={real_data_int: data, y : labels})
                plot.plot('train d2-bce cost', d2_cost_)
                plot.plot('time', time.time() - start_time)
            else:
                data, labels = gen1.next()
                d1_cost_, _ = session.run([d1_cost, d1_optim],
                              	          feed_dict={real_data_int: data, y: labels})

            plot.plot('train d1-wgan cost', d1_cost_)
            plot.plot('time', time.time() - start_time)



        # Calculate inception score every 1K iters
        if iteration % 1000 == 999:
            inception_score = test_inception()
            plot.plot('inception score', inception_score[0])

        # Calculate dev loss and generate samples every 100 iters
        if iteration % 100 == 99:
            dev_d1_costs, dev_d2_costs = [], []

            if TRAIN_DETECTOR:
                for data, labels in dev_gen_adv():
                    dev_d1_cost, summary = session.run([d1_cost, summary_op],
                                            feed_dict={real_data_int: data, y: labels})
            else:
                for data, labels in dev_gen2():
                    dev_d1_cost, summary = session.run([d1_cost, summary_op],
                                                        feed_dict={real_data_int: data,y: labels})
                    dev_d1_costs.append(dev_d1_cost)
            plot.plot('dev d1 cost', np.mean(dev_d1_costs))
            # plot.plot('dev d2 cost', np.mean(dev_d2_costs))
            generate_image(iteration, data, args.save_dir)
            generate_image(iteration, data, args.save_dir+'/random', random=True)

        if iteration in SAVE_ITERS:
            saver.save(session, 'models/'+SAVE_NAME+'_'+str(iteration)+'_steps')
        # Save logs every 100 iters
        if (iteration < 5) or (iteration % 100 == 99):
            plot.flush()
        plot.tick()
