"""
TabLoader - Tab 自动发现与加载器

【核心职责】
1. 扫描指定目录，自动发现并导入所有子目录中的 Tab
2. 每个子目录必须有 __init__.py 并导出 Tab 类
3. 实例化并返回 Tab 实例列表

【设计原则】
- 主程序只加载并信任继承自 BaseTab 的类
- Tab 的显示名称由 Tab 类自身定义
- 支持两种目录结构：
  1. 子目录结构：tabs/{feature}/__init__.py (推荐)
  2. 扁平结构：tabs/{feature}_tab.py (兼容旧方式)
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Type

from PySide6.QtWidgets import QWidget

from ..base.base_tab import BaseTab


class TabLoadError(Exception):
    """Tab 加载失败异常"""
    pass


class TabLoader:
    """
    Tab 自动加载器

    支持的目录结构：
    1. 子目录结构（推荐）：
       tabs/
       ├── task/
       │   ├── __init__.py  (导出 TaskTab)
       │   ├── task_tab.py
       │   └── task_logic.py
       └── note/
           ├── __init__.py  (导出 NoteTab)
           ...

    2. 扁平结构（兼容）：
       tabs/
       ├── task_tab.py  (包含 TaskTab)
       └── note_tab.py  (包含 NoteTab)

    使用示例：
        loader = TabLoader(tabs_directory="tabs/")
        tabs = loader.load_all()
    """

    def __init__(self, tabs_directory: str) -> None:
        """
        初始化 Tab 加载器

        Args:
            tabs_directory: Tab 文件所在目录
        """
        self._tabs_dir = Path(tabs_directory)
        self._loaded_tabs: List[BaseTab] = []
        self._load_errors: List[str] = []

    def load_all(self) -> List[BaseTab]:
        """
        加载所有 Tab

        Returns:
            实例化的 Tab 对象列表

        流程：
            1. 优先扫描子目录（加载 __init__.py 中导出的 Tab）
            2. 如果没有子目录，回退到扫描 .py 文件
            3. 在模块中查找 BaseTab 子类
            4. 实例化每个 Tab
        """
        self._loaded_tabs = []
        self._load_errors = []

        if not self._tabs_dir.exists():
            return []

        # 1. 优先扫描子目录（新的目录结构）
        subdirs = [d for d in self._tabs_dir.iterdir() if d.is_dir()]
        if subdirs:
            for subdir in sorted(subdirs):
                init_file = subdir / "__init__.py"
                if init_file.exists():
                    try:
                        tab_class = self._load_tab_from_init(subdir, init_file)
                        if tab_class:
                            tab_instance = self._instantiate_tab(tab_class)
                            if tab_instance:
                                self._loaded_tabs.append(tab_instance)
                    except Exception as e:
                        self._load_errors.append(f"{subdir.name}: {str(e)}")
            return self._loaded_tabs

        # 2. 回退到扫描 .py 文件（兼容旧的扁平结构）
        py_files = sorted(self._tabs_dir.glob("*.py"))

        for py_file in py_files:
            try:
                tab_class = self._load_tab_class(py_file)
                if tab_class:
                    tab_instance = self._instantiate_tab(tab_class)
                    if tab_instance:
                        self._loaded_tabs.append(tab_instance)
            except Exception as e:
                self._load_errors.append(f"{py_file.name}: {str(e)}")

        return self._loaded_tabs

    def _load_tab_from_init(
        self, subdir: Path, init_file: Path
    ) -> Optional[Type[BaseTab]]:
        """
        从子目录的 __init__.py 加载 Tab 类

        Args:
            subdir: 子目录路径
            init_file: __init__.py 文件路径

        Returns:
            找到的 BaseTab 子类，不存在则返回 None
        """
        module_name = f"tabs.{subdir.name}"

        # 防止重复导入
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if spec is None or spec.loader is None:
                raise TabLoadError(f"无法加载模块: {init_file.name}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        # 查找 BaseTab 子类
        tab_class = self._find_base_tab_subclass(module)

        return tab_class

    def _load_tab_class(self, py_file: Path) -> Optional[Type[BaseTab]]:
        """
        动态加载模块并查找 BaseTab 子类

        Args:
            py_file: .py 文件路径

        Returns:
            找到的 BaseTab 子类，不存在则返回 None
        """
        module_name = py_file.stem

        # 防止重复导入
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                raise TabLoadError(f"无法加载模块: {py_file.name}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        # 查找 BaseTab 子类
        tab_class = self._find_base_tab_subclass(module)

        return tab_class

    def _find_base_tab_subclass(self, module) -> Optional[Type[BaseTab]]:
        """
        在模块中查找 BaseTab 子类

        Args:
            module: 已加载的模块

        Returns:
            BaseTab 子类，不存在则返回 None
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseTab)
                and attr is not BaseTab
            ):
                return attr
        return None

    def _instantiate_tab(
        self, tab_class: Type[BaseTab]
    ) -> Optional[BaseTab]:
        """
        实例化 Tab 类

        Args:
            tab_class: BaseTab 子类

        Returns:
            Tab 实例，实例化失败返回 None
        """
        try:
            # 使用强制构造函数签名
            return tab_class(parent=None)
        except TypeError as e:
            raise TabLoadError(
                f"{tab_class.__name__} 构造函数必须为 def __init__(self, parent=None): {e}"
            )

    def get_load_errors(self) -> List[str]:
        """
        获取加载过程中的错误列表

        Returns:
            错误信息列表
        """
        return self._load_errors.copy()

    def get_tab_count(self) -> int:
        """
        获取成功加载的 Tab 数量

        Returns:
            Tab 数量
        """
        return len(self._loaded_tabs)
