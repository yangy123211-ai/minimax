# Tab 子程序开发规则

## 1. 项目架构概述

本项目是一个基于 PySide6 的桌面应用程序，采用 **UI/逻辑分离** 架构：

```
main.py (入口)
    ↓
MainWindow (主窗口)
    ↓
TabLoader (动态加载 tabs/ 目录下的子程序)
    ↓
每个 Tab: XxxTab (UI) + XxxLogic (业务逻辑)
    ↓
Data API (统一数据访问接口)
    ↓
SQLiteDataAPI (具体实现)
```

**核心设计原则**：
- Tab 子程序之间完全解耦，不得相互 import
- 不得直接访问数据库，必须通过 Data API
- UI 层只负责展示和收集输入，业务逻辑在 Logic 层
- 构造函数只接受 `parent` 参数，不传入任何业务对象

---

## 2. 目录结构规范

每个子程序放在独立目录中，包含以下文件：

```
tabs/
├── __init__.py
├── task/                      # 子程序目录
│   ├── __init__.py            # 必须导出 Tab 类
│   ├── task_tab.py            # UI 层文件
│   └── task_logic.py          # 业务逻辑层文件
├── note/
│   ├── __init__.py
│   ├── note_tab.py
│   └── note_logic.py
└── timer_reminder/
    ├── __init__.py
    ├── timer_reminder_tab.py
    └── timer_reminder_logic.py
```

**文件命名规则**：
- 子目录名：功能名使用小写字母，单词间用下划线分隔
- UI 文件：`{功能名}_tab.py`
- Logic 文件：`{功能名}_logic.py`
- `__init__.py` 必须导出 Tab 类

---

## 3. 必须遵循的类结构

### 3.1 UI 层 (XxxTab)

```python
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QGroupBox, QSplitter,
)
from PySide6.QtCore import Qt

from core.base import BaseTab
from .xxx_logic import XxxLogic  # 同目录下的 logic 模块


class XxxTab(BaseTab):
    """
    [功能名称] Tab 页面

    职责：
    - [职责描述1]
    - [职责描述2]
    """

    # Tab 在界面上显示的名称
    DISPLAY_NAME = "[显示名称]"

    def __init__(self, parent: QWidget = None) -> None:
        """强制构造函数签名：只接受 parent 参数"""
        super().__init__(parent)

        # 业务逻辑模块（延迟初始化，构造时不获取资源）
        self._logic: Optional[XxxLogic] = None

        # 构建 UI
        self.setup_ui()

    def _ensure_logic(self) -> XxxLogic:
        """确保业务逻辑模块已初始化（延迟初始化）"""
        if self._logic is None:
            self._logic = XxxLogic()
        return self._logic

    def setup_ui(self) -> None:
        """构建 UI（使用纯代码方式）"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== [区域1名称] =====
        group = QGroupBox("[区域标题]")
        layout = QVBoxLayout()

        # UI 组件创建...

        group.setLayout(layout)
        main_layout.addWidget(group)

        # 其他区域...

        #  spacer
        main_layout.addStretch()

    def on_activate(self) -> None:
        """Tab 被激活时刷新数据"""
        self._on_refresh()

    def _on_refresh(self) -> None:
        """刷新数据"""
        try:
            logic = self._ensure_logic()
            # 调用 logic 方法获取数据并更新 UI
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")

    # ===== 事件处理方法 =====
    def _on_action_name(self) -> None:
        """[动作名称]"""
        # 1. 收集用户输入
        # 2. 参数校验
        # 3. 调用 logic 执行操作
        # 4. 更新 UI 或提示结果
        pass
```

### 3.2 Logic 层 (XxxLogic)

```python
from typing import Any, Dict, List, Optional

from core.data import get_data_api


class XxxLogic:
    """
    [功能名称]业务逻辑模块

    职责：
    - [职责描述]
    """

    # 实体名称（对应 entity_registry.json 中的定义）
    ENTITY_NAME = "XxxEntity"

    def __init__(self) -> None:
        """通过框架获取 Data API"""
        self._data_api = get_data_api()

    # ===== 查询操作 =====
    def get_all_items(
        self, filter_param: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有数据

        Args:
            filter_param: 可选的过滤参数

        Returns:
            数据列表
        """
        filters = None
        if filter_param:
            filters = {"field_name": filter_param}

        return self._data_api.query(
            self.ENTITY_NAME,
            filters=filters,
            order_by="created_at DESC",
        )

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """获取指定数据"""
        return self._data_api.get(self.ENTITY_NAME, item_id)

    # ===== 写入操作 =====
    def create_item(self, field1: str, field2: str = "") -> int:
        """
        创建新数据

        Args:
            field1: 字段1说明
            field2: 字段2说明

        Returns:
            创建的数据 ID
        """
        # 业务规则校验
        if not field1 or not field1.strip():
            raise ValueError("字段1不能为空")

        data = {
            "field1": field1.strip(),
            "field2": field2.strip() if field2 else "",
        }

        return self._data_api.create(self.ENTITY_NAME, data)

    def update_item(
        self, item_id: int, field1: str, field2: str
    ) -> bool:
        """更新数据"""
        if not field1 or not field1.strip():
            raise ValueError("字段1不能为空")

        return self._data_api.update(
            self.ENTITY_NAME, item_id,
            {"field1": field1.strip(), "field2": field2.strip()}
        )

    def delete_item(self, item_id: int) -> bool:
        """删除数据"""
        return self._data_api.delete(self.ENTITY_NAME, item_id)
```

