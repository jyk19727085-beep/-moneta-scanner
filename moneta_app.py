import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 철갑 퀀트 스캐너")

# 데이터를 안전하게 불러오는 최후의 보루 함수
def get_safe_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and data['OutBlock_1']:
                return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    api_key = st.text_input("🔑 API 키:", type="password")
    basDd = st.date_input("날짜", datetime.now()).strftime("%Y%m%d")

if st.button("🚀 스캐닝 강제 실행"):
    if not api_key: st.error("API 키 입력 필수")
    else:
        # 1. 채권 데이터
        bond = get_safe_data("http://data-dbg.krx.co.kr/svc/apis/bnd/ktb_dd_trd", api_key, basDd)
        st.subheader("🌐 채권 지표")
        if not bond.empty: st.write(bond.head(1))
        else: st.info("채권 데이터 없음")

        # 2. 주식 데이터
        st.subheader("🎯 주도주 스캐닝")
        df_k1 = get_safe_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df_k2 = get_safe_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        df = pd.concat([d for d in [df_k1, df_k2] if not d.empty], ignore_index=True)
        
        if df.empty:
            st.warning("⚠️ 종목 데이터가 없습니다.")
        else:
            # 컬럼 이름이 달라도 작동하도록 '유사 이름'을 찾아 변환하는 스마트 로직
            rename_dict = {
                'ISU_SRT_CD': '종목코드', 'ISU_NM': '종목명',
                'TDD_CLSPRC': '종가', 'TDD_OPNPRC': '시가',
                'ACC_TRDVOL': '거래량', 'FLT_RT': '등락률'
            }
            df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
            
            # 숫자형 변환 (에러 시 0)
            for c in ['종가', '시가', '거래량', '등락률']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # 필터 적용 (데이터가 있는 컬럼만 사용하여 안전하게)
            if '거래량' in df.columns and '종가' in df.columns:
                res = df[
                    (df['거래량'] >= 1000000) & 
                    (df['종가'] > df['시가']) & 
                    (df['등락률'].between(2.0, 8.0))
                ].sort_values('거래량', ascending=False)
                
                if not res.empty:
                    res.index = range(1, len(res)+1)
                    st.table(res[['종목코드', '종목명', '종가', '등락률', '거래량']])
                else:
                    st.info("💡 조건 맞는 종목 없음")
            else:
                st.error("⚠️ 데이터 구조 분석 실패")
