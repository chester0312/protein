import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. 時區與頁面設定
tw_tz = pytz.timezone('Asia/Taipei')
st.set_page_config(page_title="增肌減脂雲端助手", layout="centered")

# 2. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 讀取資料 (使用 ttl=0 確保即時更新)
try:
    df_logs = conn.read(worksheet="Logs", ttl=0).dropna(how='all')
    df_foods = conn.read(worksheet="MyFoods", ttl=0).dropna(how='all')
except Exception as e:
    st.error(f"連線失敗，請檢查分頁 Logs/MyFoods。錯誤：{e}")
    df_logs = pd.DataFrame(columns=["時間", "項目", "蛋白質", "金額"])
    df_foods = pd.DataFrame(columns=["組合名稱", "蛋白質", "金額"])

# --- 側邊欄：個人狀態設定 ---
with st.sidebar:
    st.header("👤 個人狀態設定")
    curr_weight = st.number_input("目前體重 (kg)", min_value=30.0, value=67.0, step=0.1)
    p_factor = st.slider("蛋白質倍數", 1.0, 2.5, 1.5, 0.1)
    TARGET_P = round(curr_weight * p_factor, 1)
    st.info(f"🎯 當前目標：{TARGET_P} g")
    
    st.divider()
    st.header("⚙️ 組合管理")
    with st.form("add_food", clear_on_submit=True):
        new_name = st.text_input("新增快捷按鈕名稱")
        new_p = st.number_input("蛋白質(g)", min_value=0.0, step=0.1)
        new_c = st.number_input("金額(元)", min_value=0, step=1)
        if st.form_submit_button("儲存按鈕"):
            if new_name:
                food_data = pd.DataFrame([{"組合名稱": new_name, "蛋白質": new_p, "金額": new_c}])
                updated_foods = pd.concat([df_foods, food_data], ignore_index=True)
                conn.update(worksheet="MyFoods", data=updated_foods)
                st.success("按鈕已新增！")
                st.rerun()

# --- 主畫面邏輯 ---
st.title("💪 蛋白質紀錄 & 預算監控")

# 篩選今日資料 (修正時區)
if not df_logs.empty:
    df_logs['時間'] = pd.to_datetime(df_logs['時間'])
    today_date = datetime.now(tw_tz).date()
    today_df = df_logs[df_logs['時間'].dt.date == today_date]
else:
    today_df = pd.DataFrame()

# --- 核心：輸入區域 (無論是否有紀錄都會顯示，放在最上方方便操作) ---
st.subheader("📝 快速紀錄 / 手動輸入")
tab1, tab2 = st.tabs(["⚡ 快捷按鈕", "✍️ 手動輸入"])

with tab1:
    if not df_foods.empty:
        cols = st.columns(3)
        for i, row in df_foods.iterrows():
            name, p_val, c_val = row['組合名稱'], row['蛋白質'], row['金額']
            with cols[i % 3]:
                if st.button(f"{name}\n{p_val}g / ${c_val}", key=f"btn_{i}"):
                    new_entry = pd.DataFrame([{
                        "時間": datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M"),
                        "項目": name, "蛋白質": p_val, "金額": c_val
                    }])
                    updated_logs = pd.concat([df_logs, new_entry], ignore_index=True)
                    conn.update(worksheet="Logs", data=updated_logs)
                    st.rerun()
    else:
        st.info("目前沒有快捷按鈕，請至側邊欄設定。")

with tab2:
    with st.form("manual_input", clear_on_submit=True):
        m_name = st.text_input("食物名稱 (例如: 一早吃的飯糰)")
        mc1, mc2 = st.columns(2)
        m_p = mc1.number_input("蛋白質(g)", min_value=0.0)
        m_c = mc2.number_input("金額(元)", min_value=0)
        if st.form_submit_button("送出紀錄"):
            manual_entry = pd.DataFrame([{
                "時間": datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M"),
                "項目": m_name, "蛋白質": m_p, "金額": m_c
            }])
            updated_logs = pd.concat([df_logs, manual_entry], ignore_index=True)
            conn.update(worksheet="Logs", data=updated_logs)
            st.rerun()

# --- 今日進度報告 ---
st.divider()
if not today_df.empty:
    total_p = today_df["蛋白質"].sum()
    total_c = today_df["金額"].sum()
    
    st.subheader(f"📊 今日統計 ({datetime.now(tw_tz).strftime('%m/%d')})")
    st.progress(min(total_p / TARGET_P, 1.0))
    
    m1, m2, m3 = st.columns(3)
    m1.metric("今日攝取", f"{total_p} g")
    m2.metric("剩餘目標", f"{max(0.0, round(TARGET_P - total_p, 1))} g")
    m3.metric("累計花費", f"{total_c} 元")
    
    st.table(today_df[["時間", "項目", "蛋白質", "金額"]].assign(時間=lambda x: x['時間'].dt.strftime('%H:%M')))
else:
    st.warning("一早還沒吃東西？趕快紀錄一下吧！")
