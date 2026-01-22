"""
Entity Registry - 数据实体目录

【设计目的】
1. 描述系统中已存在的数据实体
2. 供开发者在开发子程序时参考
3. 避免重复创建语义相同的数据

【注意】
- 该目录不是 SQL Schema
- 子程序不得通过此目录绕过 Data API
- 子程序不得直接操作数据库

【文件格式】
YAML 或 JSON，描述实体的抽象层面信息
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class EntityRegistry:
    """
    数据实体目录管理器

    负责加载和查询数据实体信息
    """

    def __init__(self, registry_path: str) -> None:
        """
        初始化实体目录

        Args:
            registry_path: 实体目录文件路径（JSON/YAML）
        """
        self._registry_path = Path(registry_path)
        self._entities: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """加载实体目录文件"""
        if not self._registry_path.exists():
            return

        with open(self._registry_path, "r", encoding="utf-8") as f:
            if self._registry_path.suffix == ".json":
                data = json.load(f)
            else:
                import yaml

                data = yaml.safe_load(f)

        if isinstance(data, dict) and "entities" in data:
            for entity in data["entities"]:
                name = entity.get("name")
                if name:
                    self._entities[name] = entity

    def get_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定实体的定义信息

        Args:
            entity_name: 实体名称

        Returns:
            实体定义信息，不存在则返回 None
        """
        return self._entities.get(entity_name)

    def get_all_entities(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有实体定义

        Returns:
            实体名称 -> 实体定义 的字典
        """
        return self._entities.copy()

    def list_entity_names(self) -> List[str]:
        """
        列出所有实体名称

        Returns:
            实体名称列表
        """
        return list(self._entities.keys())

    def get_readable_entities(self) -> List[str]:
        """
        获取支持读取操作的实体列表

        Returns:
            支持 read 操作的实体名称列表
        """
        return [
            name
            for name, info in self._entities.items()
            if "read" in info.get("operations", [])
        ]

    def get_writable_entities(self) -> List[str]:
        """
        获取支持写入操作的实体列表

        Returns:
            支持 write 操作的实体名称列表
        """
        return [
            name
            for name, info in self._entities.items()
            if "write" in info.get("operations", [])
        ]

    def get_fields(self, entity_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取实体的可用字段信息

        Args:
            entity_name: 实体名称

        Returns:
            字段定义列表
        """
        entity = self.get_entity(entity_name)
        if entity:
            return entity.get("fields", [])
        return None
