import streamlit as st
import requests

st.title("🛡️ KRX API 상태 진단 툴")
api_key = st.text_input("🔑 인증키 입력", type="password")

if st.button("🚀 최종 진단"):
    # 실제 데이터 운영 서버 주소
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    # 주식 시세 데이터 호출을 위한 필수 파라미터 (일반적인 형식)
    params = {
        "mktId": "STK",
        "trdDd": "20260604",
        "share": "1",
        "csvxls_is": "false"
    }
    
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key.strip()}, params=params)
        st.write("응답 상태:", res.status_code)
        st.write("응답 전문:", res.text)
    except Exception as e:
        st.error(f"연결 오류: {e}")
