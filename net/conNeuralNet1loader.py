import tensorflow as tf
import math
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from dataset import loader

"""from tensorflow.examples.tutorials.mnist import input_data
data = input_data.read_data_sets("MNIST_data/", one_hot=True)"""

# picture
pic_w = 96
pic_h = 96
num_classes = 15 * 2
# other
p_keep = tf.placeholder(tf.float32)
is_test = tf.placeholder(tf.bool)
iteration = tf.placeholder(tf.int32)
lr = tf.placeholder(tf.float32)

# first con layer
n_filters1 = 24
# stride1 = [1,1,1,1]
filter1_w = 5
filter1_h = 5
# second con layer
n_filters2 = 36
stride2 = [1, 2, 2, 1]
filter2_w = 5
filter2_h = 5
# third con layer
n_filters3 = 48
# stride3 = [1,2,2,1]
filter3_w = 5
filter3_h = 5
# cetvrti
n_filters4 = 64
stride4 = [1, 2, 2, 1]
filter4_w = 3
filter4_h = 3
# pet
n_filters5 = 64
# first fc layer
n_neurons1 = 500
# second fc layer
n_neurons2 = 90
# third fc layer
n_neurons3 = num_classes

k = 1 * 1 * n_filters5

Wc1 = tf.Variable(tf.truncated_normal(shape=[filter1_w, filter1_h, 1, n_filters1], stddev=0.1), name="wcon1")
Bc1 = tf.Variable(tf.zeros(shape=[n_filters1]), name="bcon1")
Wc2 = tf.Variable(tf.truncated_normal(shape=[filter2_w, filter2_h, n_filters1, n_filters2], stddev=0.1), name="wcon2")
Bc2 = tf.Variable(tf.zeros(shape=[n_filters2]), name="bcon2")
Wc3 = tf.Variable(tf.truncated_normal(shape=[filter3_w, filter3_h, n_filters2, n_filters3], stddev=0.1), name="wcon3")
Bc3 = tf.Variable(tf.zeros(shape=[n_filters3]), name="bcon3")
Wc4 = tf.Variable(tf.truncated_normal(shape=[filter4_w, filter4_h, n_filters3, n_filters4], stddev=0.1), name="wcon4")
Bc4 = tf.Variable(tf.zeros(shape=[n_filters4]), name="bcon4")
Wc5 = tf.Variable(tf.truncated_normal(shape=[2, 2, n_filters4, n_filters5], stddev=0.1), name="wcon5")
Bc5 = tf.Variable(tf.zeros(shape=[n_filters5]), name="bcon5")
Wf1 = tf.Variable(tf.truncated_normal(shape=[k, n_neurons1], stddev=0.1), name="wf1")
Bf1 = tf.Variable(tf.zeros(shape=[n_neurons1]), name="bf1")
Wf2 = tf.Variable(tf.truncated_normal(shape=[n_neurons1, n_neurons2], stddev=0.1), name="wf2")
Bf2 = tf.Variable(tf.zeros(shape=[n_neurons2]), name="bf2")
Wf3 = tf.Variable(tf.truncated_normal(shape=[n_neurons2, n_neurons3], stddev=0.1), name="wf3")
Bf3 = tf.Variable(tf.zeros(shape=[n_neurons3]), name="bf3")


def newConLayer(input, W, B, pooling=True, activation_function=tf.nn.relu, ksize=[1, 2, 2, 1], strides=[1, 1, 1, 1],
                index=""):
    L = tf.nn.conv2d(input, W, strides=strides, padding='SAME') + B
    if pooling:
        L = tf.nn.max_pool(value=L, ksize=ksize, strides=strides, padding='SAME')
    batch_norm, mua = batchnorm(L, is_test, iteration, convolutional=True)
    A = activation_function(batch_norm)
    return A, mua


