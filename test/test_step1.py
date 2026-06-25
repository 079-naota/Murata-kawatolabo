import os
import time
from devices.dummy import DummyDevice
from storage.sqlite_storage import SQLiteStorage

def main():
    # DB保存用のディレクトリを作成
    os.makedirs("data", exist_ok=True)
    db_path = "data/test_measurements.db"
    
    print("=== テスト開始 ===")
    
    # 1. 各モジュールの初期化
    device = DummyDevice("test_sensor_01")
    storage = SQLiteStorage(db_path)
    
    # 2. デバイス接続
    device.connect()
    
    # 3. データを3回取得してDBに保存
    print("\n--- データの取得と保存 ---")
    for i in range(3):
        data = device.read()
        storage.save_measurement(data)
        print(f"[{i+1}回目] 保存完了: {data.temperature}℃, {data.humidity}%")
        time.sleep(1) # 1秒待機
        
    # 4. DBから直近（過去5分）のデータを取得して確認
    print("\n--- DBからのデータ取得（トレンド分析用） ---")
    history = storage.get_recent_measurements("test_sensor_01", limit_minutes=5)
    
    for row in history:
        # UTC時間をローカル時間のように見やすくフォーマット
        time_str = row.timestamp.strftime("%H:%M:%S")
        print(f"取得レコード: {time_str} - {row.temperature}℃, {row.humidity}%")
        
    # 5. 切断
    device.disconnect()
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()