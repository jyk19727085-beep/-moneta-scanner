import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 불사신 퀀트 스캐너")

# 안전 데이터 호출 모듈
def get_safe_krx(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=20)
        if res.status_code == 200 and 'OutBlock_1' in res.json():
            return pd.DataFrame(res.json()['OutBlock_1'])
    except: pass
    return None

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")
    basDd = st.date_input("분석 날짜", datetime.now()).strftime("%Y%m%d")

if st.button("🚀 최종 가동"):
    if not api_key: st.error("인증키를 입력하세요.")
    else:
        df1 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
        df2 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
        
        # 완전 방어 모드: 데이터가 없으면 분석 포기하고 친절한 안내
        if df1 is None and df2 is None:
            st.error("⚠️ [데이터 수신 불가] 거래소 서버가 데이터를 주지 않습니다. 내일 다시 시도하십시오.")
        else:
            df = pd.concat([df for df in [df1, df2] if df is not None], ignore_index=True)
            
            # 컬럼 강제 명명
            col_map = {'ISU_SRT_CD':'코드', 'ISU_NM':'종목명', 'TDD_CLSPRC':'종가', 'TDD_OPNPRC':'시가', 'ACC_TRDVOL':'거래량', 'FLT_RT':'등락률'}
            df = df.rename(columns=col_map)
            
            if all(c in df.columns for c in col_map.values()):
                # 데이터 정제
                for c in ['종가', '시가', '거래량', '등락률']:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # 5대 절대 규칙
                res = df[
                    (df['거래량'] >= 1000000) & 
                    (df['종가'] > df['시가']) & 
                    (df['등락률'].between(2.0, 8.0)) & 
                    (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
                ].sort_values('거래량', ascending=False)
                
                if not res.empty:
                    st.success(f"✅ {len(res)}개 종목 발견")
                    st.table(res[['코드', '종목명', '종가', '등락률', '거래량']])
                else:
                    st.info("💡 오늘 검색 조건에 맞는 종목이 없습니다.")
            else:
                st.error("⚠️ 거래소 데이터 형식이 불안정합니다.")