def newFcLayer(input, W, B, activation_function=tf.nn.relu, last=False, index=""):
    if last:
        return tf.matmul(input, W) + B
    else:
        fc = tf.matmul(input, W) + B
        batch_norm, mua = batchnorm(fc, is_test, iteration, convolutional=False)
        A = activation_function(batch_norm)
        dropout = tf.nn.dropout(A, keep_prob=p_keep)
        return dropout, mua


def batchnorm(Ylogits, is_test, iteration, convolutional=False):
    exp_moving_avg = tf.train.ExponentialMovingAverage(0.999, iteration)
    bnepsilon = 1e-5
    if convolutional:
        mean, variance = tf.nn.moments(Ylogits, [0, 1, 2])
    else:
        mean, variance = tf.nn.moments(Ylogits, [0])
    update_moving_everages = exp_moving_avg.apply([mean, variance])
    m = tf.cond(is_test, lambda: exp_moving_avg.average(mean), lambda: mean)
    v = tf.cond(is_test, lambda: exp_moving_avg.average(variance), lambda: variance)
    Ybn = tf.nn.batch_normalization(Ylogits, m, v, 0.0, 1.0, bnepsilon)
    return Ybn, update_moving_everages


X = tf.placeholder(tf.float32, shape=[None, pic_w * pic_h])
Y_labels = tf.placeholder(tf.float32, shape=[None, num_classes])
X_r = tf.reshape(X, shape=[-1, pic_w, pic_h, 1])
cl1, mau1 = newConLayer(X_r, Wc1, Bc1, pooling=True, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1])
cl2, mau2 = newConLayer(cl1, Wc2, Bc2, pooling=True, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1])
cl3, mau3 = newConLayer(cl2, Wc3, Bc3, pooling=True, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1])
cl4, mau6 = newConLayer(cl3, Wc4, Bc4, pooling=True, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1])
cl5, mau7 = newConLayer(cl4, Wc5, Bc5, pooling=False)
flatten = tf.reshape(cl5, shape=[-1, k])
fc1, mau4 = newFcLayer(flatten, Wf1, Bf1)
fc2, mau5 = newFcLayer(fc1, Wf2, Bf2)
fc3 = newFcLayer(fc2, Wf3, Bf3, last=True)
Y_predict = fc3

update = tf.group(mau1, mau2, mau3, mau4, mau5, mau6, mau7)

# cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=fc3, labels=Y_labels)
# cross_entropy = tf.losses.absolute_difference(labels=Y_labels, predictions=Y_predict)
cross_entropy = tf.losses.mean_squared_error(labels=Y_labels, predictions=Y_predict)
# cross_entropy = tf.reduce_mean(cross_entropy)
# optimizer = tf.train.AdamOptimizer(learning_rate = lr)
optimizer = tf.train.RMSPropOptimizer(learning_rate=lr)
minimize = optimizer.minimize(cross_entropy)

"""predicted = tf.argmax(Y_predict, 1)
true = tf.argmax(Y_labels,1)
correct_predictions = tf.equal(predicted, true)
accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32))"""
accuracy = tf.metrics.accuracy(labels=Y_labels, predictions=Y_predict)
saver = tf.train.Saver()
session = tf.Session()
#session.run(tf.global_variables_initializer())
#session.run(tf.local_variables_initializer())
train_batch_size = 60
test_batch_size = 10000
num_iterations = 5000

# for i in range(num_iterations):
#
#     max_learning_rate = 0.01
#     min_learning_rate = 0.0001
#     s = 7500
#     learning_rate = min_learning_rate + (max_learning_rate - min_learning_rate) * math.exp(-i / (s * 0.145))
#
#     x_train_batch, y_train_batch = loader.next_batch(60)
#     feed_dict_train = {X: x_train_batch, Y_labels: y_train_batch, lr: learning_rate, p_keep: 0.8, is_test: False,
#                        iteration: i}
#     c1 = session.run(cl1,feed_dict=feed_dict_train)
#     c2 = session.run(cl2,feed_dict=feed_dict_train)
#     c3 = session.run(cl3,feed_dict=feed_dict_train)
#     c4 = session.run(cl4,feed_dict=feed_dict_train)
#     c5 = session.run(cl5,feed_dict=feed_dict_train)
#     print(c1.shape)
#     print(c2.shape)
#     print(c3.shape)
#     print(c4.shape)
#     print(c5.shape)
#     session.run(minimize, feed_dict=feed_dict_train)
#     session.run(update, feed_dict=feed_dict_train)
#     if (i % 100 == 0):
#         x_train_batch, y_train_batch = loader.next_batch(100)
#         feed_dict_train = {X: x_train_batch, Y_labels: y_train_batch, lr: learning_rate, p_keep: 0.6, is_test: True,
#                            iteration: i}
#         loss, acc = session.run([cross_entropy, accuracy], feed_dict=feed_dict_train)
#         print("iter:", i, "loss:", loss, "acc:", acc)

