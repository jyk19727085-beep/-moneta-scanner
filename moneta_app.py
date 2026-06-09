import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**데이터 형식 자동 보정 및 ETF 배제 완료**")

def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and len(data['OutBlock_1']) > 0:
                return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키:", type="password")
    basDd = st.date_input("기준일", datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

if st.button("🚀 주도주 정밀 스캐닝 가동", type="primary", use_container_width=True):
    if not api_key: st.error("인증키 입력 필수")
    else:
        with st.spinner("거래소 데이터 호출 및 형식 보정 중..."):
            df1 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df2 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            
            if df1.empty and df2.empty:
                st.warning("⚠️ 선택한 날짜에 데이터가 없습니다.")
            else:
                df = pd.concat([df1, df2], ignore_index=True)
                
                # 강제 컬럼 매핑: 거래소가 이름을 다르게 줘도 시스템이 인식하도록 강제 변경
                # 원본 이름이 다른 경우를 대비해 목록에서 매칭
                col_map = {
                    'TDD_CLSPRC': '종가', 'TDD_OPNPRC': '시가', 
                    'ACC_TRDVOL': '거래량', 'FLT_RT': '등락률',
                    'ISU_SRT_CD': '코드', 'ISU_NM': '종목명'
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                
                # 분석 가능한 필수 컬럼이 있는지 최종 확인
                if all(v in df.columns for v in col_map.values()):
                    # 숫자 변환
                    for col in ['종가', '시가', '거래량', '등락률']:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
                    # 5대 규칙 적용
                    rule_vol = df['거래량'] >= 1000000
                    rule_candle = df['종가'] > df['시가']
                    rule_rate = (df['등락률'] >= 2.0) & (df['등락률'] <= 8.0)
                    rule_pure = ~df['종목명'].str.contains('KODEX|TIGER|HANARO|KBSTAR|ACE|SOL|KOSEF|선물|인버스|레버리지|ETN|스팩', case=False, na=False)
                    
                    final_df = df[rule_vol & rule_candle & rule_rate & rule_pure].sort_values('거래량', ascending=False).head(15)
                    
                    if not final_df.empty:
                        st.success(f"✅ 조건 만족 종목 {len(final_df)}개 포착")
                        st.table(final_df[['코드', '종목명', '종가', '등락률', '거래량']])
                    else:
                        st.info("💡 오늘 시장에서는 조건에 맞는 개별 주식이 없습니다.")
                else:
                    st.error("⚠️ 거래소 데이터 형식이 불안정합니다. 내일 오전 동기화 후 다시 시도하십시오.")
