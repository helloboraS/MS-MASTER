
import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="MS Helper", layout="wide")
st.title("Microsoft Helper ♥")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📘 MS1056", 
    "📗 MS1279-PAYMENTS", 
    "📒 MS1279-MASTER 비교", 
    "📕 MS1279-WESCO", 
    "📙 HS 코드 비교기"
])

# 탭5: HS 코드 비교기
with tab5:
    st.header("📙 Microsoft Part No. & INV HS 비교기")

    input_data = st.text_area(
        "Microsoft Part No. 와 INV HS 입력 (쉼표 또는 탭으로 구분)", 
        height=200,
        placeholder="예: MSF-12345678,3923500000\nMSF-98765432\t8473304090"
    )

    # 마스터 파일 불러오기
    if "master_df" not in st.session_state:
        if os.path.exists("MASTER_MS5673.xlsx"):
            st.session_state["master_df"] = pd.read_excel("MASTER_MS5673.xlsx")

    master_df = st.session_state.get("master_df")

    def clean_code(code):
        return str(code).strip().replace("-", "")

    def fix_hscode(code):
        try:
            code_str = str(code)
            if code_str.endswith(".0"):
                code_str = code_str[:-2]
            return code_str.zfill(10)
        except:
            return ""

    if input_data and master_df is not None:
        lines = input_data.strip().split("\n")
        results = []

        for line in lines:
            parts = re.split(r"[,\t]", line.strip())
            if len(parts) < 2:
                continue
            part_no_input = parts[0].strip()
            inv_hs_input = parts[1].strip()
            inv_hs_clean = clean_code(inv_hs_input)

            match = master_df[master_df["Microsoft Part No."].astype(str).str.strip() == part_no_input]

            if not match.empty:
                hs_code_raw = match.iloc[0]["HS Code"]
                hs_code_clean = clean_code(hs_code_raw)
                hs_code_fixed = fix_hscode(hs_code_clean)
                hs6_match = "O" if inv_hs_clean[:6] == hs_code_fixed[:6] else "X"
                hs10_match = "O" if inv_hs_clean[:10] == hs_code_fixed[:10] else "X"
            else:
                hs_code_fixed = "(없음)"
                hs6_match = hs10_match = "X"

            results.append({
                "Microsoft Part No.": part_no_input,
                "입력한 INV HS": inv_hs_clean,
                "MASTER HS Code": hs_code_fixed,
                "6자리 비교": hs6_match,
                "10자리 비교": hs10_match
            })

        result_df = pd.DataFrame(results)
        st.dataframe(result_df)
    elif input_data and master_df is None:
        st.error("⚠️ MASTER_MS5673.xlsx 파일이 업로드되지 않았습니다. 먼저 업로드해주세요.")