---

## 4. Data API 使用规范

### 4.1 可用的数据实体

必须在 `data/entity_registry.json` 中定义实体后才能使用。常见的实体：
- `TaskEntity` - 任务实体
- `NoteEntity` - 笔记实体

### 4.2 Data API 方法签名

```python
# 查询数据列表
data_api.query(
    entity_name: str,                           # 实体名称
    filters: Optional[Dict[str, Any]] = None,   # 过滤条件
    order_by: Optional[str] = None,             # 排序字段
    limit: Optional[int] = None,                # 限制数量
    offset: Optional[int] = None,               # 偏移量
) -> List[Dict[str, Any]]

# 获取单条数据
data_api.get(
    entity_name: str,
    entity_id: Any,
) -> Optional[Dict[str, Any]]

# 创建数据
data_api.create(
    entity_name: str,
    data: Dict[str, Any],                       # 字段名 -> 值
) -> Any  # 返回新创建的 ID

# 更新数据
data_api.update(
    entity_name: str,
    entity_id: Any,
    data: Dict[str, Any],                       # 要更新的字段
) -> bool

# 删除数据
data_api.delete(
    entity_name: str,
    entity_id: Any,
) -> bool

# 统计数量
data_api.count(
    entity_name: str,
    filters: Optional[Dict[str, Any]] = None,
) -> int
```

### 4.3 使用示例

```python
from core.data import get_data_api

data_api = get_data_api()

# 查询
tasks = data_api.query("TaskEntity", filters={"status": "pending"})
tasks = data_api.query("TaskEntity", order_by="priority DESC", limit=10)

# 创建
task_id = data_api.create("TaskEntity", {
    "title": "新任务",
    "description": "描述",
    "priority": 1,
    "status": "pending",
})

# 更新
success = data_api.update("TaskEntity", task_id, {"status": "completed"})

# 删除
success = data_api.delete("TaskEntity", task_id)
```

---

## 5. PySide6 常用组件

### 5.1 布局组件
| 组件 | 用途 |
|------|------|
| `QVBoxLayout` | 垂直布局 |
| `QHBoxLayout` | 水平布局 |
| `QGridLayout` | 网格布局 |
| `QSplitter` | 可分割的组件容器 |

### 5.2 输入组件
| 组件 | 用途 |
|------|------|
| `QLineEdit` | 单行文本输入 |
| `QTextEdit` | 多行文本编辑 |
| `QComboBox` | 下拉选择框 |
| `QSpinBox` | 数字微调框 |
| `QCheckBox` | 复选框 |

### 5.3 显示组件
| 组件 | 用途 |
|------|------|
| `QLabel` | 文本/图片显示 |
| `QListWidget` | 列表显示 |
| `QListWidgetItem` | 列表项 |
| `QGroupBox` | 带标题的分组框 |

### 5.4 按钮与对话框
| 组件 | 用途 |
|------|------|
| `QPushButton` | 按钮 |
| `QMessageBox` | 消息对话框 |
| `QMessageBox.question()` | 确认对话框 |

### 5.5 定时器
```python
from PySide6.QtCore import QTimer

timer = QTimer(self)
timer.setInterval(1000)  # 毫秒
timer.timeout.connect(self._on_timeout)
timer.start()
timer.stop()
```

---

## 6. UI 开发模式

### 6.1 列表选择模式
```python
self._list_widget = QListWidget()
self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

# 获取选中的数据 ID
item = self._list_widget.currentItem()
if item:
    item_id = item.data(Qt.ItemDataRole.UserRole)

# 遍历列表
for i in range(self._list_widget.count()):
    item = self._list_widget.item(i)
```

### 6.2 左右分栏模式
```python
left_widget = QWidget()
left_layout = QVBoxLayout(left_widget)

right_widget = QWidget()
right_layout = QVBoxLayout(right_widget)

splitter = QSplitter(Qt.Orientation.Horizontal)
splitter.addWidget(left_widget)
splitter.addWidget(right_widget)
splitter.setSizes([300, 500])  # 初始宽度比例

main_layout.addWidget(splitter)
```

### 6.3 对话框确认模式
```python
reply = QMessageBox.question(
    self,
    "确认",
    "确定要删除吗？",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
)

if reply == QMessageBox.StandardButton.Yes:
    # 执行删除
    pass
```

---

## 7. 开发流程

### 步骤 1：确定功能需求
1. 明确 Tab 的显示名称
2. 确定数据实体（新建或复用）
3. 定义需要的操作（CRUD）

