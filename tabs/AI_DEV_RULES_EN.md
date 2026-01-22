# Tab Subprogram Development Rules

## 1. Project Architecture Overview

This is a PySide6-based desktop application with a **UI/Logic Separation** architecture:

```
main.py (entry point)
    ↓
MainWindow (main window)
    ↓
TabLoader (dynamically loads subprograms from tabs/ directory)
    ↓
Each Tab: XxxTab (UI) + XxxLogic (business logic)
    ↓
Data API (unified data access interface)
    ↓
SQLiteDataAPI (concrete implementation)
```

**Core Design Principles**:
- Tab subprograms are completely decoupled and must NOT import each other
- Must NOT directly access database, must use Data API
- UI layer is only responsible for display and input collection, business logic in Logic layer
- Constructor only accepts `parent` parameter, no business objects allowed

---

## 2. Directory Structure

Each subprogram is placed in a separate directory:

```
tabs/
├── __init__.py
├── task/                      # Subprogram directory
│   ├── __init__.py            # Must export Tab class
│   ├── task_tab.py            # UI layer file
│   └── task_logic.py          # Business logic layer file
├── note/
│   ├── __init__.py
│   ├── note_tab.py
│   └── note_logic.py
└── timer_reminder/
    ├── __init__.py
    ├── timer_reminder_tab.py
    └── timer_reminder_logic.py
```

**File Naming Rules**:
- Subdirectory name: feature name in lowercase with underscores
- UI file: `{feature_name}_tab.py`
- Logic file: `{feature_name}_logic.py`
- `__init__.py` must export Tab class

---

## 3. Required Class Structure

### 3.1 UI Layer (XxxTab)

```python
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QGroupBox, QSplitter,
)
from PySide6.QtCore import Qt

from core.base import BaseTab
from .xxx_logic import XxxLogic  # Same directory import


class XxxTab(BaseTab):
    """
    [Feature Name] Tab Page

    Responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    """

    # Tab display name in the interface
    DISPLAY_NAME = "[Display Name]"

    def __init__(self, parent: QWidget = None) -> None:
        """Enforced constructor signature: only accepts parent parameter"""
        super().__init__(parent)

        # Business logic module (lazy initialization, no resource access in constructor)
        self._logic: Optional[XxxLogic] = None

        # Build UI
        self.setup_ui()

    def _ensure_logic(self) -> XxxLogic:
        """Ensure business logic module is initialized (lazy initialization)"""
        if self._logic is None:
            self._logic = XxxLogic()
        return self._logic

    def setup_ui(self) -> None:
        """Build UI (using pure code)"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== [Section 1 Name] =====
        group = QGroupBox("[Section Title]")
        layout = QVBoxLayout()

        # UI component creation...

        group.setLayout(layout)
        main_layout.addWidget(group)

        # Other sections...

        # Spacer
        main_layout.addStretch()

    def on_activate(self) -> None:
        """Refresh data when Tab is activated"""
        self._on_refresh()

    def _on_refresh(self) -> None:
        """Refresh data"""
        try:
            logic = self._ensure_logic()
            # Call logic methods to get data and update UI
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {str(e)}")

    # ===== Event Handler Methods =====
    def _on_action_name(self) -> None:
        """[Action Name]"""
        # 1. Collect user input
        # 2. Validate parameters
        # 3. Call logic to execute operation
        # 4. Update UI or show result
        pass
```

### 3.2 Logic Layer (XxxLogic)

```python
from typing import Any, Dict, List, Optional

from core.data import get_data_api


class XxxLogic:
    """
    [Feature Name] Business Logic Module

    Responsibilities:
    - [Responsibility]
    """

    # Entity name (corresponds to definition in entity_registry.json)
    ENTITY_NAME = "XxxEntity"

    def __init__(self) -> None:
        """Obtain Data API through framework"""
        self._data_api = get_data_api()

    # ===== Query Operations =====
    def get_all_items(
        self, filter_param: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all items

        Args:
            filter_param: Optional filter parameter

        Returns:
            List of items
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
        """Get specific item"""
        return self._data_api.get(self.ENTITY_NAME, item_id)

    # ===== Write Operations =====
    def create_item(self, field1: str, field2: str = "") -> int:
        """
        Create new item

        Args:
            field1: Field 1 description
            field2: Field 2 description

        Returns:
            Created item ID
        """
        # Business rule validation
        if not field1 or not field1.strip():
            raise ValueError("Field1 cannot be empty")

        data = {
            "field1": field1.strip(),
            "field2": field2.strip() if field2 else "",
        }

        return self._data_api.create(self.ENTITY_NAME, data)

    def update_item(
        self, item_id: int, field1: str, field2: str
    ) -> bool:
        """Update item"""
        if not field1 or not field1.strip():
            raise ValueError("Field1 cannot be empty")

        return self._data_api.update(
            self.ENTITY_NAME, item_id,
            {"field1": field1.strip(), "field2": field2.strip()}
        )

    def delete_item(self, item_id: int) -> bool:
        """Delete item"""
        return self._data_api.delete(self.ENTITY_NAME, item_id)
```

