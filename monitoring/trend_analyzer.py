import numpy as np
from typing import List
from devices.models import MeasurementData, ThresholdConfig, Alert

class TrendAnalyzer:
    """
    過去の履歴データから、傾向異常（トレンド）や突発的な異常（ボリンジャーバンド）を検知するクラス
    """
    def analyze(self, history: List[MeasurementData], config: ThresholdConfig) -> List[Alert]:
        # データが少なすぎる場合は線形回帰や標準偏差の計算ができないためスキップ（最低3データ必要）
        if not config.trend_enabled or len(history) < 3:
            return []

        alerts = []
        
        # 時間(x軸)と温度(y軸)の配列を準備
        # 最初のデータからの経過分数（分単位）をx軸とする
        t0 = history[0].timestamp.timestamp()
        x = np.array([(d.timestamp.timestamp() - t0) / 60.0 for d in history])
        y_temp = np.array([d.temperature for d in history])

        # 1. 線形回帰によるトレンド（傾き）検知
        slope, _ = np.polyfit(x, y_temp, 1)  # 1次関数(直線)でフィッティングし、傾きを取得
        
        if abs(slope) > config.trend_slope_limit:
            direction = "rising" if slope > 0 else "falling"
            alerts.append(self._create_alert(
                history[-1], "trend", direction, y_temp[-1], config.trend_slope_limit,
                f"温度の急激な変化傾向（{slope:+.2f} ℃/分）を検知しました。"
            ))

        # 2. ボリンジャーバンドによる突発異常検知
        mean_temp = np.mean(y_temp)
        std_temp = np.std(y_temp)
        
        # 普段のブレ幅(標準偏差)が計算可能な場合のみ実行
        if std_temp > 0:
            upper_band = mean_temp + (3 * std_temp)  # +3σ
            lower_band = mean_temp - (3 * std_temp)  # -3σ
            latest_temp = y_temp[-1]

            if latest_temp > upper_band:
                alerts.append(self._create_alert(
                    history[-1], "bollinger", "upper", latest_temp, upper_band,
                    f"ボリンジャーバンド上限（+3σ: {upper_band:.1f}℃）を突破する突発的な上昇を検知しました。"
                ))
            elif latest_temp < lower_band:
                alerts.append(self._create_alert(
                    history[-1], "bollinger", "lower", latest_temp, lower_band,
                    f"ボリンジャーバンド下限（-3σ: {lower_band:.1f}℃）を突破する突発的な低下を検知しました。"
                ))

        return alerts

    def _create_alert(self, data: MeasurementData, alert_type: str, direction: str, value: float, threshold: float, message: str) -> Alert:
        """Alertオブジェクトを生成するヘルパーメソッド"""
        return Alert(
            device_id=data.device_id,
            alert_type=alert_type,
            metric="temperature",
            direction=direction,
            value=value,
            threshold=threshold,
            timestamp=data.timestamp,
            message=message
        )