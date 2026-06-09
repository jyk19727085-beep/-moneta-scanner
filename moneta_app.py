import streamlit as st
import pandas as pd
import requests

st.title("📊 모네타 최종 통신 모드")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

# [핵심 수정] 운영 서버 주소로 변경
URL_STOCK = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"

if st.button("🚀 운영 서버 스캐닝 가동"):
    if not api_key: st.error("API 키 입력 필수")
    else:
        try:
            # KRX 운영 서버는 주식/채권 요청 방식이 통일된 경우가 많습니다.
            res = requests.get(URL_STOCK, headers={"AUTH_KEY": api_key.strip()}, params={"basDd": basDd}, timeout=15)
            st.write("응답:", res.text[:500]) # 서버가 뭐라고 하는지 500자까지 출력
        except Exception as e:
            st.error(f"오류: {e}")