---

## 4. Data API Usage

### 4.1 Available Data Entities

Entities must be defined in `data/entity_registry.json` before use. Common entities:
- `TaskEntity` - Task entity
- `NoteEntity` - Note entity

### 4.2 Data API Method Signatures

```python
# Query list of data
data_api.query(
    entity_name: str,                           # Entity name
    filters: Optional[Dict[str, Any]] = None,   # Filter conditions
    order_by: Optional[str] = None,             # Sort field
    limit: Optional[int] = None,                # Max results
    offset: Optional[int] = None,               # Offset
) -> List[Dict[str, Any]]

# Get single data by ID
data_api.get(
    entity_name: str,
    entity_id: Any,
) -> Optional[Dict[str, Any]]

# Create data
data_api.create(
    entity_name: str,
    data: Dict[str, Any],                       # Field name -> value
) -> Any  # Returns new created ID

# Update data
data_api.update(
    entity_name: str,
    entity_id: Any,
    data: Dict[str, Any],                       # Fields to update
) -> bool

# Delete data
data_api.delete(
    entity_name: str,
    entity_id: Any,
) -> bool

# Count data
data_api.count(
    entity_name: str,
    filters: Optional[Dict[str, Any]] = None,
) -> int
```

### 4.3 Usage Examples

```python
from core.data import get_data_api

data_api = get_data_api()

# Query
tasks = data_api.query("TaskEntity", filters={"status": "pending"})
tasks = data_api.query("TaskEntity", order_by="priority DESC", limit=10)

# Create
task_id = data_api.create("TaskEntity", {
    "title": "New Task",
    "description": "Description",
    "priority": 1,
    "status": "pending",
})

# Update
success = data_api.update("TaskEntity", task_id, {"status": "completed"})

# Delete
success = data_api.delete("TaskEntity", task_id)
```

---

## 5. PySide6 Common Components

### 5.1 Layout Components
| Component | Purpose |
|-----------|---------|
| `QVBoxLayout` | Vertical layout |
| `QHBoxLayout` | Horizontal layout |
| `QGridLayout` | Grid layout |
| `QSplitter` | Splittable container |

### 5.2 Input Components
| Component | Purpose |
|-----------|---------|
| `QLineEdit` | Single-line text input |
| `QTextEdit` | Multi-line text editor |
| `QComboBox` | Dropdown selection |
| `QSpinBox` | Number spinner |
| `QCheckBox` | Checkbox |

### 5.3 Display Components
| Component | Purpose |
|-----------|---------|
| `QLabel` | Text/image display |
| `QListWidget` | List display |
| `QListWidgetItem` | List item |
| `QGroupBox` | Group box with title |

### 5.4 Buttons and Dialogs
| Component | Purpose |
|-----------|---------|
| `QPushButton` | Button |
| `QMessageBox` | Message dialog |
| `QMessageBox.question()` | Confirmation dialog |

### 5.5 Timer
```python
from PySide6.QtCore import QTimer

timer = QTimer(self)
timer.setInterval(1000)  # milliseconds
timer.timeout.connect(self._on_timeout)
timer.start()
timer.stop()
```

---

## 6. UI Development Patterns

### 6.1 List Selection Pattern
```python
self._list_widget = QListWidget()
self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

# Get selected item ID
item = self._list_widget.currentItem()
if item:
    item_id = item.data(Qt.ItemDataRole.UserRole)

# Iterate through list
for i in range(self._list_widget.count()):
    item = self._list_widget.item(i)
```

### 6.2 Left-Right Split Pattern
```python
left_widget = QWidget()
left_layout = QVBoxLayout(left_widget)

right_widget = QWidget()
right_layout = QVBoxLayout(right_widget)

splitter = QSplitter(Qt.Orientation.Horizontal)
splitter.addWidget(left_widget)
splitter.addWidget(right_widget)
splitter.setSizes([300, 500])  # Initial width ratio

main_layout.addWidget(splitter)
```

