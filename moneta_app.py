import streamlit as st
import requests

st.title("📊 모네타: 최후의 데이터 해부")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 원본 해부 시작"):
    if not api_key:
        st.error("API 키를 입력하세요.")
    else:
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            # 1. 원본 응답 요청
            res = requests.post(url, headers={"AUTH_KEY": api_key.strip()}, data=params)
            
            st.write("응답 상태 코드:", res.status_code)
            
            # 2. JSON 파싱 전 원본 텍스트 확인 (오류의 핵심)
            st.text("서버가 보내준 원본 메시지(정확히 확인하세요):")
            st.code(res.text[:1000]) # 앞부분 1000자 출력
            
        except Exception as e:
            st.error(f"통신 오류: {e}")
