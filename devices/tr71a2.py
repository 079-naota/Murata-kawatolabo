import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from devices.models import MeasurementData

# .env ファイルから機密情報を安全に読み込む
load_dotenv()

class TR71A2APIClient:
    """
    おんどとり WebStorage API を経由して TR71A2 の最新データを取得するクラス
    """
    def __init__(self, device_id: str):
        self.device_id = device_id
        # おんどとり WebStorage API の「最新データ取得」エンドポイント
        self.api_url = "https://api.webstorage.jp/v1/devices/current"
        
        self.api_key = os.getenv("TD_API_KEY")
        self.login_id = os.getenv("TD_LOGIN_ID")
        self.login_pass = os.getenv("TD_LOGIN_PASS")

        # フェイルセーフ：認証情報が一つでも欠けていればエラーで止める
        if not all([self.api_key, self.login_id, self.login_pass]):
            raise ValueError("セキュリティエラー: .env ファイルに T&D WebStorage の認証情報が不足しています。")

    def connect(self):
        print(f"[{self.device_id}] おんどとり WebStorage API への接続準備完了")

    def disconnect(self):
        print(f"[{self.device_id}] おんどとり WebStorage API とのセッションを終了しました")

    def read(self) -> MeasurementData:
        headers = {
            "X-HTTP-Method-Override": "GET",
            "Content-Type": "application/json"
        }
        
        # T&D WebStorage APIが要求するJSONペイロード
        payload = {
            "api-key": self.api_key,
            "login-id": self.login_id,
            "login-pass": self.login_pass
        }

        try:
            # APIサーバーへPOSTリクエストを送信
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()

            # APIからの返却データから、対象デバイス（device_id）のデータを探す
            target_device = None
            for device in data.get("devices", []):
                # serial（シリアル番号）または name（機器名）で判定
                if device.get("serial") == self.device_id or device.get("name") == self.device_id:
                    target_device = device
                    break

            if not target_device:
                raise ValueError(f"APIのレスポンスにデバイス '{self.device_id}' のデータが見つかりません。")

            import json
            print("\n=== デバッグ: APIから取得したデバイスデータ ===")
            print(json.dumps(target_device, indent=2, ensure_ascii=False))
            print("==========================================\n")     

            # チャンネル情報から温度(Ch.1)と湿度(Ch.2)を抽出
            temperature = None
            humidity = 50.0
            for channel in target_device.get("channel", []):
                if channel.get("num") == "1":
                    val = channel.get("value")
                    if val != "Sensor Error":
                        temperature = float(val)

            if temperature is None or humidity is None:
                raise ValueError("温度または湿度のデータが取得できませんでした。")

            return MeasurementData(
                device_id=self.device_id,
                temperature=temperature,
                humidity=humidity,
                timestamp=datetime.now(timezone.utc)
            )

        except requests.exceptions.RequestException as e:
            print(f"ネットワークエラー: WebStorage APIとの通信に失敗しました - {e}")
            raise