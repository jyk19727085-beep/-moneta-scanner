import streamlit as st
import pandas as pd
import requests

st.title("📊 모네타 최후의 스캐너")
api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 호출 시작"):
    # 거래소 API 표준 호출 URL (운영 서버)
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    
    # 거래소 시스템이 요구하는 필수 파라미터 규격(표준)
    params = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501", # 코스피 시세용 표준 블록코드
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key.strip()}, params=params)
        data = res.json()
        st.write("응답 코드:", res.status_code)
        st.write("데이터 결과:", data)
    except Exception as e:
        st.error(f"오류: {e}")
