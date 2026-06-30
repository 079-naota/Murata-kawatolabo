import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh  # 追加

# ページの基本設定（ワイドモード）
st.set_page_config(page_title="計測データ監視ダッシュボード", layout="wide")
st.title("計測データ監視ダッシュボード ")

# 10秒(10000ミリ秒)ごとにバックグラウンドで自動更新（SOCモニター用）
st_autorefresh(interval=10000, key="data_refresh")

# 手動更新ボタンを配置
col_title, col_btn = st.columns([8, 2])
with col_btn:
    st.write("") # 位置調整
    if st.button("データを最新に更新", use_container_width=True):
        st.cache_data.clear() # キャッシュをクリアして最新を強制取得
        st.rerun()

@st.cache_data(ttl=5)
def load_data():
    conn = sqlite3.connect("data/measurements.db")
    # 複数デバイスに対応するため device_id も取得し、取得件数を増やす
    query = """
        SELECT timestamp, device_id, temperature, humidity 
        FROM measurements 
        ORDER BY timestamp DESC 
        LIMIT 300
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # タイムゾーン情報がない場合はUTCとして認識させてから日本時間に変換（エラー対策）
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Tokyo')
        
        # グラフ描画時のシリアライズエラーを防ぐためタイムゾーン情報を削除（tz-naive化）
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        df = df.sort_values('timestamp')
    return df

@st.cache_data(ttl=5)
def load_alerts():
    conn = sqlite3.connect("data/measurements.db")
    # device_id も取得するように追加
    query = """
        SELECT timestamp, device_id, alert_type, metric, value, message 
        FROM alerts 
        ORDER BY timestamp DESC 
        LIMIT 10
    """
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Tokyo')
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)
    except Exception:
        df = pd.DataFrame(columns=["timestamp", "device_id", "alert_type", "metric", "value", "message"])
    finally:
        conn.close()
    return df

st.write("直近の計測データおよびインシデント状況をリアルタイムに監視しています")

# データの取得
df_measure = load_data()
df_alerts = load_alerts()

if not df_measure.empty:
    # デバイス選択UI（プルダウンメニュー）
    device_list = df_measure['device_id'].unique()
    selected_device = st.selectbox("監視するセンサーを選択してください:", device_list)
    
    # 選択されたデバイスのデータだけに絞り込む
    df_filtered = df_measure[df_measure['device_id'] == selected_device].copy()

    # 1. グラフ表示エリア
    if not df_filtered.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"温度({selected_device})")
            
            # ボリンジャーバンドの計算
            window = 10
            df_filtered['MA'] = df_filtered['temperature'].rolling(window=window).mean()
            df_filtered['STD'] = df_filtered['temperature'].rolling(window=window).std()
            df_filtered['Upper_Band'] = df_filtered['MA'] + (df_filtered['STD'] * 2)
            df_filtered['Lower_Band'] = df_filtered['MA'] - (df_filtered['STD'] * 2)

            fig_temp = px.line(df_filtered, x='timestamp', y='temperature', markers=True)
            fig_temp.add_hline(y=26.0, line_dash="dash", line_color="red", annotation_text="上限閾値 (26.0℃)")
            fig_temp.add_hline(y=24.0, line_dash="dash", line_color="blue", annotation_text="下限閾値 (24.0℃)")
            
            if not df_filtered['Upper_Band'].isnull().all():
                fig_temp.add_scatter(x=df_filtered['timestamp'], y=df_filtered['Upper_Band'], mode='lines', 
                                     line=dict(color='rgba(255, 165, 0, 0.6)', dash='dot'), name='+2σ (異常上限)')
                fig_temp.add_scatter(x=df_filtered['timestamp'], y=df_filtered['Lower_Band'], mode='lines', 
                                     line=dict(color='rgba(255, 165, 0, 0.6)', dash='dot'), name='-2σ (異常下限)')
                
            st.plotly_chart(fig_temp, use_container_width=True)
            
        with col2:
            st.subheader(f"湿度({selected_device})")
            fig_humi = px.line(df_filtered, x='timestamp', y='humidity', markers=True)
            st.plotly_chart(fig_humi, use_container_width=True)
            
        # 2. ログ・履歴エリア
        st.markdown("---")
        t_col1, t_col2 = st.columns(2)
        
        with t_col1:
            st.subheader("最新の計測データ")
            st.dataframe(df_filtered.tail(10)[['timestamp', 'temperature', 'humidity']], use_container_width=True, hide_index=True)
            
        with t_col2:
            st.subheader("インシデントログ")
            if not df_alerts.empty:
                alert_filtered = df_alerts[(df_alerts['device_id'] == selected_device) | (df_alerts['device_id'] == 'SYSTEM_ALERT')]
                if not alert_filtered.empty:
                    st.dataframe(alert_filtered, use_container_width=True, hide_index=True)
                else:
                    st.info(f"{selected_device} に関するインシデントはありません。")
            else:
                st.info("現在、検知されたインシデント履歴はありません。システムは正常です。")
    else:
        st.info(f"選択されたデバイス ({selected_device}) のデータがまだありません。")

else:
    st.warning("まだデータベースにデータがありません。main.py を起動してデータを取得してください。")