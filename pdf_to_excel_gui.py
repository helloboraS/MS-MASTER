import streamlit as st
import pandas as pd
import pdfplumber
import tempfile
import os

def extract_format_a(pdf_path):
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")
            for line in lines:
                parts = line.split()
                if len(parts) >= 12 and parts[2].isdigit() and parts[-4].isdigit():
                    record = {
                        "PO No": parts[1],
                        "SAP Order No": parts[2],
                        "Part Number": parts[3],
                        "Part Description": " ".join(parts[4:-6]),
                        "Model No": parts[-6],
                        "Country of Origin": parts[-5],
                        "Ship Qty": parts[-4],
                        "Price UOM": parts[-3],
                        "Unit Price": parts[-2],
                        "Extended Price": parts[-1],
                        "HTS Code": "",
                        "HTS Description": ""
                    }
                    records.append(record)
                elif len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                    if records:
                        records[-1]["HTS Code"] = parts[1]
                        records[-1]["HTS Description"] = " ".join(parts[2:])
    return pd.DataFrame(records)

def extract_format_b(pdf_path):
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")
            i = 0
            while i < len(lines) - 1:
                line1 = lines[i].strip().split()
                line2 = lines[i + 1].strip().split()

                if not (line1 and line2):
                    i += 1
                    continue
                try:
                    delivery_no = line1[1]
                    msf_index = next(j for j, p in enumerate(line1) if p.startswith("MSF-"))
                    manufacturer_part_no = " ".join(line1[2:msf_index])
                    msf_index = next(j for j, p in enumerate(line1) if p.startswith("MSF-"))
                    ms_part_no = line1[msf_index]

                    model_no = line2[2] if len(line2) > 2 else "NA"

                    hts_code = line1[msf_index + 2]
                    country = line1[msf_index + 3]
                    ship_qty = line1[msf_index + 4]
                    unit_price = line1[msf_index + 5]
                    price_uom = line1[msf_index + 6]
                    ext_price = line1[msf_index + 7]

                    desc_start_index = 3 if len(line2) > 3 else None
                    desc_raw = " ".join(line2[desc_start_index:]) if desc_start_index else ""
                    desc_clean = desc_raw.replace("NEW NLR", "").strip()

                    record = {
                        "Delivery No.": delivery_no,
                        "Manufacturer Part No.": manufacturer_part_no,
                        "Model No": model_no,
                        "Microsoft Part No.": ms_part_no,
                        "HTS Code": hts_code,
                        "Country of Origin": country,
                        "Ship Qty": ship_qty,
                        "Unit Price": unit_price,
                        "Price UOM": price_uom,
                        "Extended Price": ext_price,
                        "Part Description": desc_clean
                    }
                    records.append(record)
                    i += 2
                except Exception:
                    i += 1
    return pd.DataFrame(records)

st.set_page_config(page_title="MS Helper", layout="wide")
st.title("Microsoft Helper ♥")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📘 MS1056", "📗 MS1279-PAYMENTS", "📒 MS1279-MASTER 비교", "📕 MS1279-WESCO", "📙 HS 코드 비교기"])

with tab1:
    uploaded_files_a = st.file_uploader("MS1056 PDF Upload", type=["pdf"], accept_multiple_files=True, key="a")
    if uploaded_files_a:
        all_data = {}
        for uploaded_file in uploaded_files_a:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_pdf_path = tmp_file.name
            df = extract_format_a(temp_pdf_path)
            os.remove(temp_pdf_path)
            sheet_name = os.path.splitext(uploaded_file.name)[0][:31]
            all_data[sheet_name] = df
            st.subheader(f"{sheet_name}")
            st.dataframe(df)
        if all_data:
            excel_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            with pd.ExcelWriter(excel_file.name, engine="openpyxl") as writer:
                for name, df in all_data.items():
                    df.to_excel(writer, sheet_name=name, index=False)
            with open(excel_file.name, "rb") as f:
                st.download_button(
                    label="📥 MS1056 엑셀 다운로드",
                    data=f,
                    file_name="ms1056_data.xlsx"
                )

with tab2:
    uploaded_files_b = st.file_uploader("MS1279 PDF Upload", type=["pdf"], accept_multiple_files=True, key="b")
    if uploaded_files_b:
        all_data = {}
        for uploaded_file in uploaded_files_b:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_pdf_path = tmp_file.name
            df = extract_format_b(temp_pdf_path)
            os.remove(temp_pdf_path)
            sheet_name = os.path.splitext(uploaded_file.name)[0][:31]
            all_data[sheet_name] = df
            st.subheader(f"{sheet_name}")
            st.dataframe(df)
        if all_data:
            excel_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            with pd.ExcelWriter(excel_file.name, engine="openpyxl") as writer:
                for name, df in all_data.items():
                    df.to_excel(writer, sheet_name=name, index=False)
                merged_df = pd.concat(all_data.values(), ignore_index=True)
                filtered_df = pd.DataFrame({
                    "HS CODE": merged_df["HTS Code"],
                    "DESC + ORIGIN": merged_df.apply(
                        lambda row: row["Part Description"]
                        + (" MODEL: " + row["Model No"] if row["Model No"] != "NA" else "")
                        + " ORIGIN: " + row["Country of Origin"], axis=1),
                    "PART NO.": "PART NO: " + merged_df["Microsoft Part No."] + " (" + merged_df["Manufacturer Part No."] + ")",
                    "Q'TY": merged_df["Ship Qty"],
                    "UOM": merged_df["Price UOM"],
                    "UNIT PRICE": merged_df["Unit Price"],
                    "TOTAL AMOUNT": merged_df["Extended Price"],
                    "PART NO. FULL": merged_df["Microsoft Part No."] + " (" + merged_df["Manufacturer Part No."] + ")",
                    "Model No": merged_df["Model No"]
                })
                filtered_df.to_excel(writer, sheet_name="신고서용", index=False)
            with open(excel_file.name, "rb") as f:
                st.download_button(
                    label="📥 MS1279-PAYMENTS 엑셀 다운로드",
                    data=f,
                    file_name="ms1279_payments_data.xlsx"
                )

