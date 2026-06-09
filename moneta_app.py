import streamlit as st
import requests
import pandas as pd

st.title("🛡️ 모네타: 최종 안정화 레이더")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 호출 시작"):
    if not api_key:
        st.error("API 키를 입력하세요.")
    else:
        # 거래소의 가장 표준적이고 최신 운영 서버 경로
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # 가장 기초적인 시세 호출 파라미터
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            # 404를 방지하기 위해 세션 유지 및 정확한 헤더 설정
            headers = {"AUTH_KEY": api_key.strip()}
            res = requests.post(url, headers=headers, data=params)
            
            if res.status_code == 200:
                data = res.json()
                st.success("✅ 통신 성공!")
                st.write(data)
            else:
                st.error(f"오류 발생: {res.status_code} - 주소가 잘못되었거나 서버가 응답하지 않습니다.")
        except Exception as e:
            st.error(f"시스템 오류: {e}")
