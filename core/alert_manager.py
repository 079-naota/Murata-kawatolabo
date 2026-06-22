from datetime import datetime, timezone
from typing import List, Dict
from devices.models import Alert

class AlertManager:
    """
    同一アラートの連続通知を防ぐためのクールダウン管理クラス
    """
    def __init__(self, cooldown_sec: int):
        self.cooldown_sec = cooldown_sec
        # キー: "device_id_metric_type", 値: 最後に通知した時刻
        self._last_notified: Dict[str, datetime] = {}

    def filter(self, alerts: List[Alert]) -> List[Alert]:
        filtered_alerts = []
        now = datetime.now(timezone.utc)

        for alert in alerts:
            # アラートを識別するための一意なキーを作成
            # 例: "test_sensor_01_temperature_threshold"
            alert_key = f"{alert.device_id}_{alert.metric}_{alert.alert_type}"
            
            last_time = self._last_notified.get(alert_key)
            
            # 「過去に一度も通知していない」または「前回通知からクールダウン秒数以上経過している」場合
            if last_time is None or (now - last_time).total_seconds() >= self.cooldown_sec:
                filtered_alerts.append(alert)
                # 最後に通知した時間を現在時刻で上書き
                self._last_notified[alert_key] = now
            else:
                # クールダウン中のため通知をスキップ
                pass

        return filtered_alerts