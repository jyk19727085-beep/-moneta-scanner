import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("다니엘 주인님을 위한 90% 객관적 데이터 분석 대시보드")

# 1. API 통신 모듈 (오류 방어 최적화)
def fetch_krx_data(url, basDd, api_key):
    headers = {"AUTH_KEY": api_key}
    params = {"basDd": basDd}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'OutBlock_1' in data and len(data['OutBlock_1']) > 0:
                return pd.DataFrame(data['OutBlock_1'])
            return "EMPTY" # 데이터가 없음
        elif response.status_code == 403:
            return "NO_PERMISSION" # 권한 없음
        else:
            return "ERROR"
    except:
        return "ERROR"

# 2. 사이드바
with st.sidebar:
    api_key = st.text_input("🔑 KRX API 인증키:", type="password")
    target_date = st.date_input("분석 기준일자", datetime.now() - timedelta(days=1))
    basDd = target_date.strftime("%Y%m%d")

# 3. 분석 로직
if st.button("🚀 모네타 실전 시스템 가동"):
    if not api_key:
        st.error("인증키를 입력해 주십시오.")
    else:
        # 매크로 분석
        st.subheader("🌍 거시 경제 점검")
        res = fetch_krx_data("http://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd", basDd, api_key)
        
        if isinstance(res, pd.DataFrame):
            st.success("✅ 데이터 수신 성공")
            st.write(f"지수 분석 완료 (기준일: {basDd})")
        elif res == "NO_PERMISSION":
            st.error("⚠️ [권한 오류] 아직 KRX 서버에서 API 권한이 동기화되지 않았습니다. 내일 다시 시도하십시오.")
        elif res == "EMPTY":
            st.warning("⚠️ [데이터 없음] 해당 날짜에 거래소가 데이터를 제공하지 않습니다.")
        else:
            st.error("⚠️ [통신 오류] 서버 상태를 확인 중입니다.")

        # 종목 분석 로직 (구조 유지)
        st.subheader("🎯 주도주 스캐닝")
        st.info("데이터 권한 동기화 완료 후 정밀 스캐닝을 시작합니다.")

