import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 퀀트 스캐너")

# 안전한 데이터 호출 모듈
def get_safe_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data: return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")

if st.button("🚀 최종 시스템 가동"):
    if not api_key: st.error("인증키를 입력하세요.")
    else:
        st.subheader("데이터 수신 상태")
        # 테스트용 데이터 호출
        df = get_safe_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, datetime.now().strftime("%Y%m%d"))
        
        if df.empty:
            st.warning("⚠️ [데이터 동기화 대기 중] 거래소 서버에 권한이 완전히 등록되는 중입니다. 내일 다시 시도하십시오.")
        else:
            st.success("✅ 데이터 수신 성공! 분석을 시작합니다.")
            # 분석 로직 시작
            try:
                # 숫자형 변환 안전 장치 추가
                df['TDD_CLSPRC'] = pd.to_numeric(df['TDD_CLSPRC'].str.replace(',',''), errors='coerce')
                st.dataframe(df.head(10))
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}. 데이터 형식을 확인 중입니다.")
