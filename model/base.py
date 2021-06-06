import math

from abc import ABC, abstractmethod

import torch
import torch.nn as nn
import torch.nn.functional as F

from .network_utils import get_block


def construct_supernet_layer(
        micro_cfg,
        in_channels,
        out_channels,
        stride,
        bn_momentum,
        bn_track_running_stats):
    supernet_layer = nn.ModuleList()
    for b_cfg in micro_cfg:
        block_type, kernel_size, se, activation, kwargs = b_cfg
        block = get_block(block_type=block_type,
                          in_channels=in_channels,
                          out_channels=out_channels,
                          kernel_size=kernel_size,
                          stride=stride,
                          activation=activation,
                          se=se,
                          bn_momentum=bn_momentum,
                          bn_track_running_stats=bn_track_running_stats,
                          **kwargs
                          )
        supernet_layer.append(block)
    return supernet_layer


class BaseSupernet(nn.Module):
    def __init__(
            self,
            classes,
            dataset,
            bn_momentum=0.1,
            bn_track_running_stats=True):
        super(BaseSupernet, self).__init__()
        self.macro_cfg, self.micro_cfg = self.get_model_cfg(classes)

        self.classes = classes
        self.dataset = dataset

        bn_momentum = bn_momentum
        bn_track_running_stats = bn_track_running_stats

        self.forward_state = "single"  # [single, sum]

        # First Stage
        self.first_stages = nn.ModuleList()
        for l_cfg in self.macro_cfg["first"]:
            block_type, in_channels, out_channels, stride, kernel_size, activation, se, kwargs = l_cfg

            layer = get_block(block_type=block_type,
                              in_channels=in_channels,
                              out_channels=out_channels,
                              kernel_size=kernel_size,
                              stride=stride,
                              activation=activation,
                              se=se,
                              bn_momentum=bn_momentum,
                              bn_track_running_stats=bn_track_running_stats,
                              **kwargs)
            self.first_stages.append(layer)

        # Search Stage
        self.search_stages = nn.ModuleList()
        for l_cfg in self.macro_cfg["search"]:
            in_channels, out_channels, stride = l_cfg

            layer = construct_supernet_layer(
                micro_cfg=self.micro_cfg,
                in_channels=in_channels,
                out_channels=out_channels,
                stride=stride,
                bn_momentum=bn_momentum,
                bn_track_running_stats=bn_track_running_stats)
            self.search_stages.append(layer)

        # Last Stage
        self.last_stages = nn.ModuleList()
        for l_cfg in self.macro_cfg["last"]:
            block_type, in_channels, out_channels, stride, kernel_size, activation, se, kwargs = l_cfg

            layer = get_block(block_type=block_type,
                              in_channels=in_channels,
                              out_channels=out_channels,
                              kernel_size=kernel_size,
                              stride=stride,
                              activation=activation,
                              se=se,
                              bn_momentum=bn_momentum,
                              bn_track_running_stats=bn_track_running_stats,
                              **kwargs)
            self.last_stages.append(layer)

        self._initialize_weights()

    def forward(self, x):
        for i, l in enumerate(self.first_stages):
            x = l(x)

        for i, l in enumerate(self.search_stages):
            self._forward_step(x)

        for i, l in enumerate(self.last_stages):
            x = l(x)

        return x

    def _forward_step(self, x):
        if self.forward_state == "gumbel_sum":
            weight = F.gumbel_softmax(self.arch_param[i], dim=0) 
            x = sum(p * b(x) for p, b in zip(weight, l))

        elif self.forward_state == "sum":
            weight = F.softmax(self.arch_param[i], dim=0)
            x = sum(p * b(x) for p, b in zip(weight, l))

        elif self.forward_state == "single":
            x = l[self.architecture[i]](x)

        return x


    def set_arch_param(self, arch_param):
        """
        Set architecture parameter directly
        """
        self.arch_param = arch_param
        

    def get_arch_param_nums(self):
        micro_len = len(self.micro_cfg)
        macro_len = len(self.macro_cfg["search"])

        return (macro_len, micro_len)

    def set_activate_architecture(self, architecture):
        """
        Activate the path based on the passed architecture.
        """
        self.architecture = architecture

    def initialize_arch_param(self):
        micro_len = len(self.micro_cfg)
        macro_len = len(self.macro_cfg["search"])

        self.arch_param = nn.Parameter(
            1e-3 * torch.randn((macro_len, micro_len), requires_grad=False))

    def get_arch_param(self):
        return self.arch_param

    def get_best_arch_param(self):
        """
        Get the best neural architecture by architecture parameters (argmax).
        """
        best_architecture = self.arch_param.data.argmax(dim=1)
        best_architecture = best_architecture.cpu().numpy()
        return best_architecture

    def set_forward_state(self, state):
        """
        Set supernet forward state. ["single", "sum"]
        """
        self.forward_state = state

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()

    @abstractmethod
    def get_model_cfg(self, classes):
        raise NotImplemented


