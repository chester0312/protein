import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 頁面基本設定
st.set_page_config(page_title="蛋白質與開銷雲端看板", layout="centered")

# 2. 建立 Google Sheets 連線
# 請確保在 Streamlit Secrets 中設定了 [connections.gsheets] spreadsheet = "你的網址"
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 讀取資料 (使用 ttl=0 確保每次都是抓取雲端最新資料)
try:
    df_logs = conn.read(worksheet="Logs", ttl=0).dropna(how='all')
    df_foods = conn.read(worksheet="MyFoods", ttl=0).dropna(how='all')
except Exception as e:
    st.error(f"雲端連線或工作表名稱錯誤：{e}")
    df_logs = pd.DataFrame(columns=["時間", "項目", "蛋白質", "金額"])
    df_foods = pd.DataFrame(columns=["組合名稱", "蛋白質", "金額"])

# --- 第一區：快速記錄按鈕 (從 MyFoods 讀取) ---
st.subheader("⚡ 我的常用組合")
if not df_foods.empty:
    cols = st.columns(3)
    for i, row in df_foods.iterrows():
        name = row['組合名稱']
        p_val = float(row['蛋白質'])
        c_val = int(row['金額'])
        
        with cols[i % 3]:
            # 使用 key 避免按鈕 ID 重複
            if st.button(f"{name}\n{p_val}g / ${c_val}", key=f"btn_{i}"):
                new_entry = pd.DataFrame([{
                    "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "項目": name,
                    "蛋白質": p_val,
                    "金額": c_val
                }])
                # 合併舊資料與新紀錄並上傳
                updated_logs = pd.concat([df_logs, new_entry], ignore_index=True)
                conn.update(worksheet="Logs", data=updated_logs)
                st.success(f"✅ 已紀錄：{name}")
                st.rerun()
else:
    st.info("目前沒有自定義組合。請利用側邊欄建立常用的食物（如：乳清、雞胸肉組合）。")

# --- 第二區：今日統計報告 ---
# 確保時間欄位是 datetime 格式以便篩選
if not df_logs.empty:
    df_logs['時間'] = pd.to_datetime(df_logs['時間'])
    today_df = df_logs[df_logs['時間'].dt.date == datetime.now().date()]
else:
    today_df = pd.DataFrame()

st.divider()
if not today_df.empty:
    total_p = today_df["蛋白質"].sum()
    total_c = today_df["金額"].sum()
    
    st.subheader(f"📊 今日統計 ({datetime.now().strftime('%m/%d')})")
    
    # 進度條與指標
    progress_val = min(total_p / TARGET_P, 1.0)
    st.progress(progress_val)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("今日蛋白質", f"{total_p} g")
    m2.metric("剩餘目標", f"{max(0.0, round(TARGET_P - total_p, 1))} g")
    m3.metric("累計金額", f"{total_c} 元")
    
    with st.expander("查看今日明細"):
        st.table(today_df[["項目", "蛋白質", "金額"]])
else:
    st.warning("今日尚未有任何進食紀錄。")

# --- 第三區：側邊欄 (管理組合 & 彈性輸入) ---
with st.sidebar:
    st.header("⚙️ 功能選單")
    
    # 1. 建立常用組合
    st.write("---")
    st.write("### ➕ 建立常用組合")
    with st.form("add_food", clear_on_submit=True):
        new_name = st.text_input("名稱 (如: 1.25匙乳清)")
        new_p = st.number_input("蛋白質(g)", min_value=0.0, step=0.5)
        new_c = st.number_input("金額(元)", min_value=0, step=1)
        if st.form_submit_button("儲存組合"):
            if new_name:
                food_data = pd.DataFrame([{"組合名稱": new_name, "蛋白質": new_p, "金額": new_c}])
                updated_foods = pd.concat([df_foods, food_data], ignore_index=True)
                conn.update(worksheet="MyFoods", data=updated_foods)
                st.success("組合已存入雲端！")
                st.rerun()
                
    # 2. 自由輸入 (單次性)
    st.write("---")
    st.write("### ✍️ 單次臨時紀錄")
    with st.form("temp_input", clear_on_submit=True):
        t_name = st.text_input("食物名稱")
        t_p = st.number_input("蛋白質", min_value=0.0)
        t_c = st.number_input("金額", min_value=0)
        if st.form_submit_button("新增單次紀錄"):
            temp_entry = pd.DataFrame([{
                "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "項目": t_name,
                "蛋白質": t_p,
                "金額": t_c
            }])
            updated_logs = pd.concat([df_logs, temp_entry], ignore_index=True)
            conn.update(worksheet="Logs", data=updated_logs)
            st.rerun()
# --- 側邊欄：個人狀態設定 ---
with st.sidebar:
    st.header("👤 個人狀態設定")
    
    # 讓你可以隨時調整體重與倍數
    current_weight = st.number_input("目前體重 (kg)", min_value=30.0, max_value=150.0, value=67.0, step=0.1)
    protein_factor = st.slider("蛋白質倍數 (體重 x ?)", min_value=1.0, max_value=2.5, value=1.5, step=0.1)
    
    # 自動計算新的目標
    TARGET_P = round(current_weight * protein_factor, 1)
    
    st.info(f"📊 目前目標設定：{TARGET_P} g")
    st.write("---")

st.title("💪 蛋白質 & 預算雲端紀錄")
st.write(f"當前目標：{TARGET_P}g (67kg * 1.5倍)")

    # 3. 刪除功能
    st.write("---")
    if st.button("🗑️ 清空所有常用組合"):
        conn.update(worksheet="MyFoods", data=pd.DataFrame(columns=["組合名稱", "蛋白質", "金額"]))
        st.rerun()
