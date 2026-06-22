from abc import ABC, abstractmethod
from devices.models import Alert

class Notifier(ABC):
    """
    通知先の共通インターフェース。
    """
    @abstractmethod
    def send(self, alert: Alert) -> None:
        """アラートを通知する"""
        pass