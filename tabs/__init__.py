"""
Tabs Package - Tab 子程序目录

【注意】
此目录下的每个 .py 文件代表一个 Tab 页面
每个 Tab 必须：
1. 继承自 BaseTab
2. 定义 DISPLAY_NAME 类属性
3. 严格遵循构造函数 def __init__(self, parent=None)
4. 拆分为 UI 模块和功能模块

【红线规则】
- Tab 子程序不得 import 其他 Tab
- Tab 不得被其他 Tab import
- Tab 不得直接访问数据库
"""
