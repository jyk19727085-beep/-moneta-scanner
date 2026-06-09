import streamlit as st
import pandas as pd
import requests

st.title("📊 모네타: 최후의 브라우저 우회 스캐너")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기 가동"):
    if not api_key:
        st.error("API 키 입력 필수")
    else:
        # 거래소 데이터 마켓의 메인 페이지를 거쳐서 진입하는 우회 경로
        # 가장 안정적인 웹 브라우저 헤더 설정
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"
        }
        
        # 데이터를 조회하는 표준 폼 데이터
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            # 세션을 만들어 쿠키를 획득한 후 데이터를 조회
            session = requests.Session()
            session.get("https://data.krx.co.kr/", headers=headers)
            
            # 실제 데이터 호출
            res = session.post("https://data.krx.co.kr/commbldtop/WhlSvc.ctrl", headers=headers, data=payload)
            
            if res.status_code == 200:
                data = res.json()
                st.success("✅ 통신 대성공!")
                st.write(data)
            else:
                st.error(f"서버가 여전히 404 혹은 거부를 합니다: {res.status_code}")
                st.text(res.text[:500])
        except Exception as e:
            st.error(f"시스템 예외: {e}")
