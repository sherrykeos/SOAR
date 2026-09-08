"""
Vision module for SOAR.
Provides base vision interfaces and adapters for processing and describing image knowledge assets.
"""

from .base import BaseVisionProcessor, MockVisionProcessor

__all__ = [
    "BaseVisionProcessor",
    "MockVisionProcessor",
]
