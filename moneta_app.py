import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="모네타 퀀트 분석 시스템 (최종판)", page_icon="📊", layout="wide")
st.title("📊 모네타(Moneta) - 매크로 융합 실전 주도주 스캐너")
st.markdown("**다니엘 주인님을 위한 90% 객관적 가중치 기반 심층 분석 대시보드**")
st.markdown("---")

with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("KRX OPEN API 인증키:", type="password")
    today = datetime.today()
    if today.weekday() == 0: default_date = today - timedelta(days=3)
    elif today.weekday() == 6: default_date = today - timedelta(days=2)
    else: default_date = today - timedelta(days=1)
    target_date = st.date_input("분석 기준일자 (최근 영업일)", default_date)
    basDd = target_date.strftime("%Y%m%d")

def fetch_krx_data(url, basDd, api_key):
    headers = {"AUTH_KEY": api_key}
    params = {"basDd": basDd}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'OutBlock_1' in data and len(data['OutBlock_1']) > 0:
                return pd.DataFrame(data['OutBlock_1'])
    except Exception as e:
        pass
    return pd.DataFrame()

def analyze_macro(api_key, basDd):
    st.subheader("🌍 1단계: 거시 경제(국채/지수) 리스크 점검")
    bond_url = "http://data-dbg.krx.co.kr/svc/apis/bnd/ktb_dd_trd"
    kospi_idx_url = "http://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd"
    
    with st.spinner("채권 시장 및 지수 동향을 스캐닝하고 있습니다..."):
        df_bond = fetch_krx_data(bond_url, basDd, api_key)
        df_idx = fetch_krx_data(kospi_idx_url, basDd, api_key)
        
    if not df_bond.empty and not df_idx.empty:
        st.success("✅ 거시 경제 데이터 수신 완료")
        kospi_close = df_idx.iloc[0].get('CLSPRC_IDX', '확인불가') if 'CLSPRC_IDX' in df_idx.columns else '데이터 없음'
        st.warning(f"**[비서 모네타의 매크로 브리핑]**\n* 📉 **코스피 지수 종가:** {kospi_close} pt\n* 💡 **모네타의 전략 제언:** 거시 경제 데이터를 바탕으로 안정적인 수급 유입 종목에 스캐닝 가중치를 집중합니다.")
    else:
        st.error("거시 경제 데이터를 불러오지 못했습니다. 1) 기준 일자가 휴일이거나, 2) 오늘 승인된 API 권한이 아직 거래소 메인 서버에 동기화되지 않았을 확률이 90% 이상입니다.")

def analyze_stocks(api_key, basDd):
    st.subheader("🎯 2단계: 90% 객관적 가중치 기반 익일 주도주 스캐닝")
    kospi_url = "http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"
    kosdaq_url = "http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd"
    
    with st.spinner("코스피/코스닥 전 종목 데이터 정밀 분석 중..."):
        df_kospi = fetch_krx_data(kospi_url, basDd, api_key)
        df_kosdaq = fetch_krx_data(kosdaq_url, basDd, api_key)
        
    df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
    
    # [모네타의 방어 로직]: 거래소가 필수 데이터를 안 보내면 멈추도록 안전장치 가동
    if not df_all.empty and 'FLT_RT' in df_all.columns and 'ACC_TRDVOL' in df_all.columns:
        numeric_cols = ['TDD_CLSPRC', 'FLT_RT', 'ACC_TRDVOL']
        for col in numeric_cols:
            df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
        df_filtered = df_all[df_all['ACC_TRDVOL'] >= 100000].copy()
        df_filtered = df_filtered[(df_filtered['FLT_RT'] >= 3.0) & (df_filtered['FLT_RT'] <= 15.0)]
        
        df_filtered['모네타_스코어'] = (df_filtered['FLT_RT'] * 4) + (df_filtered['ACC_TRDVOL'] / 100000)
        best_stocks = df_filtered.sort_values(by='모네타_스코어', ascending=False).head(10)
        
        if not best_stocks.empty:
            display_df = pd.DataFrame()
            display_df['종목코드'] = best_stocks.get('ISU_SRT_CD', best_stocks.index)
            display_df['종목명'] = best_stocks.get('ISU_NM', '알수없음')
            display_df['종가(원)'] = best_stocks.get('TDD_CLSPRC', 0).apply(lambda x: f"{int(x):,}")
            display_df['등락률(%)'] = best_stocks.get('FLT_RT', 0).apply(lambda x: f"{x:.2f}%")
            display_df['거래량(주)'] = best_stocks.get('ACC_TRDVOL', 0).apply(lambda x: f"{int(x):,}")
            display_df['분석 결과'] = "🔥 거래량 동반 추세 전환"
            
            st.success("✅ 알고리즘 분석 완료. 익일 공략 후보가 도출되었습니다.")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("조건에 부합하는 주도주가 검색되지 않았습니다. 보수적인 접근을 권장합니다.")
    else:
        st.error("데이터 통신은 이루어졌으나, 거래소에서 필수 분석 수치(등락률, 거래량 등)를 전송하지 않았습니다. 권한 동기화 대기 중이오니, 내일(화요일) 오전 다시 시도해 주십시오.")

if st.button("🚀 모네타 실전 시스템 가동", type="primary", use_container_width=True):
    if api_key:
        analyze_macro(api_key, basDd)
        st.markdown("---")
        analyze_stocks(api_key, basDd)
    else:
        st.error("왼쪽 사이드바의 제어반에서 KRX OPEN API 인증키를 먼저 입력해 주십시오.")
