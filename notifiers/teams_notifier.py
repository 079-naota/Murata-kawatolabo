import httpx
from devices.models import Alert
from .base import Notifier

class TeamsNotifier(Notifier):
    """
    Microsoft TeamsのIncoming Webhook (Power Automate) を利用してアラートを送信するクラス
    """
    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("Webhook URLが設定されていません。")
        self.webhook_url = webhook_url

    def send(self, alert: Alert) -> None:
        # アラートの種類に応じて色を変更（閾値逸脱: 赤色, 傾向異常: オレンジ色）
        color = "FF0000" if alert.alert_type == "threshold" else "FF9900"
        
        # 単位とタイトルの判定
        unit = "℃" if alert.metric == "temperature" else "%"
        title_text = "閾値アラート" if alert.alert_type == "threshold" else "傾向異常アラート"
        
        # TeamsのMessageCardフォーマットを作成
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"⚠️ {title_text}検知",
            "sections": [{
                "activityTitle": f"⚠️ **{title_text}**",
                "activitySubtitle": f"デバイス: {alert.device_id}",
                "facts": [
                    {"name": "検知時刻", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")},
                    {"name": "対象", "value": "温度" if alert.metric == "temperature" else "湿度"},
                    {"name": "計測値", "value": f"{alert.value:.1f} {unit}"},
                    {"name": "閾値設定", "value": f"{alert.threshold:.1f} {unit}"},
                    {"name": "方向", "value": alert.direction}
                ],
                "text": alert.message
            }]
        }
        
        # HTTP POSTリクエストでTeamsへ送信
        response = httpx.post(self.webhook_url, json=payload, timeout=10.0)
        
        # エラーがあれば例外を発生させる
        response.raise_for_status()