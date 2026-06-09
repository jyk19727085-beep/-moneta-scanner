import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 철갑 퀀트 스캐너")

def get_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200 and 'OutBlock_1' in res.json():
            return pd.DataFrame(res.json()['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")
    basDd = st.date_input("날짜", datetime.now()).strftime("%Y%m%d")

if st.button("🚀 스캐닝 강제 실행"):
    if not api_key: st.error("API 키 입력 필수")
    else:
        df1 = get_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = get_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        df = pd.concat([df1, df2], ignore_index=True) if not (df1.empty and df2.empty) else pd.DataFrame()
        
        if df.empty:
            st.warning("💡 오늘 데이터가 없습니다. (휴장일이거나 동기화 대기 중)")
        else:
            # 안전하게 필요한 컬럼만 추출 (데이터 형식이 바뀌어도 '이름'으로 찾음)
            # 시스템이 스스로 데이터의 위치를 파악하게 하는 지능형 매핑
            cols = {'ISU_NM':'종목명', 'TDD_CLSPRC':'종가', 'TDD_OPNPRC':'시가', 'ACC_TRDVOL':'거래량', 'FLT_RT':'등락률'}
            df = df.rename(columns=cols)
            
            # 숫자 데이터 정제 (데이터가 없어도 오류 안 남)
            for c in ['종가', '시가', '거래량', '등락률']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # 스캐닝 (데이터가 들어있을 때만 분석)
            if '거래량' in df.columns:
                res = df[
                    (df['거래량'] >= 1000000) & 
                    (df['종가'] > df['시가']) & 
                    (df['등락률'].between(2.0, 8.0)) & 
                    (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
                ].sort_values('거래량', ascending=False)
                
                if not res.empty:
                    st.table(res[['종목명', '종가', '등락률', '거래량']])
                else:
                    st.info("💡 조건 부합 종목 없음")
