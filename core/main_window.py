"""
MainWindow - 主窗口

【设计原则】
1. 只包含一个 QTabWidget
2. 主程序不直接定义任何 Tab 页面内容
3. 主程序只负责初始化框架、加载 Tab 子程序、管理生命周期

【职责边界】
- 初始化 UI 框架
- 加载并管理 Tab 子程序
- 不负责具体业务、逻辑、UI 细节
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Qt

from .base.base_tab import BaseTab
from .loader.tab_loader import TabLoader


class MainWindow(QMainWindow):
    """
    主窗口

    包含一个 QTabWidget，负责加载和管理所有 Tab
    """

    def __init__(
        self,
        title: str = "应用",
        tabs_directory: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化主窗口

        Args:
            title: 窗口标题
            tabs_directory: Tab 文件所在目录
            parent: 父组件
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(1024, 768)

        # 创建中央部件和 TabWidget
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)

        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(False)

        # Tab 切换信号连接
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # 布局
        layout = QWidget()
        from PySide6.QtWidgets import QVBoxLayout

        main_layout = QVBoxLayout(self._central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._tab_widget)

        # Tab 加载器
        self._tab_loader: Optional[TabLoader] = None
        self._tabs: List[BaseTab] = []

        # 加载 Tab（如果指定了目录）
        if tabs_directory:
            self.load_tabs(tabs_directory)

    def load_tabs(self, tabs_directory: str) -> int:
        """
        加载指定目录下的所有 Tab

        Args:
            tabs_directory: Tab 文件所在目录

        Returns:
            成功加载的 Tab 数量
        """
        self._tab_loader = TabLoader(tabs_directory)
        self._tabs = self._tab_loader.load_all()

        # 将 Tab 添加到 QTabWidget
        for tab in self._tabs:
            display_name = tab.get_display_name()
            self._tab_widget.addTab(tab, display_name)

        # 输出加载错误
        errors = self._tab_loader.get_load_errors()
        if errors:
            for error in errors:
                print(f"[TabLoadError] {error}")

        return self._tab_loader.get_tab_count()

    def get_tab_by_name(self, name: str) -> Optional[BaseTab]:
        """
        根据显示名称获取 Tab

        Args:
            name: Tab 显示名称

        Returns:
            对应的 Tab，不存在则返回 None
        """
        for tab in self._tabs:
            if tab.get_display_name() == name:
                return tab
        return None

    def get_current_tab(self) -> Optional[BaseTab]:
        """
        获取当前激活的 Tab

        Returns:
            当前 Tab，不存在则返回 None
        """
        current_index = self._tab_widget.currentIndex()
        if 0 <= current_index < len(self._tabs):
            return self._tabs[current_index]
        return None

    def _on_tab_changed(self, index: int) -> None:
        """
        Tab 切换回调

        Args:
            index: 新激活的 Tab 索引
        """
        if 0 <= index < len(self._tabs):
            tab = self._tabs[index]
            tab.on_activate()

            # 通知前一个 Tab 失去激活状态
            if hasattr(self, "_last_index") and 0 <= self._last_index < len(
                self._tabs
            ):
                self._tabs[self._last_index].on_deactivate()

            self._last_index = index
