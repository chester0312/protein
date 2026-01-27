import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 初始化資料庫與設定
st.set_page_config(page_title="蛋白質進度追蹤", layout="centered")

# 你的專屬數據
FOOD_DB = {
    "飯糰組合": {"protein": 25, "price": 65},      # 飯糰 + 20g豆漿
    "高蛋豆漿組合": {"protein": 35, "price": 45},  # 蛋 + 35g豆漿
    "蛋餅組合": {"protein": 27, "price": 55},      # 蛋餅 + 20g豆漿
    "午餐兩顆蛋": {"protein": 14, "price": 20},
    "博客雞胸肉": {"protein": 24, "price": 50},    # 6入299方案
    "晚餐便當": {"protein": 30, "price": 100},
    "乳清(1.2匙)": {"protein": 29, "price": 42},   # 1kg/988元
    "乳清(1匙)": {"protein": 24, "price": 35}
}

TARGET_PROTEIN = 100.5  # 67kg * 1.5

# 2. 建立資料儲存
if 'logs' not in st.session_state:
    st.session_state.logs = []

st.title("💪 增肌減脂進度看板")
st.subheader(f"目標：{TARGET_PROTEIN}g 蛋白質 / 日")

# 3. 快速記錄按鈕
st.write("### 快速紀錄今日飲食")
cols = st.columns(3)
for i, (food, data) in enumerate(FOOD_DB.items()):
    with cols[i % 3]:
        if st.button(f"{food}\n({data['protein']}g)"):
            st.session_state.logs.append({
                "時間": datetime.now().strftime("%H:%M"),
                "項目": food,
                "蛋白質": data['protein'],
                "金額": data['price']
            })

# 4. 數據統計
if st.session_state.logs:
    df = pd.DataFrame(st.session_state.logs)
    current_p = df["蛋白質"].sum()
    current_cost = df["金額"].sum()

    # 進度條
    progress = min(current_p / TARGET_PROTEIN, 1.0)
    st.write(f"### 今日進度：{current_p}g / {TARGET_PROTEIN}g")
    st.progress(progress)

    # 數據指標
    c1, c2 = st.columns(2)
    c1.metric("今日總蛋白質", f"{current_p} g")
    c2.metric("今日累計花費", f"{current_cost} 元")

    # 紀錄表格
    with st.expander("查看詳細紀錄"):
        st.table(df)
        if st.button("清除今日紀錄"):
            st.session_state.logs = []
            st.rerun()
else:
    st.info("尚未有今日紀錄，點擊上方按鈕開始！")

# 5. 溫馨提醒 (針對你的生活習慣)
st.sidebar.markdown(f"""
### 💡 執行小提醒
* **今日步數：** 記得走滿 15,000 步喔！
* **訓練叮嚀：** 今晚是運動日嗎？做二休一別忘了。
* **乳清提醒：** 運動後喝乳清效果最好。
""")
