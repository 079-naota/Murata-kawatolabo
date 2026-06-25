import time
import yaml
from datetime import datetime, timezone
from devices.dummy import DummyDevice
from devices.models import ThresholdConfig, MeasurementData, Alert
from storage.sqlite_storage import SQLiteStorage
from monitoring.threshold_checker import ThresholdChecker
from notifiers.teams_notifier import TeamsNotifier
from core.alert_manager import AlertManager
from monitoring.trend_analyzer import TrendAnalyzer
from devices.tr71a2 import TR71A2APIClient
import random

class DummySensor:
    def __init__(self, device_id):
        self.device_id = device_id

    def connect(self):
        print(f"[{self.device_id}] 仮想センサー接続完了")

    def disconnect(self):
        print(f"[{self.device_id}] 仮想センサー切断")

    def read(self):
        # 20.0℃〜30.0℃、湿度40.0%〜60.0%のランダムな数値を生成
        fake_temp = round(random.uniform(20.0, 30.0), 1)
        fake_humi = round(random.uniform(40.0, 60.0), 1)
        
        return MeasurementData(
            device_id=self.device_id,
            temperature=fake_temp,
            humidity=fake_humi,
            timestamp=datetime.now(timezone.utc)
        )

def load_config(path: str) -> dict:
    """YAML設定ファイルを読み込む"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    print("=== システム起動準備 ===")
    config = load_config("config.yaml")
    
    # 閾値設定オブジェクトの構築
    threshold_conf = ThresholdConfig(
        device_id=config['device']['id'],
        temp_lower=config['threshold']['temp_lower'],
        temp_upper=config['threshold']['temp_upper'],
        humi_lower=config['threshold']['humi_lower'],
        humi_upper=config['threshold']['humi_upper'],
        trend_enabled=config['trend']['enabled'],
        trend_window_min=config['trend']['window_min'],
        trend_slope_limit=config['trend']['slope_limit'],
        alert_cooldown_sec=config['alert']['cooldown_sec']
    )

    # 各モジュールの初期化
    device = TR71A2APIClient(config['device']['id'])
    storage = SQLiteStorage(config['monitoring']['db_path'])
    checker = ThresholdChecker()
    analyzer = TrendAnalyzer()
    notifier = TeamsNotifier(config['teams']['webhook_url'])
    alert_mgr = AlertManager(threshold_conf.alert_cooldown_sec)

    print("=== 計測データ管理システム メインループ開始 ===")
    
    #監視対象デバイスをリストで管理
    devices=[
        TR71A2APIClient(config['device']['id']),
        DummySensor("dummy_001")
    ]

    #所有デバイスの一括接続
    for dev in devices:
        dev.connect()

    #監視用の変数を初期化
    last_success_time = datetime.now()
    error_count = 0


    try:
        while True:
            for dev in devices:
                try:
                    # 1. データの取得
                    data = dev.read()
                    now_str = datetime.now().strftime('%H:%M:%S')
                    print(f"[{now_str}] 計測: 温度 {data.temperature}℃, 湿度 {data.humidity}%")

                    #データを正常に受信できたら監視タイマーのリセット
                    last_success_time = datetime.now()
                    if error_count > 0:
                        print("通信障害から復帰しました。")
                        error_count = 0
                    
                    # 2. データのDB保存
                    storage.save_measurement(data)
                    
                    # 3. 閾値チェック
                    alerts = checker.check(data, threshold_conf)
                    
                    # 4. （※ここに後で傾向監視（トレンド分析）が追加されます）
                    history = storage.get_recent_measurements(data.device_id, threshold_conf.trend_window_min)
                    trend_alerts = analyzer.analyze(history, threshold_conf)
                    alerts.extend(trend_alerts)

                    # 5. クールダウンによる重複通知のフィルタリング
                    valid_alerts = alert_mgr.filter(alerts)
                    
                    if len(alerts) > 0 and len(valid_alerts) == 0:
                        print("  -> 異常を検知しましたが、スパム防止のため通知をスキップしました。")
                    
                    # 6. アラートの通知とDB記録
                    for alert in valid_alerts:
                        print(f"  -> 通知送信中: {alert.metric} {alert.direction}")
                        notifier.send(alert)
                        storage.save_alert(alert)
                        
                except Exception as e:
                    error_count += 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{dev.device_id}] 読み取りエラー ({error_count}回目): {e}")
            
            #データ取得成功からどれだけの時間が経過したかを計算
            time_since_last = (datetime.now() - last_success_time).total_seconds()

            #センサーの通信が一定時間以上途絶している場合の警告
            if time_since_last > 300:
                print(" 警告: センサー通信が5分以上途絶しています。")

                sos_alert = Alert(
                    device_id="SYSTEM_ALERT",
                    alert_type="system_down",
                    metric="system",
                    direction="offline",
                    value=0.0,
                    threshold=0.0,
                    timestamp=datetime.now(timezone.utc),
                    message="センサー通信が5分以上途絶しています。"
                )

                #SOSの連発を防ぐためのクールダウン
                if alert_mgr.filter([sos_alert]):
                    notifier.send(sos_alert)

            #7.次のサイクルまでの待機
            time.sleep(config['monitoring']['interval_sec'])

    except KeyboardInterrupt:
        # Ctrl+C で安全に終了するための処理
        print("\n=== システム停止要求を受信 ===")
    finally:
        for dev in devices:
            dev.disconnect()
        print("=== システムを安全に終了しました ===")

if __name__ == "__main__":
    main()