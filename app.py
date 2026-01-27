import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="個人化營養看板", layout="centered")

# 建立 Google Sheets 連線 (建議試算表內建立兩個工作表：Logs 和 MyFoods)
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 讀取數據
# 假設 Logs 存每日紀錄，MyFoods 存你的自定義組合
try:
    df_logs = conn.read(worksheet="Logs")
    df_foods = conn.read(worksheet="MyFoods")
except:
    # 若工作表不存在，建立初始結構
    df_logs = pd.DataFrame(columns=["時間", "項目", "蛋白質", "金額"])
    df_foods = pd.DataFrame(columns=["組合名稱", "蛋白質", "金額"])

TARGET_P = 100.5

st.title("💪 個人化蛋白質紀錄看板")

# --- 第一區：你的自定義快捷鍵 ---
st.write("### ⚡ 你的常用組合")
if not df_foods.empty:
    # 這裡會根據你儲存的資料自動產生按鈕
    cols = st.columns(3)
    for i, row in df_foods.iterrows():
        with cols[i % 3]:
            if st.button(f"{row['組合名稱']}\n({row['蛋白質']}g / ${row['金額']})"):
                new_entry = pd.DataFrame([{
                    "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "項目": row['組合名稱'],
                    "蛋白質": row['蛋白質'],
                    "金額": row['金額']
                }])
                df_logs = pd.concat([df_logs, new_entry], ignore_index=True)
                conn.update(worksheet="Logs", data=df_logs)
                st.success(f"已紀錄：{row['組合名稱']}")
                st.rerun()
else:
    st.info("目前還沒有設定常用組合，請到下方建立。")

# --- 第二區：建立/管理常用組合 ---
with st.sidebar:
    st.header("⚙️ 組合管理")
    with st.form("add_food_form", clear_on_submit=True):
        f_name = st.text_input("設定組合名稱", placeholder="例如：雙蛋大豆漿")
        f_p = st.number_input("蛋白質含量(g)", min_value=0.0)
        f_c = st.number_input("價格", min_value=0)
        if st.form_submit_button("儲存為常用按鈕"):
            if f_name:
                new_food = pd.DataFrame([{"組合名稱": f_name, "蛋白質": f_p, "金額": f_c}])
                df_foods = pd.concat([df_foods, new_food], ignore_index=True)
                conn.update(worksheet="MyFoods", data=df_foods)
                st.success("組合已儲存！")
                st.rerun()
    
    if st.button("清空所有常用組合"):
        conn.update(worksheet="MyFoods", data=pd.DataFrame(columns=["組合名稱", "蛋白質", "金額"]))
        st.rerun()

# --- 第三區：彈性自由輸入 ---
st.write("---")
with st.expander("✍️ 臨時輸入 (不存成按鈕)"):
    with st.form("temp_input", clear_on_submit=True):
        t_name = st.text_input("食物名稱")
        t_p = st.number_input("蛋白質", min_value=0.0)
        t_c = st.number_input("金額", min_value=0)
        if st.form_submit_button("新增單次紀錄"):
            new_entry = pd.DataFrame([{
                "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "項目": t_name,
                "蛋白質": t_p,
                "金額": t_c
            }])
            df_logs = pd.concat([df_logs, new_entry], ignore_index=True)
            conn.update(worksheet="Logs", data=df_logs)
            st.rerun()

# --- 第四區：今日統計報告 ---
# 確保時間欄位格式正確
df_logs['時間'] = pd.to_datetime(df_logs['時間'])
today_df = df_logs[df_logs['時間'].dt.date == datetime.now().date()]

if not today_df.empty:
    total_p = today_df["蛋白質"].sum()
    total_c = today_df["金額"].sum()
    st.write("---")
    st.write(f"### 📊 今日統計 ({datetime.now().date()})")
    st.progress(min(total_p / TARGET_P, 1.0))
    st.metric("今日總蛋白質", f"{total_p} g", f"剩餘 {max(0.0, round(TARGET_P-total_p, 1))} g")
    st.metric("今日總花費", f"{total_c} 元")
    st.table(today_df[["項目", "蛋白質", "金額"]])