### 步骤 2：创建子程序目录结构
```bash
# 在 tabs/ 目录下创建子程序目录
mkdir -p tabs/new_feature
touch tabs/new_feature/__init__.py
touch tabs/new_feature/new_feature_tab.py
touch tabs/new_feature/new_feature_logic.py
```

### 步骤 3：创建 __init__.py
```python
# tabs/new_feature/__init__.py
from .new_feature_tab import NewFeatureTab

__all__ = ["NewFeatureTab"]
```

### 步骤 4：创建 Logic 文件
```python
# tabs/new_feature/new_feature_logic.py
from typing import Any, Dict, List, Optional
from core.data import get_data_api

class NewFeatureLogic:
    ENTITY_NAME = "NewFeatureEntity"  # 或复用现有实体

    def __init__(self) -> None:
        self._data_api = get_data_api()

    def get_all_items(self) -> List[Dict[str, Any]]:
        return self._data_api.query(self.ENTITY_NAME, order_by="created_at DESC")

    def create_item(self, name: str, description: str = "") -> int:
        # 业务校验
        if not name or not name.strip():
            raise ValueError("名称不能为空")
        # 创建数据
        return self._data_api.create(self.ENTITY_NAME, {
            "name": name.strip(),
            "description": description.strip(),
        })

    # ... 其他方法
```

### 步骤 5：创建 Tab 文件
```python
# tabs/new_feature/new_feature_tab.py
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt

from core.base import BaseTab
from .new_feature_logic import NewFeatureLogic


class NewFeatureTab(BaseTab):
    DISPLAY_NAME = "新功能"

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._logic = None
        self.setup_ui()

    def _ensure_logic(self) -> NewFeatureLogic:
        if self._logic is None:
            self._logic = NewFeatureLogic()
        return self._logic

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 构建 UI 组件...
        main_layout.addStretch()

    def on_activate(self) -> None:
        self._on_refresh()

    def _on_refresh(self) -> None:
        # 刷新数据
        pass

    def _on_add(self) -> None:
        # 添加操作
        pass
```

### 步骤 6：测试运行
```bash
cd /home/hello/Yolov8/MHTools/project_minimax
python main.py
```

---

## 8. 常见实体定义格式

如果需要新建实体，在 `data/entity_registry.json` 中添加：

```json
{
  "name": "ItemEntity",
  "description": "物品实体",
  "table_name": "items",
  "fields": [
    {"name": "id", "type": "integer", "readable": true, "writable": false},
    {"name": "name", "type": "string", "readable": true, "writable": true, "required": true},
    {"name": "description", "type": "string", "readable": true, "writable": true, "required": false},
    {"name": "category", "type": "string", "readable": true, "writable": true, "required": false},
    {"name": "created_at", "type": "timestamp", "readable": true, "writable": false},
    {"name": "updated_at", "type": "timestamp", "readable": true, "writable": false}
  ],
  "operations": ["read", "write", "update", "delete"]
}
```

### 8.1 表名自动生成规则

框架会自动根据实体名称生成表名：
- 默认规则：`EntityName -> snake_case + "s"`
  - `TaskEntity` → `tasks`
  - `NoteEntity` → `notes`
  - `ItemEntity` → `items`
  - `TimerReminderEntity` → `timer_reminders`

- 如需自定义表名，在实体中添加 `table_name` 字段覆盖默认值

### 8.2 字段类型映射

| JSON type | SQL type |
|-----------|----------|
| `integer` | INTEGER |
| `string` | TEXT |
| `boolean` | INTEGER |
| `timestamp` | TIMESTAMP |

### 8.3 字段属性

| 属性 | 说明 |
|------|------|
| `name` | 字段名 |
| `type` | 数据类型 |
| `description` | 字段描述 |
| `readable` | 是否可读 |
| `writable` | 是否可写 |
| `required` | 是否必填 |
| `default` | 默认值 |

---

## 9. 错误处理规范

```python
def _on_action(self) -> None:
    """处理动作的通用模式"""
    try:
        # 1. 获取输入
        input_value = self._input_widget.text().strip()

        # 2. 参数校验
        if not input_value:
            QMessageBox.warning(self, "警告", "请输入xxx")
            return

        # 3. 调用 Logic
        logic = self._ensure_logic()
        logic.do_something(input_value)

        # 4. 成功后更新 UI
        self._on_refresh()

    except ValueError as e:
        # 业务逻辑错误
        QMessageBox.warning(self, "警告", str(e))
    except Exception as e:
        # 系统错误
        QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
```

---

## 10. 样式设置

### 内联样式示例
```python
self._label.setStyleSheet("""
    QLabel {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
""")
```

### 常用颜色值
- 绿色（成功）: `#4CAF50`
- 蓝色（信息）: `#2196F3`
- 橙色（警告）: `#FF9800`
- 红色（错误）: `#F44336`
- 灰色（禁用）: `#888888`

---

## 11. 禁止事项（红线规则）

1. **禁止**直接 import 其他 Tab 文件
2. **禁止**被其他 Tab import
3. **禁止**直接访问数据库（SQLite 等）
4. **禁止**在构造函数中获取外部资源
5. **禁止**修改构造函数签名（只接受 parent 参数）
