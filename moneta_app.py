import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 매크로 및 주도주 통합 스캐너")
st.markdown("---")

def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200 and 'OutBlock_1' in res.json():
            return pd.DataFrame(res.json()['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("KRX API 인증키:", type="password")
    basDd = st.date_input("분석 기준일", datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

if st.button("🚀 전체 시스템 가동", type="primary", use_container_width=True):
    if not api_key: st.error("인증키를 입력하십시오.")
    else:
        # 1. 채권 데이터 연동 (국고채 일별 거래)
        st.subheader("🌐 채권 시장 동향 (국고채)")
        bond_df = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/bnd/ktb_dd_trd", api_key, basDd)
        if not bond_df.empty:
            st.success("✅ 채권 데이터 수신 완료")
            st.write(bond_df.head(3))
        else:
            st.warning("⚠️ 채권 데이터 수신 불가 (서버 동기화 확인)")

        # 2. 주도주 스캐닝
        st.subheader("🎯 개별 기업 주도주 스캐너")
        df1 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        if df1.empty and df2.empty:
            st.error("⚠️ 거래소 서버 응답 없음.")
        else:
            df = pd.concat([d for d in [df1, df2] if not d.empty], ignore_index=True)
            # 이름 강제 매핑 및 데이터 정제
            col_map = {'ISU_SRT_CD':'코드', 'ISU_NM':'종목명', 'TDD_CLSPRC':'종가', 'TDD_OPNPRC':'시가', 'ACC_TRDVOL':'거래량', 'FLT_RT':'등락률'}
            df = df.rename(columns=col_map)
            
            for c in ['종가', '시가', '거래량', '등락률']:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # Daniel 주인님의 5대 절대 규칙 적용
            rule = (df['거래량'] >= 1000000) & (df['종가'] > df['시가']) & (df['등락률'].between(2.0, 8.0)) & (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
            res = df[rule].sort_values('거래량', ascending=False).head(15)
            
            if not res.empty:
                show_df = res[['코드', '종목명', '종가', '등락률', '거래량']].copy()
                show_df.index = range(1, len(show_df)+1)
                st.table(show_df)
            else:
                st.info("💡 오늘 검색 조건(거래량 100만주 이상, 양봉 반전 등)에 맞는 개별 주식이 없습니다.")
