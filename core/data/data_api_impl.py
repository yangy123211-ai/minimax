"""
SQLiteDataAPI - SQLite 实现

【核心设计原则】
1. 这是 Data API 的一种实现
2. 子程序不得直接使用此类
3. 子程序只能通过 get_data_api() 获取统一接口

【职责】
- 屏蔽 SQL 细节
- 管理数据库连接
- 负责数据一致性
- 自动表创建
"""

import json
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .data_api import DataAPI


class SQLiteDataAPI(DataAPI):
    """
    SQLite 实现的数据访问接口

    【表名生成规则】
    - 默认规则：EntityName -> snake_case + "s" (如 TaskEntity -> task_entities)
    - 特殊映射：可在 entity_registry.json 中指定 table_name 覆盖

    【注意】
    - 这是框架内部实现
    - 子程序只能通过 get_data_api() 获取 DataAPI 抽象接口
    """

    def __init__(self, db_path: str) -> None:
        """
        初始化 SQLite Data API

        Args:
            db_path: SQLite 数据库文件路径
        """
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._entity_registry: Optional[Dict] = None
        self._table_cache: Dict[str, str] = {}  # 实体名 -> 表名 缓存
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _load_entity_registry(self) -> Dict:
        """加载实体注册表"""
        if self._entity_registry is None:
            registry_path = self._db_path.parent / "entity_registry.json"
            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    self._entity_registry = json.load(f)
            else:
                self._entity_registry = {"entities": []}
        return self._entity_registry

    def _entity_to_table(self, entity_name: str) -> Optional[str]:
        """将实体名称映射到表名

        【映射规则】
        1. 先检查缓存
        2. 再查 entity_registry.json 中的 table_name 字段
        3. 最后自动生成：EntityName -> snake_case + "s"
        """
        # 1. 检查缓存
        if entity_name in self._table_cache:
            return self._table_cache[entity_name]

        # 2. 从 entity_registry.json 获取
        registry = self._load_entity_registry()
        table_name = None

        for entity in registry.get("entities", []):
            if entity.get("name") == entity_name:
                # 检查是否有显式指定的 table_name
                if "table_name" in entity:
                    table_name = entity["table_name"]
                break

        # 3. 自动生成（如果未指定）
        if table_name is None:
            table_name = self._generate_table_name(entity_name)

        # 缓存并返回
        self._table_cache[entity_name] = table_name
        return table_name

    def _generate_table_name(self, entity_name: str) -> str:
        """自动生成表名

        规则：EntityName -> snake_case + "s"
        例如：
        - TaskEntity -> task_entities
        - NoteEntity -> note_entities
        - TimerReminderEntity -> timer_reminders
        """
        # CamelCase -> snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', entity_name)
        snake = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # 特殊情况处理（保持向后兼容）
        special_cases = {
            "task_entities": "tasks",
            "note_entities": "notes",
            "timer_reminder_entities": "timer_reminders",
        }

        return special_cases.get(snake, snake + "s")

    def _ensure_table_exists(self, entity_name: str) -> None:
        """确保表存在，如果不存在则自动创建"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查表是否已存在
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if cursor.fetchone():
                conn.close()
                return

            # 从 entity_registry.json 获取字段定义
            registry = self._load_entity_registry()
            fields = []

            for entity in registry.get("entities", []):
                if entity.get("name") == entity_name:
                    fields = entity.get("fields", [])
                    break

            if not fields:
                conn.close()
                raise ValueError(f"实体 {entity_name} 未定义字段，请先在 entity_registry.json 中配置")

            # 构建建表 SQL
            columns = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

            for field in fields:
                field_name = field.get("name")
                field_type = field.get("type", "TEXT").upper()

                # 跳过 id 字段（已单独处理）
                if field_name == "id":
                    continue

                # 处理默认值
                default = field.get("default")
                if default is not None:
                    if isinstance(default, str):
                        default_sql = f"DEFAULT '{default}'"
                    else:
                        default_sql = f"DEFAULT {default}"
                elif field_type == "TEXT":
                    default_sql = "DEFAULT ''"
                else:
                    default_sql = ""

                columns.append(f"{field_name} {field_type} {default_sql}".strip())

            columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            create_sql = f"""
                CREATE TABLE {table_name} (
                    {', '.join(columns)}
                )
            """

            cursor.execute(create_sql)
            conn.commit()
            conn.close()

    def _init_database(self) -> None:
        """初始化数据库"""
        with self._lock:
            conn = self._get_connection()
            conn.close()
        # 不再预创建表，改为按需创建

    def query(
        self,
        entity_name: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """查询数据"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return []

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql = f"SELECT * FROM {table_name}"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                sql += " WHERE " + " AND ".join(conditions)

            if order_by:
                sql += f" ORDER BY {order_by}"

            if limit is not None:
                sql += f" LIMIT {limit}"
                if offset is not None:
                    sql += f" OFFSET {offset}"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

    def get(self, entity_name: str, entity_id: Any) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单条数据"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return None

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

    def create(self, entity_name: str, data: Dict[str, Any]) -> Any:
        """创建新数据"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            raise ValueError(f"未知实体: {entity_name}")

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            columns = list(data.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = list(data.values())

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(sql, values)

            new_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return new_id

    def update(
        self, entity_name: str, entity_id: Any, data: Dict[str, Any]
    ) -> bool:
        """更新数据"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return False

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            columns = list(data.keys())
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            values = list(data.values()) + [entity_id]

            sql = f"UPDATE {table_name} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(sql, values)

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            return affected > 0

    def delete(self, entity_name: str, entity_id: Any) -> bool:
        """删除数据"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return False

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (entity_id,))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            return affected > 0

    def count(self, entity_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计符合条件的数据数量"""
        table_name = self._entity_to_table(entity_name)
        if not table_name:
            return 0

        # 确保表存在
        self._ensure_table_exists(entity_name)

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql = f"SELECT COUNT(*) FROM {table_name}"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                sql += " WHERE " + " AND ".join(conditions)

            cursor.execute(sql, params)
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else 0
