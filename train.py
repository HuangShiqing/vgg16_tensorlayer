import tensorflow as tf
import time
import os
from model import *
from varible import *
from data import read_data, data_generator


def losses(logits, labels):
    with tf.variable_scope('loss') as scope:
        cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits \
            (logits=logits, labels=labels, name='xentropy_per_example')
        loss = tf.reduce_mean(cross_entropy, name='loss')
        tf.summary.scalar(scope.name + '/loss', loss)
    return loss


def optimizer_adam(loss, learning_rate):
    with tf.name_scope('optimizer'):
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
        global_step = tf.Variable(0, name='global_step', trainable=False)
        train_op = optimizer.minimize(loss, global_step=global_step)
    return train_op


def optimizer_sgd(loss, learning_rate):
    with tf.name_scope('optimizer'):
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
        global_step = tf.Variable(0, name='global_step', trainable=False)
        train_op = optimizer.minimize(loss, global_step=global_step)
    return train_op


def main():
    x_train, y_train, x_valid, y_valid = read_data(Gb_data_dir)

    batch_size = Gb_batch_size
    learning_rate = Gb_learning_rate
    log_dir = Gb_ckpt_dir
    final_dir = Gb_ckpt_dir
    n_epoch = Gb_epoch
    n_step_epoch = int(len(y_train) / batch_size)
    save_frequency = Gb_save_frequency

    input_pb = tf.placeholder(tf.float32, [None, 224, 224, 3])
    label_pb = tf.placeholder(tf.int32, [None])
    logist = vgg16_model(input_pb)
    loss_op = losses(logits=logist, labels=label_pb)
    train_op = optimizer_sgd(loss_op, learning_rate=learning_rate)

    saver = tf.train.Saver(max_to_keep=1000)
    summary_op = tf.summary.merge_all()
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        train_writer = tf.summary.FileWriter(log_dir, sess.graph)
        step = 0
        min_loss = 10000000
        for epoch in range(n_epoch):
            step_epoch = 0
            # TODO shuffle chunks
            data_yield = data_generator(x_train, y_train)

            for img, lable in data_yield:
                step += 1
                step_epoch += 1
                start_time = time.time()
                loss, _, summary_str = sess.run([loss_op, train_op, summary_op],
                                                feed_dict={input_pb: img, label_pb: lable})
                train_writer.add_summary(summary_str, step)
                # 每step打印一次该step的loss
                print("Loss %fs  : Epoch %d  %d/%d: Step %d  took %fs" % (
                    loss, epoch, step_epoch, n_step_epoch, step, time.time() - start_time))

                if step % save_frequency == 0:
                    print("Save model " + "!" * 10)
                    save_path = saver.save(sess,
                                           final_dir + 'ep{0:03d}-step{1:d}-loss{2:.3f}'.format(epoch, step, loss))
                    if loss < min_loss:
                        min_loss = loss
                    else:
                        try:
                            os.remove(final_dir + temp + '.data-00000-of-00001')
                            os.remove(final_dir + temp + '.index')
                            os.remove(final_dir + temp + '.meta')
                        except:
                            pass
                        temp = 'ep{0:03d}-step{1:d}-loss{2:.3f}'.format(epoch, step, loss)


if __name__ == '__main__':
    main()
