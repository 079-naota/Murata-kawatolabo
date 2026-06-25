from datetime import datetime, timezone
from devices.models import MeasurementData, ThresholdConfig
from monitoring.threshold_checker import ThresholdChecker

def main():
    print("=== 閾値判定テスト開始 ===")
    
    # 1. 厳しい閾値を設定（アラートを発生させやすくするため）
    # 温度: 24.0〜26.0℃ / 湿度: 45.0〜55.0%
    config = ThresholdConfig(
        device_id="test_sensor_01",
        temp_lower=24.0,
        temp_upper=26.0,
        humi_lower=45.0,
        humi_upper=55.0,
        trend_enabled=False,
        trend_window_min=10,
        trend_slope_limit=0.5,
        alert_cooldown_sec=300
    )
    
    checker = ThresholdChecker()
    
    # 2. テストデータの準備（意図的に上限超え、下限超え、正常のパターンを作る）
    test_cases = [
        MeasurementData("test_sensor_01", datetime.now(timezone.utc), 28.5, 60.0), # 温度・湿度ともに上限超え
        MeasurementData("test_sensor_01", datetime.now(timezone.utc), 22.0, 40.0), # 温度・湿度ともに下限超え
        MeasurementData("test_sensor_01", datetime.now(timezone.utc), 25.0, 50.0), # 正常値
    ]
    
    # 3. 判定の実行
    for i, data in enumerate(test_cases, 1):
        print(f"\n[ケース{i}] 計測値: 温度 {data.temperature}℃, 湿度 {data.humidity}%")
        alerts = checker.check(data, config)
        
        if not alerts:
            print("  ->正常（アラートなし）")
        else:
            for alert in alerts:
                print(f"  ->アラート検知: [{alert.metric} {alert.direction}] {alert.message}")

    print("\n=== 閾値判定テスト完了 ===")

if __name__ == "__main__":
    main()