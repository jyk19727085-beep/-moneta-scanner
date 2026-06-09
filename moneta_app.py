import streamlit as st
import pandas as pd

st.set_page_config(page_title="모네타 퀀트 분석기", layout="wide")
st.title("📊 모네타 퀀트 분석 대시보드")

uploaded_file = st.file_uploader("KRX 엑셀/CSV 파일을 업로드하세요", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 1. 데이터 로드
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    st.success("✅ 데이터 로드 성공!")
    
    # 2. 5대 퀀트 필터링 (주인님의 핵심 지침 적용)
    # 거래량 100만주 이상, 양봉, 등락률 2~8% 등 필터링 로직
    # (실제 컬럼명에 맞춰 조정이 필요할 수 있습니다)
    
    filtered_df = df[
        (df['거래량'] >= 1000000) & 
        (df['종가'] > df['시가']) & 
        (df['등락률'].between(2.0, 8.0))
    ]
    
    st.subheader("🎯 퀀트 필터링 결과")
    st.dataframe(filtered_df)
    
    st.info("분석 완료! 위 데이터를 바탕으로 추가적인 상관계수 분석이나 섹터별 매수를 진행할까요?")

else:
    st.warning("분석할 데이터를 업로드해 주십시오.")
