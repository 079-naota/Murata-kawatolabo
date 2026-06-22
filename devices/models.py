from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class MeasurementData:
    """
    センサーから取得した1回分の計測データを表現するクラス
    """
    device_id: str
    timestamp: datetime
    temperature: float
    humidity: float | None = None
    # センサーからの生データ（バイト列など）をデバッグや将来拡張のために保持
    raw: dict = field(default_factory=dict)

@dataclass
class ThresholdConfig:
    """
    デバイスごとの閾値・監視設定を保持するマスタデータクラス
    """
    device_id: str
    temp_lower: float
    temp_upper: float
    humi_lower: float
    humi_upper: float
    trend_enabled: bool
    trend_window_min: int
    trend_slope_limit: float
    alert_cooldown_sec: int

@dataclass
class Alert:
    """
    検知された異常（アラート）の情報を保持するクラス
    """
    device_id: str
    alert_type: str      # "threshold" または "trend"
    metric: str          # "temperature" または "humidity"
    direction: str       # "upper", "lower", "rising", "falling"
    value: float
    threshold: float
    timestamp: datetime
    message: str
    # アラートの一意なIDはインスタンス生成時に自動でUUIDを割り当てる
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))