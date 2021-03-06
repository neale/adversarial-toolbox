import numpy as np
import scipy.misc
import time


def make_generator(path, n_files, batch_size):
    epoch_count = [1]

    def get_epoch():
        images = np.zeros((batch_size, 3, 128, 128), dtype='int32')
        files = range(n_files)
        random_state = np.random.RandomState(epoch_count[0])
        random_state.shuffle(files)
        epoch_count[0] += 1
        for n, i in enumerate(files):
            fn = "{}/{}.JPEG".format(path, str(i+1).zfill(len(str(n_files))))
            image = scipy.misc.imread(fn, mode='RGB')
            image = scipy.misc.imresize(image, (128, 128, 3))
            images[n % batch_size] = image.transpose(2, 0, 1)
            if n > 0 and n % batch_size == 0:
                yield (images,)
    return get_epoch


def load(batch_size, data_dir='/home/neale/repos/adversarial-toolbox/images/imagenet12'):
    return (
        make_generator(data_dir+'/train', 49999, batch_size),
        make_generator(data_dir+'/val', 49999, batch_size)
    )


if __name__ == '__main__':
    train_gen, valid_gen = load(64)
    t0 = time.time()
    for i, batch in enumerate(train_gen(), start=1):
        print "{}\t{}".format(str(time.time() - t0), batch[0][0, 0, 0, 0])
        if i == 1000:
            break
        t0 = time.time()
