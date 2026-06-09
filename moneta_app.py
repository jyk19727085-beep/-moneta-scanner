import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타 퀀트 스캐너 - 철벽 방어 모드")

# 1. 서버 통신 함수 (오류 시 무조건 빈 결과 반환)
def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=20)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and data['OutBlock_1']:
                return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

# 2. 사이드바
with st.sidebar:
    api_key = st.text_input("🔑 API 키", type="password")
    basDd = st.text_input("날짜(YYYYMMDD)", datetime.now().strftime("%Y%m%d"))

# 3. 데이터 분석 엔진
if st.button("🚀 스캐닝 강제 실행"):
    if not api_key: st.error("API 키 입력 필수")
    else:
        # 데이터 수신
        st.write("📡 데이터 수신 중...")
        df1 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        df = pd.concat([df1, df2], ignore_index=True) if not (df1.empty and df2.empty) else pd.DataFrame()
        
        if df.empty:
            st.error("⚠️ 데이터가 없습니다. (휴장일이거나 서버 접속 제한)")
        else:
            # 4. 정밀 데이터 정제 (KeyError 완벽 방어)
            cols_needed = {'ISU_NM':'종목명', 'TDD_CLSPRC':'종가', 'TDD_OPNPRC':'시가', 'ACC_TRDVOL':'거래량', 'FLT_RT':'등락률'}
            df = df.rename(columns={k: v for k, v in cols_needed.items() if k in df.columns})
            
            # 숫자 데이터만 골라냄
            for c in ['종가', '시가', '거래량', '등락률']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # 5. 최종 필터 (조건 만족 종목만 표출)
            if '거래량' in df.columns:
                res = df[
                    (df['거래량'] >= 1000000) & 
                    (df['종가'] > df['시가']) & 
                    (df['등락률'].between(2.0, 8.0)) & 
                    (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
                ]
                
                if not res.empty:
                    st.success(f"✅ 포착된 종목: {len(res)}개")
                    st.table(res[['종목명', '종가', '등락률', '거래량']])
                else:
                    st.info("💡 오늘 장 조건 부합 종목 없음")
