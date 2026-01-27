import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="增肌減脂雲端記錄器", layout="centered")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料
df = conn.read()

# 你的目標與固定清單
TARGET_P = 100.5
QUICK_FOODS = {
    "飯糰組合": {"p": 25, "c": 65},
    "高蛋豆漿組合": {"p": 35, "c": 45},
    "博客雞胸肉": {"p": 24, "c": 50},
    "晚餐便當": {"p": 30, "c": 100},
    "乳清(1.2匙)": {"p": 29, "c": 42},
}

st.title("💪 蛋白質雲端紀錄 (永久儲存版)")

# --- 快速記錄 ---
st.write("### ⚡ 常用組合")
cols = st.columns(len(QUICK_FOODS))
for i, (name, data) in enumerate(QUICK_FOODS.items()):
    if cols[i].button(f"{name}"):
        new_data = pd.DataFrame([{
            "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "項目": name,
            "蛋白質": data['p'],
            "金額": data['c']
        }])
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success(f"已存入雲端：{name}")
        st.rerun()

# --- 自由輸入 ---
st.write("---")
st.write("### ✍️ 彈性自由輸入")
with st.form("custom_input", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        custom_name = st.text_input("食物名稱")
    with col2:
        custom_p = st.number_input("蛋白質(g)", min_value=0.0)
    with col3:
        custom_c = st.number_input("金額(元)", min_value=0)
    
    if st.form_submit_button("新增並同步至雲端"):
        new_data = pd.DataFrame([{
            "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "項目": custom_name,
            "蛋白質": custom_p,
            "金額": custom_c
        }])
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success(f"已同步：{custom_name}")
        st.rerun()

# --- 今日進度報告 ---
# 篩選出今天的資料
df['時間'] = pd.to_datetime(df['時間'])
today_df = df[df['時間'].dt.date == datetime.now().date()]

if not today_df.empty:
    total_p = today_df["蛋白質"].sum()
    total_c = today_df["金額"].sum()
    
    st.write("---")
    st.write(f"### 📊 今日統計 ({datetime.now().date()})")
    st.progress(min(total_p / TARGET_P, 1.0))
    st.metric("今日總蛋白質", f"{total_p} g", f"{round(total_p - TARGET_P, 1)} g")
    st.metric("今日總金額", f"{total_c} 元")
    st.table(today_df[["時間", "項目", "蛋白質", "金額"]])
else:
    st.info("今日尚無雲端紀錄。")
