from abc import ABC, abstractmethod
from .models import MeasurementData

class MeasurementDevice(ABC):
    """
    計測デバイスの共通インターフェース。
    新しいデバイスを追加する際はこのクラスを継承して実装する。
    """

    @abstractmethod
    def connect(self) -> None:
        """デバイスへの接続を確立する"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """接続を切断し、リソースを解放する"""
        pass

    @abstractmethod
    def read(self) -> MeasurementData:
        """デバイスから計測値を1件取得して返す"""
        pass

    @property
    @abstractmethod
    def device_id(self) -> str:
        """デバイスを一意に識別するIDを返す"""
        pass