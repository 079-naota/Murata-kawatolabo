import sqlite3
import random
import math
from datetime import datetime, timedelta, timezone

# データベースファイルのパス
DB_PATH = "data/measurements.db"

def setup_db():
    """テーブルの初期化（既存のデータをクリアしてクリーンな状態にする）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS measurements')
    cursor.execute('DROP TABLE IF EXISTS alerts')
    
    cursor.execute('''
        CREATE TABLE measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_id TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            metric TEXT NOT NULL,
            direction TEXT,
            value REAL,
            threshold REAL,
            message TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_measurement(cursor, dt, device_id, temp, humi):
    cursor.execute('''
        INSERT INTO measurements (timestamp, device_id, temperature, humidity)
        VALUES (?, ?, ?, ?)
    ''', (dt.isoformat(), device_id, round(temp, 1), round(humi, 1)))

def insert_alert(cursor, dt, device_id, alert_type, metric, direction, value, threshold, message):
    cursor.execute('''
        INSERT INTO alerts (timestamp, device_id, alert_type, metric, direction, value, threshold, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (dt.isoformat(), device_id, alert_type, metric, direction, value, threshold, message))


def generate_demo_data():
    conn = setup_db()
    cursor = conn.cursor()
    
    # 基準時間：現在時刻からちょうど3日前
    now_utc = datetime.now(timezone.utc)
    start_time = now_utc - timedelta(days=3)
    
    current_time = start_time
    target_device = "52AA1F10"  # 本物のおんどとりID
    dummy_device = "dummy_001"
    
    print("=== プレゼン用デモデータを生成中 ===")
    
    while current_time <= now_utc:
        # 経過時間（時間）
        elapsed_hours = (current_time - start_time).total_seconds() / 3600.0
        
        # ---------------------------------------------------
        # 正常データのベース生成（サイン波で昼夜の気温差を表現）
        # ベース温度: 22.0℃ 〜 24.0℃
        # ---------------------------------------------------
        base_temp = 23.0 + math.sin(elapsed_hours * (math.pi / 12)) * 1.0
        base_humi = 50.0 + math.cos(elapsed_hours * (math.pi / 12)) * 5.0
        
        # ランダムな揺らぎを追加
        temp_val = base_temp + random.uniform(-0.3, 0.3)
        humi_val = base_humi + random.uniform(-1.0, 1.0)
        
        dummy_temp = 23.5 + random.uniform(-0.5, 0.5)
        dummy_humi = 55.0 + random.uniform(-2.0, 2.0)

        # ---------------------------------------------------
        # シナリオ1: トレンド異常（1日目の午後13:00頃）
        # 閾値(26℃)は超えないが、急激に温度が上昇する
        # ---------------------------------------------------
        if 25.0 <= elapsed_hours <= 25.5:
            temp_val += (elapsed_hours - 25.0) * 4.0 # 最大+2.0℃の急上昇
            if int(elapsed_hours * 12) % 6 == 0: # アラート履歴に1件追加
                insert_alert(cursor, current_time, target_device, "trend", "temperature", "rapid_increase", temp_val, 0.5, "温度の急激な上昇トレンドを検知しました")

        # ---------------------------------------------------
        # シナリオ2: テクニカル指標（ボリンジャーバンド）の逸脱（2日目の午前10:00頃）
        # 1点だけ異常なスパイクが発生する
        # ---------------------------------------------------
        elif 46.0 <= elapsed_hours <= 46.08: # 1回(5分間)だけのスパイク
            temp_val += 3.0 # ダッシュボード上でオレンジ点線（+2σ）を突き抜ける

        # ---------------------------------------------------
        # シナリオ3: 閾値超過（2日目の午後15:00頃）
        # 完全に閾値（26.0℃）を超えてアラートが鳴り続ける
        # ---------------------------------------------------
        elif 51.0 <= elapsed_hours <= 53.0:
            temp_val = 27.5 + random.uniform(-0.2, 0.2)
            if int(elapsed_hours * 12) % 12 == 0: # クールダウンを考慮して1時間に1回アラート記録
                insert_alert(cursor, current_time, target_device, "threshold", "temperature", "upper", temp_val, 26.0, "temperature が上限値 (26.0) を超過しました")

        # ---------------------------------------------------
        # シナリオ4: システムダウン / 監視対象ダウン（3日目の午前09:00〜10:00）
        # データが一切保存されない（空白期間ができる）
        # ---------------------------------------------------
        elif 69.0 <= elapsed_hours <= 70.0:
            if elapsed_hours >= 69.08 and elapsed_hours < 69.15: # ダウンから5分後にSOSアラート
                insert_alert(cursor, current_time, "SYSTEM_ALERT", "system_down", "system", "offline", 0.0, 0.0, "センサー通信が5分以上途絶しています。API制限かネットワーク断の恐れがあります。")
            
            current_time += timedelta(minutes=5)
            continue # DBへのデータ保存をスキップ（グラフに空白を作る）

        # データの保存
        insert_measurement(cursor, current_time, target_device, temp_val, humi_val)
        insert_measurement(cursor, current_time, dummy_device, dummy_temp, dummy_humi)
        
        # 5分進める
        current_time += timedelta(minutes=5)

    conn.commit()
    conn.close()
    print("✅ プレゼン用デモデータ（3日分・4シナリオ）の生成が完了しました！")
    print("streamlit run dashboard.py を起動してダッシュボードを確認してください。")

if __name__ == "__main__":
    generate_demo_data()