import torch
import torch.nn as nn
import gc


def center_crop(layer, target_height, target_width):
    _, _, layer_height, layer_width = layer.size()
    diff_y = (layer_height - target_height) // 2
    diff_x = (layer_width - target_width) // 2
    return layer[:, :, diff_y : (diff_y + target_height), diff_x : (diff_x + target_width)]


def align_layers(layers):
    layer_heights = []
    layer_widths = []
    rtn = []
    for layer in layers:
        layer_heights.append(layer.size(2))
        layer_widths.append(layer.size(3))
    target_height = min(layer_heights)
    target_width = min(layer_widths)
    for layer, layer_height, layer_width in zip(layers, layer_heights, layer_widths):
        diff_y = (layer_height - target_height) // 2
        diff_x = (layer_width - target_width) // 2
        rtn.append(layer[:, :, diff_y : (diff_y + target_height), diff_x : (diff_x + target_width)])
    torch.cuda.empty_cache()
    gc.collect()
    return torch.cat(rtn, dim=1)


class ConvolutionBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

    def forward(self, x):
        return self.conv_layers(x)


class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = ConvolutionBlock(in_channels, out_channels)
        self.mpool = nn.MaxPool2d((2, 2))

    def forward(self, x):
        skip = self.conv(x)
        out = self.mpool(skip)
        return skip, out


class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up_conv = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2, padding=0)
        self.conv = ConvolutionBlock(out_channels + out_channels, out_channels)

    def forward(self, x, skip):
        out = self.up_conv(x)
        if out.size(2) != skip.size(2) or out.size(3) != skip.size(3):
            skip = center_crop(skip, out.size(2), out.size(3))

        out = torch.cat([out, skip], axis=1)
        out = self.conv(out)
        return out


class UpConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up_conv = nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2),
            nn.Dropout(0.2),
        )

    def forward(self, x):
        return self.up_conv(x)


