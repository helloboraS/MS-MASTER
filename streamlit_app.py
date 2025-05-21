import streamlit as st
import pandas as pd
from io import BytesIO

# --- Load and merge master data ---
@st.cache_data
def load_master_data():
    master = pd.read_excel('master_data.xlsx')
    model = pd.read_excel('model_master.xlsx')
    merged = pd.merge(master, model, on='모델명', how='left')
    return merged

master_df = load_master_data()

# --- App Title ---
st.set_page_config(layout="wide")
st.title('자재코드 인증정보 자동 병합')

# --- 수기 입력 기능 ---
st.subheader("🔧 수기 입력")
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = []

with st.form("manual_entry_form"):
    cols = st.columns([2, 1, 1, 1, 1])  # 비율 조정해서 더 넓게
    with cols[0]:
        manual_part = st.text_input("자재코드", key="part")
    with cols[1]:
        manual_qty = st.number_input("수량", min_value=0, step=1, key="qty")
    with cols[2]:
        manual_price = st.number_input("단가", min_value=0.0, step=10.0, key="price")
    with cols[3]:
        manual_amount = st.number_input("총금액", value=0.0, step=10.0, key="amount")
    with cols[4]:
        manual_origin = st.text_input("원산지", key="origin")

    submitted = st.form_submit_button("추가")

    if submitted:
        st.session_state.manual_data.append({
            "자재코드": manual_part,
            "수량": manual_qty,
            "단가": manual_price,
            "총금액": manual_amount,
            "원산지": manual_origin
        })
        st.success("수기 항목이 추가되었습니다.")

if st.session_state.manual_data:
    df_manual = pd.DataFrame(st.session_state.manual_data)
    st.dataframe(df_manual)

    if st.button("수기 입력 전체 삭제"):
        st.session_state.manual_data = []
        st.success("수기 입력 항목이 초기화되었습니다.")

    towrite_manual = BytesIO()
    df_manual.to_excel(towrite_manual, index=False, engine='openpyxl')
    towrite_manual.seek(0)
    st.download_button("수기입력 다운로드", towrite_manual, file_name="manual_input.xlsx")