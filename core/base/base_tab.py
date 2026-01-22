"""
BaseTab 基类 - 所有 Tab 页面的强制抽象基类

设计原则：
1. 仅作为 UI 层抽象，不包含业务逻辑
2. 不保存任何状态
3. 子类必须严格遵循构造函数签名：def __init__(self, parent=None)

【红线规则】
- Tab 子程序必须继承 BaseTab
- 主程序只加载并信任继承自 BaseTab 的类
"""

from typing import Optional

from PySide6.QtWidgets import QWidget


class BaseTab(QWidget):
    """
    所有 Tab 页面的抽象基类

    职责：
    - 定义 Tab 页面的通用接口
    - 强制约束子类的构造函数签名
    - 确保所有 Tab 有一致的 UI 结构

    不负责：
    - 业务逻辑
    - 数据访问
    - 状态管理
    """

    # 子类必须定义此属性，作为 Tab 在 QTabWidget 中的显示名称
    DISPLAY_NAME: str = "未命名"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        强制构造函数签名

        【红线规则】
        - 只接受 parent 参数
        - 禁止传入业务对象、数据库连接、配置参数等
        - Tab 在构造阶段不得获取任何外部资源

        Args:
            parent: 父组件（由 QTabWidget 传入）
        """
        super().__init__(parent)
        self._parent = parent

    @classmethod
    def get_display_name(cls) -> str:
        """
        获取 Tab 显示名称

        Returns:
            Tab 的显示名称
        """
        return cls.DISPLAY_NAME

    def setup_ui(self) -> None:
        """
        子类必须在此方法中构建 UI

        注意：子类应在 __init__ 结束时调用此方法
        """
        raise NotImplementedError("子类必须实现 setup_ui() 方法")

    def refresh(self) -> None:
        """
        可选的刷新方法

        当 Tab 被切换到前台时，框架可能调用此方法
        子类可覆盖此方法以实现数据刷新逻辑
        """
        pass

    def on_activate(self) -> None:
        """
        Tab 被激活时的回调

        可选实现，用于处理 Tab 获得焦点时的逻辑
        """
        pass

    def on_deactivate(self) -> None:
        """
        Tab 失去激活状态时的回调

        可选实现，用于清理临时资源等
        """
        pass
