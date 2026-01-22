"""
应用程序入口

【设计原则】
1. 只负责初始化框架
2. 初始化 Data 层
3. 加载数据实体目录
4. 加载并管理 Tab 子程序
5. 不负责具体业务、逻辑、UI 细节
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import MainWindow
from core.data import DataAPI, set_data_api, EntityRegistry
from core.data.data_api_impl import SQLiteDataAPI


def main() -> None:
    """
    主程序入口

    初始化流程：
        1. 创建 QApplication
        2. 初始化 Data 层
        3. 加载数据实体目录
        4. 创建主窗口并加载 Tab
        5. 进入事件循环
    """
    # 创建应用
    app = QApplication(sys.argv)

    # ========================================
    # 1. 初始化 Data 层
    # ========================================
    # 创建 Data API 实现（当前使用 SQLite 实现）
    db_path = Path(__file__).parent / "data" / "app.db"
    data_api = SQLiteDataAPI(db_path=str(db_path))
    set_data_api(data_api)

    # ========================================
    # 2. 加载数据实体目录（供开发者参考）
    # ========================================
    entity_registry_path = Path(__file__).parent / "data" / "entity_registry.json"
    entity_registry = EntityRegistry(str(entity_registry_path))

    # 打印可用的实体（供调试）
    print("=== 数据实体目录已加载 ===")
    print(f"可用实体: {entity_registry.list_entity_names()}")
    print("===============================")

    # ========================================
    # 3. 创建主窗口并加载 Tab
    # ========================================
    tabs_dir = Path(__file__).parent / "tabs"

    window = MainWindow(
        title="个人桌面系统内核",
        tabs_directory=str(tabs_dir),
    )

    # ========================================
    # 4. 显示窗口并进入事件循环
    # ========================================
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
