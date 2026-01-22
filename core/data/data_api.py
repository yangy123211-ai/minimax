"""
Data API - 统一数据访问接口

【核心设计原则】
1. 子程序不得直接访问数据库
2. 所有数据操作必须通过 Data API
3. 子程序不知道数据库类型、表名、字段
4. Data API 负责数据一致性、缓存、事务等

【数据所有权规则】
- 数据不属于任何子程序
- 数据属于框架
- 子程序只是数据的"使用者"或"写入者之一"
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class DataAPI(ABC):
    """
    抽象数据访问接口

    所有数据操作必须通过此接口

    子程序使用示例：
        # 读取数据
        items = data_api.query("TaskEntity", filters={"status": "pending"})

        # 写入数据
        data_api.create("TaskEntity", {"title": "新任务", "content": "内容"})

        # 更新数据
        data_api.update("TaskEntity", task_id, {"status": "completed"})
    """

    @abstractmethod
    def query(
        self,
        entity_name: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        查询数据

        Args:
            entity_name: 实体名称（对应数据实体目录中的定义）
            filters: 过滤条件（抽象字段名 -> 值）
            order_by: 排序字段
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            符合条件的数据列表
        """
        pass

    @abstractmethod
    def get(self, entity_name: str, entity_id: Any) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取单条数据

        Args:
            entity_name: 实体名称
            entity_id: 数据 ID

        Returns:
            对应的数据记录，不存在则返回 None
        """
        pass

    @abstractmethod
    def create(self, entity_name: str, data: Dict[str, Any]) -> Any:
        """
        创建新数据

        Args:
            entity_name: 实体名称
            data: 要创建的数据（字段名 -> 值）

        Returns:
            创建的数据 ID
        """
        pass

    @abstractmethod
    def update(
        self, entity_name: str, entity_id: Any, data: Dict[str, Any]
    ) -> bool:
        """
        更新数据

        Args:
            entity_name: 实体名称
            entity_id: 要更新的数据 ID
            data: 要更新的字段（字段名 -> 值）

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    def delete(self, entity_name: str, entity_id: Any) -> bool:
        """
        删除数据

        Args:
            entity_name: 实体名称
            entity_id: 要删除的数据 ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def count(self, entity_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计符合条件的数据数量

        Args:
            entity_name: 实体名称
            filters: 过滤条件

        Returns:
            数据数量
        """
        pass


# 全局 Data API 实例（单例模式）
_data_api_instance: Optional[DataAPI] = None


def set_data_api(api: DataAPI) -> None:
    """
    设置全局 Data API 实例

    Args:
        api: DataAPI 实现实例
    """
    global _data_api_instance
    _data_api_instance = api


def get_data_api() -> DataAPI:
    """
    获取全局 Data API 实例

    Returns:
        DataAPI 实例

    Raises:
        RuntimeError: 如果尚未初始化 Data API
    """
    global _data_api_instance
    if _data_api_instance is None:
        raise RuntimeError("Data API 尚未初始化，请先调用 set_data_api()")
    return _data_api_instance
