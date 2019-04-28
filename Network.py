import numpy as np
np.random.seed(111)

# parameters for initialization
INIT_MEAN = 0.0
INIT_STD = 0.01


class Fully_Connected:

    def __init__(self, layers, initial_lr, reg, dropout, activations_func):
        self.lr = initial_lr  # learning rate
        self.reg = reg  # lambda
        self.dropout = dropout  # a list of dropout probability per layer
        self.layers = layers  # list of layers size
        self.activation_functions = activations_func  # list of activation functions
        self.is_train = True
        self.activations = []

        # data structures for saving weights and gradients of each layer
        self.weights = [np.random.normal(INIT_MEAN, INIT_STD, (prev_layer + 1, next_layer)) for prev_layer, next_layer in zip(layers, layers[1:])]
        self.grads = [np.zeros((prev_layer + 1, next_layer)) for prev_layer, next_layer in zip(layers, layers[1:])]

    def forward(self, x):
        # x - matrix of examples. Each example in a different column
        batch_size = np.size(x, 1)

        out = x.copy()  # copy input
        for layer_num in range(len(self.layers) - 1):
            # add bias to each layer and save activations
            out = np.concatenate((np.ones(batch_size).reshape(1, -1), out), axis=0)
            self.activations.append(out.copy())

            # linear transformation
            out = np.dot(self.weights[layer_num].transpose(), out)  # z = Wx

            # non linearity
            if self.activation_functions[layer_num] == "relu":
                out = np.maximum(out, 0)  # a = relu(z, 0)
            elif self.activation_functions[layer_num] == "tanh":
                out = np.tanh(out)  # a = tanh(z)
            elif self.activation_functions[layer_num] == "softmax":
                max_val = np.max(out, axis=0)  # find the max valued class in each column (example)
                e_x = np.exp(out - max_val)  # subtract max_val from all values of each example to prevent overflow
                out = e_x/np.sum(e_x, axis=0)  # a = tanh(z)

            # dropout in training time and not on the last layer
            if self.is_train:
                success_prob = 1 - self.dropout[layer_num]  # 0.2 dropout is 0.2 success = ~0.8 should of neurons should not be zeroed out
                num_neurons = np.size(self.weights[layer_num], 1)  # number of output neurons
                mask = np.random.binomial(n=1, p=success_prob, size=batch_size*num_neurons).reshape(-1, batch_size)
                out = out * mask / success_prob  # element wise multiplication by the mask and scaling output

        return out.copy()

    def backward(self, net_out, labels):

        def dactivation_dz(layer, activation_val):
            if self.activation_functions[layer] == "tanh":
                return 1 - np.tanh(activation_val) ** 2
            if self.activation_functions[layer] == "relu":
                return activation_val

        batch_size = np.size(labels, 1)
        dL_da = []

        for layer in range(len(self.layers), 0, -1):
            for example_idx in range(batch_size):
                if layer == len(self.layers) - 1:
                    delta = (net_out[:, example_idx] - labels[:, example_idx])
                else:
                    delta = dL_da[example_idx] * dactivation_dz(layer, self.activations[layer][:, example_idx])
                prev_act = self.activations[layer - 1][:, example_idx].transpose()
                self.grads[layer] += np.dot(delta, prev_act)  # dL/dw = (a_m - T)*a_m-1^T
                dL_da.append(np.dot(self.weights[layer].transpose(), delta))  # dL/d(a_m-1) = w_m^T*(a_m - T)
            self.grads[layer] += self.reg*self.weights[layer]  # add regularization

    # return the sum and average of losses per batch
    def loss_function(self, net_out, labels):
        sum_weights = 0.0
        for l in range(len(self.layers) - 1):
            sum_weights += np.sum(self.weights[l] ** 2)  # L2 loss proportional to the loss value
        loss = np.sum(net_out * labels, axis=0) + self.reg*sum_weights
        return np.sum(loss), np.average(loss)

    def test_time(self):
        self.is_train = False

    def train_time(self):
        self.is_train = True

    def init_vals(self):
        self.activations = []
        self.grads = [np.zeros((prev_layer + 1, next_layer)) for prev_layer, next_layer in zip(self.layers, self.layers[1:])]



