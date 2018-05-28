import imp
import tensorflow as tf
from tensorflow.python.framework import ops

lib_file = imp.find_module('kernels', __path__)[1]
_warprnnt = tf.load_op_library(lib_file)


def rnnt_loss(trans_acts, pred_acts, labels, input_lengths, label_lengths,
        blank_label=0):
    '''Computes the RNNT loss between a sequence of activations and a
    ground truth labeling.
    Args:
        trans_acts: A 3-D Tensor of floats.  The dimensions
                     should be (B, T, V), where T is the time index, B
                     is the minibatch index, and V indexes over
                     activations for each symbol in the alphabet.
        pred_acts: A 3-D Tensor of floats.  The dimensions
                     should be (B, U, V), where U is the predicted label, B
                     is the minibatch index, and V indexes over
                     activations for each symbol in the alphabet.
        labels: A 2-D Tensor of ints, a padded label sequences to make sure 
                     labels for the minibatch are same length.
        input_lengths: A 1-D Tensor of ints, the number of time steps
                       for each sequence in the minibatch.
        label_lengths: A 1-D Tensor of ints, the length of each label
                       for each example in the minibatch.
        blank_label: int, the label value/index that the RNNT
                     calculation should use as the blank label
    Returns:
        1-D float Tensor, the cost of each example in the minibatch
        (as negative log probabilities).
    * This class performs the softmax operation internally.
    * The label reserved for the blank symbol should be label 0.
    '''
    loss, _, _ = _warprnnt.warp_rnnt(trans_acts, pred_acts, labels, input_lengths,
                                  label_lengths, blank_label)
    return loss


@ops.RegisterGradient("WarpRNNT")
def _RNNTLossGrad(op, grad_loss, trans_grad, pred_grad):
    trans_grad = op.outputs[1]
    pred_grad = op.outputs[2]
    # NOTE since here we are batch first, cannot use _BroadcastMul
    grad_loss = tf.reshape(grad_loss, (-1, 1, 1))
    return [grad_loss * trans_grad, grad_loss * pred_grad, None, None, None]

@ops.RegisterShape("WarpRNNT")
def _RNNTLossShape(op):
    trans_inputs_shape = op.inputs[0].get_shape().with_rank(3)
    pred_input_shape = op.inputs[1].get_shape().with_rank(3)
    batch_size = trans_inputs_shape[0]
    return [batch_size, trans_inputs_shape, pred_input_shape]
