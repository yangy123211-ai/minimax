"""
Core Package - 核心框架组件
"""

from .base import BaseTab
from .loader import TabLoader
from .main_window import MainWindow

__all__ = [
    "BaseTab",
    "MainWindow",
    "TabLoader",
]
