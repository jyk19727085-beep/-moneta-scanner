import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📊 모네타 퀀트 시스템 (오류 원천 차단판)")

def fetch_safe(url, key, date):
    try:
        res = requests.get(url, headers={"AUTH_KEY": key}, params={"basDd": date}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and data['OutBlock_1']:
                return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return None # 에러 시 None 반환

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", datetime.now().strftime("%Y%m%d"))

if st.button("🚀 스캐닝 가동"):
    if not api_key: st.error("API 키 입력 필수")
    else:
        # 데이터 수신
        st.write("📡 데이터 수신 중...")
        df1 = fetch_safe("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = fetch_safe("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        # NoneType 오류 방지: 데이터가 있는 것만 리스트에 추가
        data_list = [d for d in [df1, df2] if d is not None and not d.empty]
        
        if not data_list:
            st.error("⚠️ 데이터가 없습니다. (휴장일이거나 서버 오류)")
        else:
            df = pd.concat(data_list, ignore_index=True)
            # 이름 매핑 및 정제
            df = df.rename(columns={'ISU_NM':'종목명', 'TDD_CLSPRC':'종가', 'TDD_OPNPRC':'시가', 'ACC_TRDVOL':'거래량', 'FLT_RT':'등락률'})
            
            # 숫자 데이터만 골라내기
            for c in ['종가', '시가', '거래량', '등락률']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # 필터링
            res = df[
                (df['거래량'] >= 1000000) & 
                (df['종가'] > df['시가']) & 
                (df['등락률'].between(2.0, 8.0)) & 
                (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
            ]
            
            if not res.empty:
                st.success(f"✅ 포착 종목: {len(res)}개")
                st.table(res[['종목명', '종가', '등락률', '거래량']])
            else:
                st.info("💡 오늘 검색 결과 없음.")
