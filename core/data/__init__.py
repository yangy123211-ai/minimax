"""
Data Package - 数据访问层

提供统一的数据访问接口，屏蔽底层数据库实现细节
"""

from .data_api import DataAPI, get_data_api, set_data_api
from .entity_registry import EntityRegistry

__all__ = [
    "DataAPI",
    "get_data_api",
    "set_data_api",
    "EntityRegistry",
]
