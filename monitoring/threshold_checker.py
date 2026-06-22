from typing import List
from devices.models import MeasurementData, ThresholdConfig, Alert

class ThresholdChecker:
    """
    計測データが設定された閾値（上限・下限）を逸脱していないか検査するクラス
    """
    def check(self, data: MeasurementData, config: ThresholdConfig) -> List[Alert]:
        alerts = []

        # --- 温度のチェック ---
        if data.temperature > config.temp_upper:
            alerts.append(self._create_alert(
                data, config, "temperature", "upper", data.temperature, config.temp_upper,
                f"温度が上限閾値（{config.temp_upper}℃）を超過しています。"
            ))
        elif data.temperature < config.temp_lower:
            alerts.append(self._create_alert(
                data, config, "temperature", "lower", data.temperature, config.temp_lower,
                f"温度が下限閾値（{config.temp_lower}℃）を下回っています。"
            ))

        # --- 湿度のチェック（湿度が取得できている場合のみ） ---
        if data.humidity is not None:
            if data.humidity > config.humi_upper:
                alerts.append(self._create_alert(
                    data, config, "humidity", "upper", data.humidity, config.humi_upper,
                    f"湿度が上限閾値（{config.humi_upper}%）を超過しています。"
                ))
            elif data.humidity < config.humi_lower:
                alerts.append(self._create_alert(
                    data, config, "humidity", "lower", data.humidity, config.humi_lower,
                    f"湿度が下限閾値（{config.humi_lower}%）を下回っています。"
                ))

        return alerts

    def _create_alert(self, data: MeasurementData, config: ThresholdConfig, 
                      metric: str, direction: str, value: float, threshold: float, message: str) -> Alert:
        """Alertオブジェクトを生成するヘルパーメソッド"""
        return Alert(
            device_id=data.device_id,
            alert_type="threshold",
            metric=metric,
            direction=direction,
            value=value,
            threshold=threshold,
            timestamp=data.timestamp,
            message=message
        )