class UNET(nn.Module):
    def __init__(self, in_channels=4, out_channels=1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.e1 = EncoderBlock(in_channels, 64)
        self.e2 = EncoderBlock(64, 128)
        self.e3 = EncoderBlock(128, 256)
        self.e4 = EncoderBlock(256, 512)

        self.b = ConvolutionBlock(512, 1024)

        self.d1 = DecoderBlock(1024, 512)
        self.d2 = DecoderBlock(512, 256)
        self.d3 = DecoderBlock(256, 128)
        self.d4 = DecoderBlock(128, 64)
        self.output = nn.Conv2d(64, out_channels, kernel_size=1, padding=0)

    def forward(self, x):
        skip1, out = self.e1(x)
        skip2, out = self.e2(out)
        skip3, out = self.e3(out)
        skip4, out = self.e4(out)

        out = self.b(out)
        out = self.d1(out, skip4)
        out = self.d2(out, skip3)
        out = self.d3(out, skip2)
        out = self.d4(out, skip1)
        out = torch.squeeze(out)
        out = self.output(out)

        return out

    def predict(self, x):
        out = self.forward(x)
        if self.out_channels == 1:
            out = torch.sigmoid(out)
        elif self.out_channels > 1:
            out = torch.softmax(out)
        return out


class UNETPP(nn.Module):
    def __init__(self, pretrained_unet=None, freeze_weights=False, deep_vision=False, in_channels=4, out_channels=1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.pretrained_unet = pretrained_unet
        self.deep_vision = deep_vision
        self.upsamp = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        if self.pretrained_unet is not None:
            self.conv0_0 = self.pretrained_unet.e1
            self.conv1_0 = self.pretrained_unet.e2
            self.conv2_0 = self.pretrained_unet.e3
            self.conv3_0 = self.pretrained_unet.e4
            self.conv4_0 = EncoderBlock(512, 1024)
            if freeze_weights:
                for param in self.conv0_0.parameters():
                    param.requires_grad = False
                for param in self.conv1_0.parameters():
                    param.requires_grad = False
                for param in self.conv2_0.parameters():
                    param.requires_grad = False
                for param in self.conv3_0.parameters():
                    param.requires_grad = False
        else:
            self.conv0_0 = EncoderBlock(in_channels, 64)
            self.conv1_0 = EncoderBlock(64, 128)
            self.conv2_0 = EncoderBlock(128, 256)
            self.conv3_0 = EncoderBlock(256, 512)
            self.conv4_0 = EncoderBlock(512, 1024)

        self.conv0_1 = ConvolutionBlock(64 + 128, 64)
        self.conv0_2 = ConvolutionBlock(2 * 64 + 128, 64)
        self.conv0_3 = ConvolutionBlock(3 * 64 + 128, 64)
        self.conv0_4 = ConvolutionBlock(4 * 64 + 128, 64)

        self.conv1_1 = ConvolutionBlock(128 + 256, 128)
        self.conv1_2 = ConvolutionBlock(2 * 128 + 256, 128)
        self.conv1_3 = ConvolutionBlock(3 * 128 + 256, 128)

        self.conv2_1 = ConvolutionBlock(256 + 512, 256)
        self.conv2_2 = ConvolutionBlock(2 * 256 + 512, 256)

        self.conv3_1 = ConvolutionBlock(512 + 1024, 512)

        self.up_conv1_0 = UpConv(128, 128)
        self.up_conv2_0 = UpConv(256, 256)
        self.up_conv3_0 = UpConv(512, 512)

        self.up_conv1_1 = UpConv(128, 128)
        self.up_conv2_1 = UpConv(256, 256)
        self.up_conv1_2 = UpConv(128, 128)

        self.up_conv4_0 = UpConv(1024, 1024)
        self.up_conv3_1 = UpConv(512, 512)
        self.up_conv2_2 = UpConv(256, 256)
        self.up_conv1_3 = UpConv(128, 128)

        if self.deep_vision:
            self.deep1 = nn.Conv2d(64, out_channels, kernel_size=1)
            self.deep2 = nn.Conv2d(64, out_channels, kernel_size=1)
            self.deep3 = nn.Conv2d(64, out_channels, kernel_size=1)
            self.deep4 = nn.Conv2d(64, out_channels, kernel_size=1)
        else:
            self.deep = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        skip0_0, x0_0 = self.conv0_0(x)
        skip1_0, x1_0 = self.conv1_0(x0_0)
        skip2_0, x2_0 = self.conv2_0(x1_0)
        skip3_0, x3_0 = self.conv3_0(x2_0)
        skip4_0, x4_0 = self.conv4_0(x3_0)

        x0_1 = self.conv0_1(torch.cat([skip0_0, self.up_conv1_0(skip1_0)], dim=1))
        x1_1 = self.conv1_1(torch.cat([skip1_0, self.up_conv2_0(skip2_0)], dim=1))
        x0_2 = self.conv0_2(torch.cat([skip0_0, x0_1, self.up_conv1_1(x1_1)], dim=1))

        x2_1 = self.conv2_1(torch.cat([skip2_0, self.up_conv3_0(skip3_0)], dim=1))
        x1_2 = self.conv1_2(torch.cat([skip1_0, x1_1, self.up_conv2_1(x2_1)], dim=1))
        x0_3 = self.conv0_3(torch.cat([skip0_0, x0_1, x0_2, self.up_conv1_2(x1_2)], dim=1))

        x3_1 = self.conv3_1(torch.cat([skip3_0, self.up_conv4_0(skip4_0)], dim=1))
        x2_2 = self.conv2_2(torch.cat([skip2_0, x2_1, self.up_conv3_1(x3_1)], dim=1))
        x1_3 = self.conv1_3(torch.cat([skip1_0, x1_1, x1_2, self.up_conv2_2(x2_2)], dim=1))
        x0_4 = self.conv0_4(torch.cat([skip0_0, x0_1, x0_2, x0_3, self.up_conv1_3(x1_3)], dim=1))

        if self.deep_vision:
            out1 = self.deep1(x0_1)
            out2 = self.deep2(x0_2)
            out3 = self.deep3(x0_3)
            out4 = self.deep4(x0_4)
            return [out1, out2, out3, out4]
        else:
            out = self.deep(x0_4)
        return out

    def predict(self, x):
        skip0_0, x0_0 = self.conv0_0(x)
        skip1_0, x1_0 = self.conv1_0(x0_0)
        skip2_0, x2_0 = self.conv2_0(x1_0)
        skip3_0, x3_0 = self.conv3_0(x2_0)
        skip4_0, x4_0 = self.conv4_0(x3_0)

        x0_1 = self.conv0_1(align_layers([skip0_0, self.up_conv1_0(skip1_0)]))
        x1_1 = self.conv1_1(align_layers([skip1_0, self.up_conv2_0(skip2_0)]))
        x0_2 = self.conv0_2(align_layers([skip0_0, x0_1, self.up_conv1_1(x1_1)]))
        x2_1 = self.conv2_1(align_layers([skip2_0, self.up_conv3_0(skip3_0)]))
        x1_2 = self.conv1_2(align_layers([skip1_0, x1_1, self.up_conv2_1(x2_1)]))
        x0_3 = self.conv0_3(align_layers([skip0_0, x0_1, x0_2, self.up_conv1_2(x1_2)]))
        x3_1 = self.conv3_1(align_layers([skip3_0, self.up_conv4_0(skip4_0)]))
        x2_2 = self.conv2_2(align_layers([skip2_0, x2_1, self.up_conv3_1(x3_1)]))
        x1_3 = self.conv1_3(align_layers([skip1_0, x1_1, x1_2, self.up_conv2_2(x2_2)]))
        x0_4 = self.conv0_4(align_layers([skip0_0, x0_1, x0_2, x0_3, self.up_conv1_3(x1_3)]))

        if self.deep_vision:
            out1 = self.deep1(x0_1)
            out2 = self.deep2(x0_2)
            out3 = self.deep3(x0_3)
            out4 = self.deep4(x0_4)
            x = out4.size(2)
            y = out4.size(3)
            out1 = center_crop(out1, x, y)
            out2 = center_crop(out2, x, y)
            out3 = center_crop(out3, x, y)
            out = out1 + out2 + out3 + out4
            out = out / 4
        else:
            out = self.deep(x0_4)

        if self.out_channels == 1:
            out = torch.sigmoid(out)
        elif self.out_channels > 1:
            out = torch.softmax(out)
        return out


def load_models(unet_checkpoint_path, unetpp_checkpoint_path):
    """
    Function to load U-Net and U-Net++ models from checkpoint files.

    :param unet_checkpoint_path: Path to the U-Net checkpoint file (.sav).
    :param unetpp_checkpoint_path: Path to the U-Net++ checkpoint file (.sav).
    :return: Tuple containing the U-Net and U-Net++ models.
    """

    # Load U-Net model
    checkpoint_unet = torch.load(unet_checkpoint_path, map_location=torch.device("cpu"))
    model_unet = UNET()
    model_unet.load_state_dict(checkpoint_unet["model_state_dict"])

    # Load U-Net++ model
    checkpoint_unetpp = torch.load(unetpp_checkpoint_path, map_location=torch.device("cpu"))

    # Extract parameters used during saving
    # pretrained_unet = checkpoint_unetpp.get('pretrained_unet', None)
    freeze_weights = checkpoint_unetpp.get("freeze_weights", False)
    deep_vision = checkpoint_unetpp.get("deep_vision", False)
    in_channels = checkpoint_unetpp.get("in_channels", 4)
    out_channels = checkpoint_unetpp.get("out_channels", 1)

    # Initialize the U-Net++ model with the saved parameters
    model_unetpp = UNETPP(
        pretrained_unet=model_unet,
        freeze_weights=freeze_weights,
        deep_vision=deep_vision,
        in_channels=in_channels,
        out_channels=out_channels,
    )

    # Load state dictionary into the U-Net++ model
    model_unetpp.load_state_dict(checkpoint_unetpp["model_state_dict"])

    return model_unet, model_unetpp
