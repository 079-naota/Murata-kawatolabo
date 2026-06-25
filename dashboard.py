import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import time


# ページの基本設定
st.set_page_config(page_title="計測データ監視ダッシュボード", layout="wide")
st.title("計測データ監視ダッシュボード")

# DBからデータを読み込む関数
# st.cache_data をつけると、毎回DBを読まずに高速化してくれます
@st.cache_data(ttl=10)  # 10秒ごとにキャッシュをクリアして最新データを取得
def load_data():
    conn = sqlite3.connect("data/measurements.db")
    # pandasを使ってSQLを一発でデータフレーム(表形式)に変換
    query = """
        SELECT timestamp, temperature, humidity 
        FROM measurements 
        ORDER BY timestamp DESC 
        LIMIT 100
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 文字列の時間を、Pythonが計算できる「日時型」に変換し、日本時間(+9時間)に合わせる
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert('Asia/Tokyo')
    # グラフを見やすくするため、古い順に並べ替える
    df = df.sort_values('timestamp')
    return df

# データの読み込み
st.write("直近100件のデータを表示中（10秒自動更新）")
df = load_data()

# グラフの描画 (Plotlyを使用)
if not df.empty:
    # 画面を左右に2分割する
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("温度")
        fig_temp = px.line(df, x='timestamp', y='temperature', markers=True)
        # 上限・下限の赤い線を引く（config.yamlの設定値と合わせる）
        fig_temp.add_hline(y=26.0, line_dash="dash", line_color="red", annotation_text="上限閾値 (26.0℃)")
        fig_temp.add_hline(y=24.0, line_dash="dash", line_color="blue", annotation_text="下限閾値 (24.0℃)")
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with col2:
        st.subheader("湿度")
        fig_humi = px.line(df, x='timestamp', y='humidity', markers=True)
        st.plotly_chart(fig_humi, use_container_width=True)
        
    # 生のデータテーブルも下部に表示
    st.subheader("最新データ一覧")
    st.dataframe(df.tail(10)) # 最新の10件だけ表で表示
else:
    st.warning("まだデータベースにデータがありません。main.py を起動してデータを取得してください。")


time.sleep(10)  #main.pyの更新時間に合わせて待機
st.rerun()  # ページを自動更新