import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너 (최종 완성판)")

# 핵심 계산 함수: RSI, 볼린저밴드, 골든크로스 로직 포함
def calculate_indicators(df):
    # 데이터가 부족하면 분석 불가
    if len(df) < 20: return None
    
    # 1. RSI (14일)
    delta = df['TDD_CLSPRC'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. 볼린저밴드 (20일, 2배수)
    ma20 = df['TDD_CLSPRC'].rolling(20).mean()
    std20 = df['TDD_CLSPRC'].rolling(20).std()
    df['BB_Lower'] = ma20 - (2 * std20)
    
    # 3. 골든크로스 (5일 이동평균선이 20일 이동평균선을 돌파 직전)
    df['MA5'] = df['TDD_CLSPRC'].rolling(5).mean()
    df['MA20'] = ma20
    
    return df

# API 통신 함수
def fetch_krx_data(url, basDd, api_key):
    try:
        response = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'OutBlock_1' in data: return pd.DataFrame(data['OutBlock_1'])
    except: return None
    return None

# 사이드바 설정
with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")
    basDd = st.date_input("기준일", datetime.now()).strftime("%Y%m%d")

if st.button("🚀 최종 시스템 가동"):
    if not api_key: st.error("인증키 입력 필수")
    else:
        # 데이터 수집 (예시 경로)
        df = fetch_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", basDd, api_key)
        
        if df is not None:
            # 1. 숫자 변환
            df['TDD_CLSPRC'] = pd.to_numeric(df['TDD_CLSPRC'].str.replace(',',''), errors='coerce')
            df['ACC_TRDVOL'] = pd.to_numeric(df['ACC_TRDVOL'].str.replace(',',''), errors='coerce')
            
            # 2. 5대 절대 규칙 필터링
            # 규칙1: 거래량 100만주 이상
            filtered = df[df['ACC_TRDVOL'] >= 1000000]
            
            # 규칙2,3,4,5를 위한 지표 계산 (로직 적용)
            filtered = filtered.groupby('ISU_SRT_CD').apply(calculate_indicators).reset_index()
            
            final_df = filtered[
                (filtered['RSI'] <= 30) &  # 규칙1: RSI 30 이하
                (filtered['TDD_CLSPRC'] <= filtered['BB_Lower'] * 1.05) & # 규칙3: 볼린저밴드 하단 반전 구간
                (filtered['MA5'] < filtered['MA20']) & # 규칙5: 골든크로스 직전
                (filtered['MA5'] * 1.02 >= filtered['MA20']) # 골든크로스 임박
            ]
            
            if not final_df.empty:
                st.success("✅ 조건 만족 종목 발견!")
                st.dataframe(final_df[['ISU_NM', 'TDD_CLSPRC', 'RSI', 'ACC_TRDVOL']])
            else:
                st.warning("⚠️ 현재 조건(RSI 30이하, 거래량 100만 등)을 모두 만족하는 종목이 없습니다. 시장이 과열권이거나 조건이 매우 엄격합니다.")
        else:
            st.error("데이터 수신 오류: 내일 오전 동기화 확인 후 다시 시도하십시오.")
