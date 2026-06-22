import random
from datetime import datetime, timezone
from .base import MeasurementDevice
from .models import MeasurementData

class DummyDevice(MeasurementDevice):
    """
    テスト用のダミーデバイス。
    20.0〜30.0℃の温度と、40.0〜60.0%の湿度をランダムに生成する。
    """
    def __init__(self, device_id: str = "dummy_01"):
        self._device_id = device_id
        self._connected = False

    def connect(self) -> None:
        self._connected = True
        print(f"[{self._device_id}] ダミーデバイスに接続しました。")

    def disconnect(self) -> None:
        self._connected = False
        print(f"[{self._device_id}] ダミーデバイスから切断しました。")

    def read(self) -> MeasurementData:
        if not self._connected:
            raise RuntimeError("デバイスが接続されていません。")
        
        temp = round(random.uniform(20.0, 30.0), 1)
        humi = round(random.uniform(40.0, 60.0), 1)
        
        return MeasurementData(
            device_id=self._device_id,
            timestamp=datetime.now(timezone.utc),
            temperature=temp,
            humidity=humi,
            raw={"status": "ok", "source": "dummy"}
        )

    @property
    def device_id(self) -> str:
        return self._device_id