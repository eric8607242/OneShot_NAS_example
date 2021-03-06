import torch.nn as nn

from ..base_model import BaseModel
from ..block_builder import get_block


class ProxylessNASModel(BaseModel):
    def _construct_stage_layers(self, architecture, bn_momentum, bn_track_running_stats, *args, **kwargs):
        """ Construct searched layers in entire search stage.

        Return:
            stages (nn.Sequential)
        """
        stages = []
        for l_cfg, block_idx in zip(self.macro_cfg["search"], architecture):
            in_channels, out_channels, stride = l_cfg

            block_type, kernel_size, se, activation, cfg_kwargs = self.micro_cfg[block_idx]
            layer = get_block(block_type=block_type,
                              in_channels=in_channels,
                              out_channels=out_channels,
                              kernel_size=kernel_size,
                              stride=stride,
                              activation=activation,
                              se=se,
                              bn_momentum=bn_momentum,
                              bn_track_running_stats=bn_track_running_stats,
                              **cfg_kwargs)
            stages.append(layer)

        stages = nn.Sequential(*stages)
        return stages