"""tf.add_to_collection('sir', Wc1)
tf.add_to_collection('sir', Bc1)        
tf.add_to_collection('sir', Wc2)        
tf.add_to_collection('sir', Bc2)        
tf.add_to_collection('sir', Wc3)        
tf.add_to_collection('sir', Bc3)        
tf.add_to_collection('sir', Wc4)        
tf.add_to_collection('sir', Bc4)        
tf.add_to_collection('sir', Wc5)        
tf.add_to_collection('sir', Bc5)
tf.add_to_collection('sir', Wf1)        
tf.add_to_collection('sir', Bf1)        
tf.add_to_collection('sir', Wf2)        
tf.add_to_collection('sir', Bf2)        
tf.add_to_collection('sir', Wf3)        
tf.add_to_collection('sir', Bf3)"""
"""x_test_batch=[]
y_test_batch = []
feed_dict_test = {X:x_test_batch, Y_labels:y_test_batch, lr:learning_rate, p_keep:1.0, is_test:True, iteration:4}
acc, p,last_layer = session.run([accuracy,predicted,fc3], feed_dict=feed_dict_test)
print("accuracy on 10000 test images -> {acc}".format(acc=acc))"""
"""img,lbl,pred,a_strenght = collect_wrong_predictions(x_test_batch,y_test_batch,p, last_layer)
plot_wrong_predictions(img, lbl,pred, a_strenght, bound=10)
plt.show()
img,lbl,pred,a_strenght = collect_right_predictions(x_test_batch,y_test_batch,p, last_layer)
plot_wrong_predictions(img, lbl,pred, a_strenght, bound=10)
plt.show()"""
saver.restore(session, "/tmp/model.ckpt")
x_train_batch, y_train_batch = loader.next_batch(1)
image = x_train_batch[0]
image_r = np.reshape(image, (96,96))
plt.subplot(2,1,1)
plt.imshow(image_r, cmap="gray")
tocke = y_train_batch[0]
tocke = tocke*48 + 48
plt.scatter(tocke[::2], tocke[1::2], c="b")
feed_dict_train = {X: x_train_batch, Y_labels: y_train_batch, lr: 0.01, p_keep: 0.8, is_test: True,
                       iteration: 0}
predicted = session.run(Y_predict, feed_dict= feed_dict_train)[0]
predicted = predicted*48 + 48
plt.scatter(predicted[::2], predicted[1::2], c="r")

plt.subplot(2,1,2)
flipped_image = x_train_batch.reshape(-1,1,96,96)[:,:,:,::-1]
plt.imshow(flipped_image[0][0], cmap="gray")

y_new = np.copy(y_train_batch)
y_new[:, ::2] = y_new[:, ::2] * -1

flip_indices = [
    (0, 2), (1, 3),
    (4, 8), (5, 9), (6, 10), (7, 11),
    (12, 16), (13, 17), (14, 18), (15, 19),
    (22, 24), (23, 25),
    ]

for a, b in flip_indices:
    tmp = np.copy(y_new[:, a])
    y_new[:, a]= y_new[:, b]
    y_new[:, b]= tmp

y_0_shifted = y_new[0]*48 + 48
plt.scatter(y_0_shifted[::2], y_0_shifted[1::2], c="r")
plt.show()



