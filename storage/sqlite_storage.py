import sqlite3
from datetime import datetime
from typing import List
from devices.models import MeasurementData, Alert

class SQLiteStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """テーブルとインデックスが存在しない場合は作成する"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 計測値テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            # アラートテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT,
                    notified INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # 検索高速化のためのインデックス
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_device_time ON measurements(device_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_device_time ON alerts(device_id, timestamp)")
            conn.commit()

    def save_measurement(self, data: MeasurementData) -> None:
        """計測データをDBに保存する"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO measurements (device_id, timestamp, temperature, humidity)
                VALUES (?, ?, ?, ?)
            """, (
                data.device_id,
                data.timestamp.isoformat(),
                data.temperature,
                data.humidity
            ))
            conn.commit()

    def get_recent_measurements(self, device_id: str, limit_minutes: int) -> List[MeasurementData]:
        """指定された時間（分）以内の計測データを取得する（トレンド分析用）"""
        with sqlite3.connect(self.db_path) as conn:
            # ISO8601形式の文字列として保存されているため、SQLiteのdatetime関数で計算
            cursor = conn.cursor()
            cursor.execute("""
                SELECT device_id, timestamp, temperature, humidity
                FROM measurements
                WHERE device_id = ? 
                  AND timestamp >= datetime('now', ?)
                ORDER BY timestamp ASC
            """, (device_id, f'-{limit_minutes} minutes'))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(MeasurementData(
                    device_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    temperature=row[2],
                    humidity=row[3]
                ))
            return results

    def save_alert(self, alert: Alert) -> None:
        """発生したアラートをDBに記録する"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (
                    alert_id, device_id, alert_type, metric, direction, 
                    value, threshold, timestamp, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.device_id, alert.alert_type, alert.metric,
                alert.direction, alert.value, alert.threshold, 
                alert.timestamp.isoformat(), alert.message
            ))
            conn.commit()