with tab3:
    # st.header("📒 마스터 데이터 비교")

    if "master_df" not in st.session_state:
        if not os.path.exists("MASTER_MS5673.xlsx"):
            st.warning("⚠️ MASTER_MS5673.xlsx 파일이 현재 디렉토리에 존재하지 않습니다.")
        if os.path.exists("MASTER_MS5673.xlsx"):
            st.session_state["master_df"] = pd.read_excel("MASTER_MS5673.xlsx")

    uploaded_excel = st.file_uploader("엑셀업로드", type=["xlsx"], key="compare_excel")

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

    if uploaded_excel and master_df is not None:
        input_df = pd.read_excel(uploaded_excel)
        master_df = master_df.rename(columns=lambda x: x.strip())
        input_df = input_df.rename(columns=lambda x: x.strip())
        
        input_df["Microsoft Part No."] = input_df["Microsoft Part No."].astype(str).str.strip()
        master_df["Microsoft Part No."] = master_df["Microsoft Part No."].astype(str).str.strip()
        
        merged = input_df.merge(master_df, how="left", on="Microsoft Part No.")
        merged["INV HS"] = merged["INV HS"].apply(clean_code)
        


        merged["HS Code"] = merged["HS Code"].apply(clean_code).apply(fix_hscode)

        merged["HS10_MATCH"] = merged.apply(lambda row: "O" if row["INV HS"][:10] == row["HS Code"][:10] else "X", axis=1)
        merged["HS6_MATCH"] = merged.apply(lambda row: "O" if row["INV HS"][:6] == row["HS Code"][:6] else "X", axis=1)

        merged["전파"] = merged["전파인증번호"].apply(lambda x: "O" if pd.notna(x) and str(x).strip() else "X")
        merged["전기"] = merged["전기인증번호"].apply(lambda x: "O" if pd.notna(x) and str(x).strip() else "X")

        final_df = merged.copy()

        invoice_sheet = pd.DataFrame({
            "HS Code": final_df["HS Code"],
            "Part Description": final_df["Part Description"] + ' ORIGIN:' + final_df["원산지"],
            "Microsoft Part No.": "PART NO: " + final_df["Microsoft Part No."],
            "수량": final_df["수량"],
            "단위": final_df["단위"],
            "단가": final_df["단가"],
            "금액": final_df["금액"],
            "Microsoft Part No. (원본)": final_df["Microsoft Part No."],  # ← 추가된 열
            "전파": final_df["전파"],
            "전기": final_df["전기"],
            "요건비대상사유": final_df["요건비대상"]
        })

        radio_req = (
            final_df.groupby(["HS Code", "원산지", "모델명", "전파인증번호"], as_index=False)
            .agg({"수량": "sum"})
        )

        safety_req = (
            final_df.groupby(["기관", "HS Code", "원산지", "모델명", "전기인증번호", "정격전압"], as_index=False)
            .agg({"수량": "sum"})
        )

        to_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        with pd.ExcelWriter(to_excel.name, engine="openpyxl") as writer:
            final_df.drop(columns=["무역거래처상호"], errors="ignore").to_excel(writer, index=False, sheet_name="비교결과")
            invoice_sheet.to_excel(writer, index=False, sheet_name="신고서")
            radio_req.to_excel(writer, index=False, sheet_name="전파요건")
            safety_req.to_excel(writer, index=False, sheet_name="전안요건")

        with open(to_excel.name, "rb") as f:
            st.download_button(
                label="📥 비교 결과 엑셀 다운로드",
                data=f,
                file_name="MS5673_신고.xlsx"
            )
    elif master_df is None:
        st.warning("⚠️ 마스터 파일이 없습니다. 최초 1회 업로드가 필요합니다.")



with tab5:
    st.header("📙 Microsoft Part No. & INV HS 비교기")

    input_data = st.text_area("Microsoft Part No. 와 INV HS 입력 (쉼표 또는 탭으로 구분)", height=200,
        placeholder="예: MSF-12345678,3923500000\nMSF-98765432\t8473304090")

    if "master_df" not in st.session_state:
        if os.path.exists("MASTER_MS5673.xlsx"):
            st.session_state["master_df"] = pd.read_excel("MASTER_MS5673.xlsx")
        else:
            st.warning("⚠️ MASTER_MS5673.xlsx 파일이 존재하지 않습니다.")

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
            parts = re.split(r"[,	]", line.strip())
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
