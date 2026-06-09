import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 모네타: 시장 분리 호출 엔진")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

def fetch_market_data(mkt_id):
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    params = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId": mkt_id, # STK(코스피), KSQ(코스닥) 분리 호출
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    res = requests.post(url, headers={"AUTH_KEY": api_key.strip()}, data=params)
    return res.json()

if st.button("🚀 주식 데이터 정밀 호출"):
    if not api_key: st.error("키 입력 필수")
    else:
        st.write("📡 코스피 데이터 호출 중...")
        kospi_data = fetch_market_data("STK")
        st.write("코스피 응답:", kospi_data.get('OutBlock_1', '데이터 없음')[:5])
        
        st.write("📡 코스닥 데이터 호출 중...")
        kosdaq_data = fetch_market_data("KSQ")
        st.write("코스닥 응답:", kosdaq_data.get('OutBlock_1', '데이터 없음')[:5])
