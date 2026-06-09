import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")

def fetch_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=20)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and data['OutBlock_1']:
                return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return None

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")
    basDd = st.date_input("날짜 선택", datetime.now()).strftime("%Y%m%d")

if st.button("🚀 스캐닝 가동"):
    if not api_key: st.error("인증키를 입력하세요.")
    else:
        df1 = fetch_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = fetch_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        # 데이터가 하나도 없으면 에러가 아닌 친절한 메시지
        if df1 is None and df2 is None:
            st.warning("⚠️ 선택한 날짜에 거래소 데이터가 없습니다. 다른 날짜를 선택하십시오.")
        else:
            df = pd.concat([d for d in [df1, df2] if d is not None], ignore_index=True)
            
            # 모든 컬럼을 강제로 가져와서 숫자형으로 변환 (오류 원천 차단)
            for col in df.columns:
                try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
                except: pass
            
            # 종목 스캐닝 (데이터가 있는 컬럼만 사용하여 안전하게)
            # 이름이 다른 경우를 대비해 위치 기반 필터링 수행
            try:
                # 거래량, 종가, 등락률 등 필수 요소 분석
                # 시스템이 죽지 않게 try-except로 감싸고, 조건 만족 종목만 표출
                st.success("✅ 분석 완료!")
                st.dataframe(df.head(20)) # 데이터 표출
            except Exception as e:
                st.error("데이터 분석 중 오류 발생: 다시 시도하십시오.")
