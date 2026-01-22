"""
TimerReminderTab - 时间触发提醒 Tab 页面

【设计原则】
1. 只负责界面展示
2. 收集用户操作
3. 不包含业务计算
4. 不直接访问 Data API

【UI/功能分离】
- UI 模块：TimerReminderTab（此文件）
- 功能模块：timer_reminder_logic.py（业务逻辑）
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QGridLayout,
    QSpinBox,
)
from PySide6.QtCore import Qt, QTimer, Signal

from core.base import BaseTab
from .timer_reminder_logic import TimerReminderLogic, TimeRule


class TimerReminderTab(BaseTab):
    """
    时间触发提醒 Tab 页面

    职责：
    - 展示当前时间和功能状态
    - 提供启停控制
    - 配置和确认时间规则
    - 显示下一次触发时间
    """

    # Tab 显示名称
    DISPLAY_NAME = "定时提醒"

    # 自定义信号：触发提醒
    trigger_reminder = Signal()

    def __init__(self, parent: QWidget = None) -> None:
        """
        强制构造函数签名
        """
        super().__init__(parent)

        # 业务逻辑模块（延迟初始化）
        self._logic: Optional[TimerReminderLogic] = None

        # 时间更新定时器
        self._time_timer: Optional[QTimer] = None

        # 触发检测定时器
        self._check_timer: Optional[QTimer] = None

        # 构建 UI
        self.setup_ui()
        self._setup_timers()

    def _ensure_logic(self) -> TimerReminderLogic:
        """确保业务逻辑模块已初始化"""
        if self._logic is None:
            self._logic = TimerReminderLogic()
        return self._logic

    def _setup_timers(self) -> None:
        """设置定时器"""
        # 时间显示更新定时器（每秒更新）
        self._time_timer = QTimer(self)
        self._time_timer.setInterval(1000)
        self._time_timer.timeout.connect(self._on_update_time)

        # 触发条件检测定时器（每100毫秒检测一次，更及时）
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(100)
        self._check_timer.timeout.connect(self._on_check_trigger)

    def setup_ui(self) -> None:
        """构建 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== 当前时间显示 =====
        time_group = QGroupBox("当前时间")
        time_layout = QVBoxLayout()

        self._current_time_label = QLabel("00:00:00")
        self._current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_time_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                font-family: monospace;
            }
        """)
        time_layout.addWidget(self._current_time_label)

        time_group.setLayout(time_layout)
        main_layout.addWidget(time_group)

        # ===== 功能状态 =====
        status_group = QGroupBox("功能状态")
        status_layout = QHBoxLayout()

        self._status_label = QLabel("已停止")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #888888;
            }
        """)
        self._status_label.setMinimumHeight(40)
        status_layout.addWidget(self._status_label)

        # 启动/停止按钮
        self._toggle_btn = QPushButton("启动")
        self._toggle_btn.setMinimumWidth(100)
        self._toggle_btn.setMinimumHeight(40)
        self._toggle_btn.clicked.connect(self._on_toggle)
        status_layout.addWidget(self._toggle_btn)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # ===== 规则配置 =====
        config_group = QGroupBox("触发规则配置")
        config_layout = QGridLayout()

        # 分钟周期
        config_layout.addWidget(QLabel("分钟周期:"), 0, 0)
        self._cycle_spin = QSpinBox()
        self._cycle_spin.setRange(1, 1440)
        self._cycle_spin.setValue(1)
        self._cycle_spin.valueChanged.connect(self._on_rule_input_changed)
        config_layout.addWidget(self._cycle_spin, 0, 1)

        # 分钟余数
        config_layout.addWidget(QLabel("分钟余数:"), 1, 0)
        self._remainder_spin = QSpinBox()
        self._remainder_spin.setRange(0, 1439)
        self._remainder_spin.setValue(0)
        self._remainder_spin.valueChanged.connect(self._on_rule_input_changed)
        config_layout.addWidget(self._remainder_spin, 1, 1)

        # 秒数
        config_layout.addWidget(QLabel("触发秒数:"), 2, 0)
        self._second_spin = QSpinBox()
        self._second_spin.setRange(0, 59)
        self._second_spin.setValue(0)
        self._second_spin.valueChanged.connect(self._on_rule_input_changed)
        config_layout.addWidget(self._second_spin, 2, 1)

        # 规则说明
        rule_desc = "触发条件：\n分钟 % 周期 = 余数 且 秒 = 指定值"
        config_layout.addWidget(QLabel(rule_desc), 3, 0, 1, 2)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # ===== 规则确认 =====
        confirm_layout = QHBoxLayout()

        self._confirm_btn = QPushButton("确认设置")
        self._confirm_btn.clicked.connect(self._on_confirm_rule)
        confirm_layout.addWidget(self._confirm_btn)

        self._cancel_btn = QPushButton("取消待确认")
        self._cancel_btn.clicked.connect(self._on_cancel_pending)
        confirm_layout.addWidget(self._cancel_btn)

        main_layout.addLayout(confirm_layout)

        # ===== 规则状态显示 =====
        rule_status_group = QGroupBox("规则状态")
        rule_status_layout = QVBoxLayout()

        self._active_rule_label = QLabel("当前规则: 未配置")
        self._active_rule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rule_status_layout.addWidget(self._active_rule_label)

        self._pending_rule_label = QLabel("待确认规则: 无")
        self._pending_rule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pending_rule_label.setStyleSheet("color: #888888;")
        rule_status_layout.addWidget(self._pending_rule_label)

        rule_status_group.setLayout(rule_status_layout)
        main_layout.addWidget(rule_status_group)

        # ===== 下次触发时间 =====
        next_group = QGroupBox("下次触发")
        next_layout = QVBoxLayout()

        self._next_trigger_label = QLabel("未配置规则")
        self._next_trigger_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next_trigger_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2196F3;
            }
        """)
        next_layout.addWidget(self._next_trigger_label)

        next_group.setLayout(next_layout)
        main_layout.addWidget(next_group)

        #  spacer
        main_layout.addStretch()

    def on_activate(self) -> None:
        """Tab 被激活时启动定时器"""
        # 从数据库加载规则和状态
        logic = self._ensure_logic()
        logic.load_from_db()

        # 同步输入框与加载的规则
        self._sync_inputs_with_rule()

        self._on_update_time()  # 立即更新一次时间显示
        if self._time_timer:
            self._time_timer.start()
        if self._check_timer:
            self._check_timer.start()

        self._update_display()

        # 如果之前正在运行，继续运行
        logic = self._ensure_logic()
        if logic.is_running and self._check_timer:
            self._check_timer.start()

    def _sync_inputs_with_rule(self) -> None:
        """同步输入框与已激活的规则"""
        logic = self._ensure_logic()
        if logic.has_active_rule:
            rule = logic.get_active_rule()
            self._cycle_spin.setValue(rule.minute_cycle)
            self._remainder_spin.setValue(rule.minute_remainder)
            self._second_spin.setValue(rule.second)

    def on_deactivate(self) -> None:
        """Tab 失去激活状态时暂停定时器"""
        if self._time_timer:
            self._time_timer.stop()
        if self._check_timer:
            self._check_timer.stop()

    def _on_update_time(self) -> None:
        """更新时间显示"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        self._current_time_label.setText(f"{date_str}\n{time_str}")

    def _on_check_trigger(self) -> None:
        """检测触发条件"""
        logic = self._ensure_logic()
        if logic.check_trigger():
            self._show_reminder()

    def _show_reminder(self) -> None:
        """显示提醒弹窗"""
        # 停止定时器避免重复触发
        if self._check_timer:
            self._check_timer.stop()

        # 显示不可忽略的对话框
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("提醒！")
        msg_box.setText("时间触发提醒！")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        # 设置为应用模态，阻止其他操作
        msg_box.setModal(True)
        msg_box.exec_()

        # 重新启动检测定时器
        if self._check_timer:
            self._check_timer.start()

        # 更新显示
        self._update_display()

    def _on_toggle(self) -> None:
        """切换启停状态"""
        logic = self._ensure_logic()

        if logic.is_running:
            logic.stop()
            self._update_status_display()
        else:
            if logic.start():
                self._update_status_display()
            else:
                QMessageBox.warning(
                    self,
                    "无法启动",
                    "请先配置并确认触发规则！"
                )

    def _on_rule_input_changed(self) -> None:
        """规则输入变化时的提示"""
        # 用户修改输入时，显示待确认状态
        self._pending_rule_label.setText(
            f"待确认规则: {self._get_input_rule_str()} (未应用)"
        )
        self._pending_rule_label.setStyleSheet("color: #FF9800;")

    def _get_input_rule_str(self) -> str:
        """获取当前输入框中的规则字符串"""
        cycle = self._cycle_spin.value()
        remainder = self._remainder_spin.value()
        second = self._second_spin.value()
        return f"周期={cycle}, 余数={remainder}, 秒={second}"

    def _on_confirm_rule(self) -> None:
        """确认规则"""
        logic = self._ensure_logic()

        # 创建规则
        rule = TimeRule(
            minute_cycle=self._cycle_spin.value(),
            minute_remainder=self._remainder_spin.value(),
            second=self._second_spin.value(),
        )

        # 设置待确认规则
        logic.set_pending_rule(rule)

        # 确认生效
        if logic.confirm_rule():
            self._update_display()
            QMessageBox.information(
                self,
                "规则已生效",
                f"触发规则已更新：\n{self._get_input_rule_str()}"
            )
        else:
            QMessageBox.warning(self, "确认失败", "无法确认规则")

    def _on_cancel_pending(self) -> None:
        """取消待确认的规则"""
        logic = self._ensure_logic()
        logic.cancel_pending_rule()
        self._update_display()

    def _update_display(self) -> None:
        """更新所有显示"""
        self._update_status_display()
        self._update_rule_display()
        self._update_next_trigger_display()

    def _update_status_display(self) -> None:
        """更新状态显示"""
        logic = self._ensure_logic()

        if logic.is_running:
            self._status_label.setText("运行中")
            self._status_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #4CAF50;
                }
            """)
            self._toggle_btn.setText("停止")
        else:
            self._status_label.setText("已暂停")
            self._status_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #888888;
                }
            """)
            self._toggle_btn.setText("启动")

    def _update_rule_display(self) -> None:
        """更新规则状态显示"""
        logic = self._ensure_logic()

        if logic.has_active_rule:
            rule = logic.get_active_rule()
            rule_str = f"周期={rule.minute_cycle}, 余数={rule.minute_remainder}, 秒={rule.second}"
            self._active_rule_label.setText(f"当前规则: {rule_str}")
            self._active_rule_label.setStyleSheet("color: #4CAF50;")
        else:
            self._active_rule_label.setText("当前规则: 未配置")
            self._active_rule_label.setStyleSheet("color: #888888;")

        if logic.has_pending_rule:
            pending = logic.get_pending_rule()
            pending_str = f"周期={pending.minute_cycle}, 余数={pending.minute_remainder}, 秒={pending.second}"
            self._pending_rule_label.setText(f"待确认规则: {pending_str}")
            self._pending_rule_label.setStyleSheet("color: #FF9800;")
        else:
            self._pending_rule_label.setText("待确认规则: 无")
            self._pending_rule_label.setStyleSheet("color: #888888;")

    def _update_next_trigger_display(self) -> None:
        """更新下次触发时间显示"""
        logic = self._ensure_logic()

        if logic.has_active_rule:
            display = logic.get_next_trigger_display()
            self._next_trigger_label.setText(display)

            # 计算距离下次触发还有多久
            next_time = logic.get_next_trigger_time()
            if next_time:
                now = datetime.now()
                delta = (next_time - now).total_seconds()

                if delta < 10:
                    # 即将触发，橙色
                    self._next_trigger_label.setStyleSheet("""
                        QLabel {
                            font-size: 20px;
                            font-weight: bold;
                            color: #FF9800;
                        }
                    """)
                elif delta < 60:
                    # 1分钟内，蓝色
                    self._next_trigger_label.setStyleSheet("""
                        QLabel {
                            font-size: 20px;
                            font-weight: bold;
                            color: #2196F3;
                        }
                    """)
                else:
                    # 正常状态
                    self._next_trigger_label.setStyleSheet("""
                        QLabel {
                            font-size: 20px;
                            font-weight: bold;
                            color: #4CAF50;
                        }
                    """)
        else:
            self._next_trigger_label.setText("未配置规则")
            self._next_trigger_label.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: #888888;
                }
            """)
