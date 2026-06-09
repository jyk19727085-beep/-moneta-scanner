import streamlit as st
import requests

st.title("📊 모네타 최후의 연결 테스트")

api_key = st.text_input("🔑 API 인증키", type="password")
basDd = st.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기"):
    # 거래소 API 표준 호출 URL (운영 서버)
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    
    # 필수 파라미터 재설정 (표준 양식)
    params = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501", 
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    
    try:
        # 호출
        res = requests.get(url, headers={"AUTH_KEY": api_key.strip()}, params=params, timeout=15)
        st.write("응답 상태 코드:", res.status_code)
        st.write("응답 내용:", res.text[:1000]) # 결과의 앞부분 1000자만 출력
    except Exception as e:
        st.error(f"오류: {e}")
