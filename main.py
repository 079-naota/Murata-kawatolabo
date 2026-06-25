import time
import yaml
from datetime import datetime
from devices.dummy import DummyDevice
from devices.models import ThresholdConfig
from storage.sqlite_storage import SQLiteStorage
from monitoring.threshold_checker import ThresholdChecker
from notifiers.teams_notifier import TeamsNotifier
from core.alert_manager import AlertManager
from monitoring.trend_analyzer import TrendAnalyzer


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
    device = DummyDevice(config['device']['id'])
    storage = SQLiteStorage(config['monitoring']['db_path'])
    checker = ThresholdChecker()
    analyzer = TrendAnalyzer()
    notifier = TeamsNotifier(config['teams']['webhook_url'])
    alert_mgr = AlertManager(threshold_conf.alert_cooldown_sec)

    print("=== 計測データ管理システム メインループ開始 ===")
    device.connect()

    try:
        while True:
            # 1. データの取得
            data = device.read()
            now_str = datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] 計測: 温度 {data.temperature}℃, 湿度 {data.humidity}%")
            
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
                
            # 7. 次の取得サイクルまで待機
            time.sleep(config['monitoring']['interval_sec'])

    except KeyboardInterrupt:
        # Ctrl+C で安全に終了するための処理
        print("\n=== システム停止要求を受信 ===")
    finally:
        device.disconnect()
        print("=== システムを安全に終了しました ===")

if __name__ == "__main__":
    main()