### 6.3 Dialog Confirmation Pattern
```python
reply = QMessageBox.question(
    self,
    "Confirm",
    "Are you sure you want to delete?",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
)

if reply == QMessageBox.StandardButton.Yes:
    # Execute deletion
    pass
```

---

## 7. Development Process

### Step 1: Define Requirements
1. Determine Tab display name
2. Decide on data entity (create new or reuse)
3. Define required operations (CRUD)

### Step 2: Create Subprogram Directory Structure
```bash
# Create subprogram directory under tabs/
mkdir -p tabs/new_feature
touch tabs/new_feature/__init__.py
touch tabs/new_feature/new_feature_tab.py
touch tabs/new_feature/new_feature_logic.py
```

### Step 3: Create __init__.py
```python
# tabs/new_feature/__init__.py
from .new_feature_tab import NewFeatureTab

__all__ = ["NewFeatureTab"]
```

### Step 4: Create Logic File
```python
# tabs/new_feature/new_feature_logic.py
from typing import Any, Dict, List, Optional
from core.data import get_data_api

class NewFeatureLogic:
    ENTITY_NAME = "NewFeatureEntity"  # Or reuse existing entity

    def __init__(self) -> None:
        self._data_api = get_data_api()

    def get_all_items(self) -> List[Dict[str, Any]]:
        return self._data_api.query(self.ENTITY_NAME, order_by="created_at DESC")

    def create_item(self, name: str, description: str = "") -> int:
        # Business validation
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        # Create data
        return self._data_api.create(self.ENTITY_NAME, {
            "name": name.strip(),
            "description": description.strip(),
        })

    # ... Other methods
```

### Step 5: Create Tab File
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
from .new_feature_logic import NewFeatureLogic  # Same directory import


class NewFeatureTab(BaseTab):
    DISPLAY_NAME = "New Feature"

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

        # Build UI components...
        main_layout.addStretch()

    def on_activate(self) -> None:
        self._on_refresh()

    def _on_refresh(self) -> None:
        # Refresh data
        pass

    def _on_add(self) -> None:
        # Add operation
        pass
```

### Step 6: Test Run
```bash
cd /home/hello/Yolov8/MHTools/project_minimax
python main.py
```

---

## 8. Entity Definition Format

If a new entity is needed, add to `data/entity_registry.json`:

```json
{
  "name": "ItemEntity",
  "description": "Item entity",
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

### 8.1 Automatic Table Name Generation

The framework automatically generates table names from entity names:
- Default rule: `EntityName -> snake_case + "s"`
  - `TaskEntity` → `tasks`
  - `NoteEntity` → `notes`
  - `ItemEntity` → `items`
  - `TimerReminderEntity` → `timer_reminders`

- To customize table name, add `table_name` field to override default

### 8.2 Field Type Mapping

| JSON type | SQL type |
|-----------|----------|
| `integer` | INTEGER |
| `string` | TEXT |
| `boolean` | INTEGER |
| `timestamp` | TIMESTAMP |

### 8.3 Field Properties

| Property | Description |
|----------|-------------|
| `name` | Field name |
| `type` | Data type |
| `description` | Field description |
| `readable` | Whether readable |
| `writable` | Whether writable |
| `required` | Whether required |
| `default` | Default value |

---

## 9. Error Handling Pattern

```python
def _on_action(self) -> None:
    """Generic pattern for action handling"""
    try:
        # 1. Get input
        input_value = self._input_widget.text().strip()

        # 2. Validate parameters
        if not input_value:
            QMessageBox.warning(self, "Warning", "Please enter xxx")
            return

        # 3. Call Logic
        logic = self._ensure_logic()
        logic.do_something(input_value)

        # 4. Update UI on success
        self._on_refresh()

    except ValueError as e:
        # Business logic error
        QMessageBox.warning(self, "Warning", str(e))
    except Exception as e:
        # System error
        QMessageBox.critical(self, "Error", f"Operation failed: {str(e)}")
```

---

## 10. Styling

### Inline Style Example
```python
self._label.setStyleSheet("""
    QLabel {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
""")
```

### Common Color Values
- Green (success): `#4CAF50`
- Blue (info): `#2196F3`
- Orange (warning): `#FF9800`
- Red (error): `#F44336`
- Gray (disabled): `#888888`

---

## 11. Prohibited Actions (Red Lines)

1. **NEVER** directly import other Tab files
2. **NEVER** allow other Tabs to import this Tab
3. **NEVER** directly access database (SQLite, etc.)
4. **NEVER** access external resources in constructor
5. **NEVER** modify constructor signature (only accepts parent parameter)
