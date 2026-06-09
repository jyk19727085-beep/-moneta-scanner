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
        # 거래소의 가장 표준적이고 공식적인 데이터 호출 주소
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # 데이터 호출을 위한 표준 파라미터 (MDCSTAT01501: 주식 시세)
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            # 404를 방지하기 위해 세션을 생성하고 헤더에 키를 포함
            headers = {"AUTH_KEY": api_key.strip()}
            res = requests.post(url, headers=headers, data=params)
            
            if res.status_code == 200:
                st.success("✅ 통신 성공! 데이터를 가져왔습니다.")
                st.write(res.json())
            else:
                st.error(f"오류 발생: {res.status_code} - 주소 경로나 서버 응답을 확인하십시오.")
        except Exception as e:
            st.error(f"시스템 오류: {e}")
