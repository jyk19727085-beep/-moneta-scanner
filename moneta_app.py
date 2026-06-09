import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 모네타: 최종 표준 통신 스캐너")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 정밀 호출"):
    # KRX 공식 운영 서버 URL
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    
    # 퀀트 레이더 표준 데이터 블록 (MDCSTAT01501: 주식 시세)
    # 파라미터 누락 방지를 위해 필수값들을 모두 명시했습니다.
    params = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId": "ALL",
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    
    headers = {"AUTH_KEY": api_key.strip()}
    
    try:
        # GET 방식이 아닌, 거래소 가이드에 따라 명시적 전송
        res = requests.post(url, headers=headers, data=params)
        data = res.json()
        
        if 'OutBlock_1' in data:
            st.success(f"✅ 데이터 수신 성공! {len(data['OutBlock_1'])}개 종목")
            df = pd.DataFrame(data['OutBlock_1'])
            st.dataframe(df.head(10))
        else:
            st.error("데이터 없음. 서버 응답 결과:")
            st.write(data)
            
    except Exception as e:
        st.error(f"코드 오류: {e}")
