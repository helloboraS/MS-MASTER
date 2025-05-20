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
st.title('자재코드 인증정보 자동 병합')

# --- 엑셀 업로드 ---
uploaded_file = st.file_uploader("자재코드, 수량, 원산지, 단가, 총금액 포함된 엑셀 업로드", type=["xlsx"])

if uploaded_file:
    try:
        input_df = pd.read_excel(uploaded_file)

        if '자재코드' not in input_df.columns:
            st.error("'자재코드' 컬럼이 엑셀에 포함되어 있어야 합니다.")
        else:
            # 병합 수행
            merged_result = pd.merge(input_df, master_df, on='자재코드', how='left')

            # 필요한 컬럼 순서로 재정렬 (Sheet 1)
            columns_to_show = [
                '자재코드', 'HS CODE', '모델규격', '모델명',
                '전파인증번호', '전기기관', '전기인증번호', '정격전압',
                '원산지', '수량', '단가', '총금액'
            ]
            filtered_result = merged_result[[col for col in columns_to_show if col in merged_result.columns]]

            st.success('병합 완료! 아래에서 결과 확인 가능')
            st.dataframe(filtered_result)

            # 두 번째 시트: 전파 인증 요약
            radio_df = merged_result.dropna(subset=['전파인증번호'])
            radio_summary = radio_df.groupby([
                '세번부호' if '세번부호' in radio_df.columns else 'HS CODE',
                '원산지', '모델명', '전파인증번호'
            ], as_index=False)['수량'].sum()

            # 세 번째 시트: 전기 인증 요약
            elec_df = merged_result.dropna(subset=['전기인증번호'])
            elec_summary = elec_df.groupby([
                '전기기관',
                '세번부호' if '세번부호' in elec_df.columns else 'HS CODE',
                '원산지', '모델명', '전기인증번호', '정격전압'
            ], as_index=False)['수량'].sum()

            # 네 번째 시트: 커스터마이징 시트
            summary_sheet4 = merged_result.copy()
            summary_sheet4['공란'] = ''
            summary_sheet4['수량단위'] = 'EA'
            sheet4_columns = [
                'HS CODE', '원산지', '공란', '수량', '수량단위', '단가', '총금액', '자재코드'
            ]
            sheet4_result = summary_sheet4[[col for col in sheet4_columns if col in summary_sheet4.columns]]

            # 다운로드용 엑셀 생성 (4시트)
            towrite = BytesIO()
            with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                filtered_result.to_excel(writer, sheet_name='전체리스트', index=False)
                radio_summary.to_excel(writer, sheet_name='전파인증 요약', index=False)
                elec_summary.to_excel(writer, sheet_name='전기인증 요약', index=False)
                sheet4_result.to_excel(writer, sheet_name='수입신고용', index=False)
            towrite.seek(0)

            st.download_button(
                label='엑셀로 다운로드 (4시트 포함)',
                data=towrite,
                file_name='merged_result_with_cert.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    except Exception as e:
        st.error(f"엑셀 처리 중 오류 발생: {e}")
else:
    st.info("먼저 자재코드 포함된 엑셀을 업로드해 주세요.")