"""
Breast Cancer AI Models
Contains model definitions for both BI-RADS and pathological classification
"""

import torch
import torch.nn as nn
from typing import Optional


class BasicBlock(nn.Module):
    """ResNet Basic Block for pathological classification model"""
    
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1, identity_downsample: Optional[nn.Module] = None):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.identity_downsample = identity_downsample

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply forward computation."""
        identity = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.bn2(x)

        if self.identity_downsample is not None:
            identity = self.identity_downsample(identity)
        
        x += identity
        x = self.relu(x)
        return x


class ResNet18(nn.Module):
    """
    Original ResNet-18 Model for pathological classification (matches checkpoint)
    """
    
    def __init__(self, input_channels: int = 3, num_classes: int = 3):
        super(ResNet18, self).__init__()
        self.conv1 = nn.Conv2d(input_channels, 64, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(64, 64, stride=1)
        self.layer2 = self._make_layer(64, 128, stride=2)
        self.layer3 = self._make_layer(128, 256, stride=2)
        self.layer4 = self._make_layer(256, 512, stride=2)

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def identity_downsample(self, in_channels: int, out_channels: int) -> nn.Module:
        """Downsampling block to reduce the feature sizes."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(out_channels)
        )

    def _make_layer(self, in_channels: int, out_channels: int, stride: int) -> nn.Module:
        """Create sequential basic block."""
        identity_downsample = None
        if stride != 1:
            identity_downsample = self.identity_downsample(in_channels, out_channels)

        return nn.Sequential(
            BasicBlock(in_channels, out_channels, identity_downsample=identity_downsample, stride=stride),
            BasicBlock(out_channels, out_channels)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.shape[0], -1)
        x = self.fc(x)
        return x


class BreastCancerResNet18(nn.Module):
    """ResNet-18 Model for pathological classification (benign, malignant, normal)"""
    
    def __init__(self, input_channels: int = 3, num_classes: int = 3):
        super(BreastCancerResNet18, self).__init__()
        self.conv1 = nn.Conv2d(input_channels, 64, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(64, 64, stride=1)
        self.layer2 = self._make_layer(64, 128, stride=2)
        self.layer3 = self._make_layer(128, 256, stride=2)
        self.layer4 = self._make_layer(256, 512, stride=2)

        # Last layers
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def identity_downsample(self, in_channels: int, out_channels: int) -> nn.Module:
        """Downsampling block to reduce the feature sizes."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(out_channels)
        )

    def _make_layer(self, in_channels: int, out_channels: int, stride: int) -> nn.Module:
        """Create sequential basic block."""
        identity_downsample = None

        if stride != 1:
            identity_downsample = self.identity_downsample(in_channels, out_channels)

        return nn.Sequential(
            BasicBlock(in_channels, out_channels, identity_downsample=identity_downsample, stride=stride),
            BasicBlock(out_channels, out_channels)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.shape[0], -1)
        x = self.fc(x)
        return x


class SimpleConvNet(nn.Module):
    """Simple CNN for BI-RADS classification as a fallback"""
    
    def __init__(self, num_classes: int = 5):
        super(SimpleConvNet, self).__init__()
        
        self.conv_layers = nn.Sequential(
            # First conv block
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Second conv block
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Third conv block
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        
        # Adaptive pooling to handle variable input sizes
        self.adaptive_pool = nn.AdaptiveAvgPool2d((7, 7))
        
        # Classification layers
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(128 * 7 * 7, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        x = self.conv_layers(x)
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.classifier(x)
        return x


# Class names for different analysis types
BIRADS_CLASS_NAMES = [
    "BI-RADS 1 (Negative)",
    "BI-RADS 2 (Benign)",
    "BI-RADS 3 (Probably Benign)",
    "BI-RADS 4 (Suspicious)",
    "BI-RADS 5 (Highly Suspicious)"
]

PATHOLOGICAL_CLASS_NAMES = ["benign", "malignant", "normal"]