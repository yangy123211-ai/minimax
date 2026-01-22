"""
TimerReminderLogic - 时间触发提醒功能模块

【设计原则】
1. 只负责业务逻辑计算
2. 不包含 UI 代码
3. 通过 Data API 访问数据库
4. 提供状态查询和操作接口

【功能特性】
- 时间触发规则管理
- 规则确认/生效机制
- 触发时间预测
- 数据库持久化
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from core.data import get_data_api


@dataclass
class TimeRule:
    """
    时间触发规则

    触发条件：
        当前分钟 % 分钟周期 == 分钟余数
        且 当前秒数 == 指定秒数
    """
    minute_cycle: int = 1      # 分钟周期（取模用）
    minute_remainder: int = 0  # 分钟余数
    second: int = 0            # 触发秒数

    def __post_init__(self) -> None:
        """验证和规范化参数"""
        # 确保值在合理范围内
        self.minute_cycle = max(1, self.minute_cycle)
        self.minute_remainder = max(0, self.minute_remainder) % self.minute_cycle
        self.second = max(0, min(59, self.second))

    def is_match(self, now: datetime) -> bool:
        """
        检查当前时间是否匹配规则

        Args:
            now: 当前时间

        Returns:
            是否匹配
        """
        return (now.minute % self.minute_cycle == self.minute_remainder
                and now.second == self.second)

    def get_next_trigger_time(self, after: Optional[datetime] = None) -> datetime:
        """
        获取下一次触发时间

        Args:
            after: 参考时间（默认当前时间）

        Returns:
            下一次触发时间
        """
        if after is None:
            after = datetime.now()

        # 如果当前时间刚好匹配，返回下一周期的时间
        if self.is_match(after):
            return self._get_next_trigger_from(after + timedelta(seconds=1))

        return self._get_next_trigger_from(after)

    def _get_next_trigger_from(self, from_time: datetime) -> datetime:
        """从指定时间开始计算下一次触发时间"""
        base_minute = from_time.minute
        base_second = from_time.second

        # 计算下一次匹配分钟
        current_cycle_position = base_minute % self.minute_cycle

        if current_cycle_position <= self.minute_remainder:
            # 当前周期内还未到目标分钟
            target_minute = base_minute + (self.minute_remainder - current_cycle_position)
        else:
            # 需要等到下一个周期
            target_minute = base_minute + (self.minute_cycle - current_cycle_position) + self.minute_remainder

        # 构建触发时间
        # 调整小时和天如果需要
        trigger_time = from_time.replace(
            minute=0,
            second=self.second,
            microsecond=0
        ) + timedelta(minutes=target_minute)

        return trigger_time

    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "minute_cycle": self.minute_cycle,
            "minute_remainder": self.minute_remainder,
            "second": self.second,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "TimeRule":
        """从字典创建"""
        return cls(
            minute_cycle=data.get("minute_cycle", 1),
            minute_remainder=data.get("minute_remainder", 0),
            second=data.get("second", 0),
        )


class TimerReminderLogic:
    """
    时间触发提醒逻辑模块

    职责：
    - 管理功能启停状态
    - 管理时间规则（待确认/已生效）
    - 检测时间触发条件
    - 计算下一次触发时间
    - 数据库持久化
    """

    ENTITY_NAME = "TimerReminderEntity"
    ENTITY_ID = 1  # Single record with fixed ID

    def __init__(self) -> None:
        """初始化"""
        # 功能状态
        self._is_running: bool = False

        # 规则管理
        self._pending_rule: Optional[TimeRule] = None  # 待确认的规则
        self._active_rule: Optional[TimeRule] = None   # 已生效的规则

        # 记录上一次触发时间（用于避免重复触发）
        self._last_trigger_time: Optional[datetime] = None

        # 数据库初始化
        self._data_api = get_data_api()
        self._ensure_db_record()

    def _ensure_db_record(self) -> None:
        """确保数据库中存在记录"""
        existing = self._data_api.get(self.ENTITY_NAME, self.ENTITY_ID)
        if existing is None:
            # 创建默认记录
            self._data_api.create(self.ENTITY_NAME, {
                "minute_cycle": 1,
                "minute_remainder": 0,
                "second": 0,
                "is_active": False,
                "is_running": False,
            })

    def load_from_db(self) -> None:
        """从数据库加载规则和状态"""
        record = self._data_api.get(self.ENTITY_NAME, self.ENTITY_ID)
        if record is not None:
            # 加载规则
            if record.get("is_active", False):
                self._active_rule = TimeRule(
                    minute_cycle=record.get("minute_cycle", 1),
                    minute_remainder=record.get("minute_remainder", 0),
                    second=record.get("second", 0),
                )
            # 加载运行状态（不自动启动，只恢复状态标志）
            self._is_running = record.get("is_running", False)

    def _save_to_db(self) -> None:
        """保存规则和状态到数据库"""
        data = {
            "minute_cycle": self._active_rule.minute_cycle if self._active_rule else 1,
            "minute_remainder": self._active_rule.minute_remainder if self._active_rule else 0,
            "second": self._active_rule.second if self._active_rule else 0,
            "is_active": self._active_rule is not None,
            "is_running": self._is_running,
        }
        self._data_api.update(self.ENTITY_NAME, self.ENTITY_ID, data)

    @property
    def is_running(self) -> bool:
        """获取运行状态"""
        return self._is_running

    @property
    def has_active_rule(self) -> bool:
        """是否有已生效的规则"""
        return self._active_rule is not None

    @property
    def has_pending_rule(self) -> bool:
        """是否有待确认的规则"""
        return self._pending_rule is not None

    def get_active_rule(self) -> Optional[TimeRule]:
        """获取已生效的规则"""
        return self._active_rule

    def get_pending_rule(self) -> Optional[TimeRule]:
        """获取待确认的规则"""
        return self._pending_rule

    def set_pending_rule(self, rule: TimeRule) -> None:
        """
        设置待确认的规则

        注意：设置后需要调用 confirm_rule() 才会生效
        """
        self._pending_rule = rule

    def confirm_rule(self) -> bool:
        """
        确认规则，使待确认规则生效

        Returns:
            是否成功（有规则待确认）
        """
        if self._pending_rule is not None:
            self._active_rule = self._pending_rule
            self._pending_rule = None
            # 重置触发记录，避免规则切换后立即触发
            self._last_trigger_time = None
            # 保存到数据库
            self._save_to_db()
            return True
        return False

    def cancel_pending_rule(self) -> None:
        """取消待确认的规则"""
        self._pending_rule = None

    def start(self) -> bool:
        """
        启动功能

        Returns:
            是否成功（有已生效的规则才能启动）
        """
        if self._active_rule is not None:
            self._is_running = True
            # 保存到数据库
            self._save_to_db()
            return True
        return False

    def stop(self) -> None:
        """停止功能"""
        self._is_running = False
        # 保存到数据库
        self._save_to_db()

    def toggle(self) -> bool:
        """
        切换启停状态

        Returns:
            切换后的运行状态
        """
        if self._is_running:
            self.stop()
        else:
            self.start()
        return self._is_running

    def check_trigger(self, now: Optional[datetime] = None) -> bool:
        """
        检查是否满足触发条件

        Args:
            now: 检查时间（默认当前时间）

        Returns:
            是否触发
        """
        if now is None:
            now = datetime.now()

        # 检查运行状态和规则
        if not self._is_running or self._active_rule is None:
            return False

        # 检查时间匹配
        if self._active_rule.is_match(now):
            # 避免同一秒内重复触发
            if self._last_trigger_time is None or self._last_trigger_time.second != now.second:
                self._last_trigger_time = now
                return True

        return False

    def get_next_trigger_time(self) -> Optional[datetime]:
        """
        获取下一次触发时间

        Returns:
            下一次触发时间，无规则则返回 None
        """
        if self._active_rule is None:
            return None
        return self._active_rule.get_next_trigger_time()

    def get_status_info(self) -> Dict[str, Any]:
        """
        获取状态信息

        Returns:
            状态信息字典
        """
        next_time = self.get_next_trigger_time()

        return {
            "is_running": self._is_running,
            "has_active_rule": self.has_active_rule,
            "has_pending_rule": self.has_pending_rule,
            "active_rule": self._active_rule.to_dict() if self._active_rule else None,
            "pending_rule": self._pending_rule.to_dict() if self._pending_rule else None,
            "next_trigger_time": next_time.isoformat() if next_time else None,
        }

    def get_next_trigger_display(self) -> str:
        """
        获取下一次触发时间的显示文本

        Returns:
            显示文本
        """
        if self._active_rule is None:
            return "未配置触发规则"

        next_time = self._active_rule.get_next_trigger_time()
        if next_time is None:
            return "无匹配时间"

        now = datetime.now()

        # 计算剩余时间
        delta = next_time - now
        total_seconds = int(delta.total_seconds())

        if total_seconds <= 0:
            return "即将触发"

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒后 ({next_time.strftime('%H:%M:%S')})"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒后 ({next_time.strftime('%H:%M:%S')})"
        else:
            return f"{seconds}秒后 ({next_time.strftime('%H:%M:%S')})"
