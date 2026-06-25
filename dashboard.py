import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import time

# ページの基本設定（ワイドモード）
st.set_page_config(page_title="計測データ監視ダッシュボード", layout="wide")
st.title("計測データ監視ダッシュボード")

# 【機能拡張】計測データの読み込み（キャッシュの有効期限を5秒に設定）
@st.cache_data(ttl=5)
def load_data():
    conn = sqlite3.connect("data/measurements.db")
    query = """
        SELECT timestamp, temperature, humidity 
        FROM measurements 
        ORDER BY timestamp DESC 
        LIMIT 100
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert('Asia/Tokyo')
        df = df.sort_values('timestamp')
    return df

# アラート履歴（インシデントログ）の読み込み
@st.cache_data(ttl=5)
def load_alerts():
    conn = sqlite3.connect("data/measurements.db")
    query = """
        SELECT timestamp, alert_type, metric, value, message 
        FROM alerts 
        ORDER BY timestamp DESC 
        LIMIT 10
    """
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert('Asia/Tokyo')
    except Exception:
        # main.py側でまだ一度もアラートが発生せず、テーブルが存在しない場合のフォールバック
        df = pd.DataFrame(columns=["timestamp", "alert_type", "metric", "value", "message"])
    finally:
        conn.close()
    return df

st.write("直近の計測データおよびインシデント状況をリアルタイムに監視しています（10秒自動更新）")

# データの取得
df_measure = load_data()
df_alerts = load_alerts()

if not df_measure.empty:
    # 1. グラフ表示エリア（左右分割カラム）
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("温度推移 と ボリンジャーバンド")
        
        # ★機能追加1: ボリンジャーバンドの動的計算（過去10件のローリング窓）
        window = 10
        df_measure['MA'] = df_measure['temperature'].rolling(window=window).mean()
        df_measure['STD'] = df_measure['temperature'].rolling(window=window).std()
        df_measure['Upper_Band'] = df_measure['MA'] + (df_measure['STD'] * 2)
        df_measure['Lower_Band'] = df_measure['MA'] - (df_measure['STD'] * 2)

        # 基本の温度グラフ
        fig_temp = px.line(df_measure, x='timestamp', y='temperature', markers=True)
        
        # 固定閾値の線（レッドライン・ブルーライン）
        fig_temp.add_hline(y=26.0, line_dash="dash", line_color="red", annotation_text="上限閾値 (26.0℃)")
        fig_temp.add_hline(y=24.0, line_dash="dash", line_color="blue", annotation_text="下限閾値 (24.0℃)")
        
        # ★機能追加1: 計算されたボリンジャーバンド(±2σ)を点線で重ね書き
        if not df_measure['Upper_Band'].isnull().all():
            fig_temp.add_scatter(x=df_measure['timestamp'], y=df_measure['Upper_Band'], mode='lines', 
                                 line=dict(color='rgba(255, 165, 0, 0.6)', dash='dot'), name='+2σ (異常上限)')
            fig_temp.add_scatter(x=df_measure['timestamp'], y=df_measure['Lower_Band'], mode='lines', 
                                 line=dict(color='rgba(255, 165, 0, 0.6)', dash='dot'), name='-2σ (異常下限)')
            
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with col2:
        st.subheader("湿度推移")
        fig_humi = px.line(df_measure, x='timestamp', y='humidity', markers=True)
        st.plotly_chart(fig_humi, use_container_width=True)
        
    # 2. ログ・履歴エリア（上下分割カラム）
    st.markdown("---")
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        st.subheader("最新の計測データ (直近10件)")
        st.dataframe(df_measure.tail(10)[['timestamp', 'temperature', 'humidity']], use_container_width=True, hide_index=True)
        
    with t_col2:
        # ★機能追加3: 最新のアラート履歴（インシデントログ）の表示
        st.subheader("最新のアラート履歴 (インシデントログ)")
        if not df_alerts.empty:
            st.dataframe(df_alerts, use_container_width=True, hide_index=True)
        else:
            st.info("現在、検知されたインシデント履歴はありません。システムは正常です。")
else:
    st.warning("まだデータベースにデータがありません。main.py を起動してデータを取得してください。")

# 10秒待機してページを強制再実行（無限ループによるLive更新）
time.sleep(30)
st.rerun()