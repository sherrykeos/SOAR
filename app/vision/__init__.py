"""
Vision package for SOAR.
Provides base vision interfaces, mock processor for testing,
and the local Qwen2.5-VL-3B-Instruct production vision model adapter.
"""

from .base import BaseVisionProcessor, MockVisionProcessor
from .qwen import QwenVisionProcessor

__all__ = [
    "BaseVisionProcessor",
    "MockVisionProcessor",
    "QwenVisionProcessor",
]
