import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="모네타 퀀트 스캐너", layout="wide")
st.title("📊 모네타(Moneta) 퀀트 스캐너")
st.markdown("---")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("검색 날짜(YYYYMMDD)", datetime.now().strftime("%Y%m%d"))

if st.button("🚀 전체 시장 스캐닝 가동", type="primary"):
    if not api_key:
        st.error("API 키를 입력해 주십시오.")
    else:
        # 거래소 표준 운영 API 호출
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501", # 주식 시세
            "mktId": "ALL", # 전체 시장
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            res = requests.post(url, headers={"AUTH_KEY": api_key.strip()}, data=params)
            data = res.json()
            
            if 'OutBlock_1' in data:
                df = pd.DataFrame(data['OutBlock_1'])
                
                # 데이터 정제: 이름표 번역 (영문 -> 한글)
                rename_map = {
                    'ISU_NM': '종목명', 'TDD_CLSPRC': '종가', 
                    'TDD_OPNPRC': '시가', 'ACC_TRDVOL': '거래량', 'FLT_RT': '등락률'
                }
                df = df.rename(columns=rename_map)
                
                # 숫자 변환
                for col in ['종가', '시가', '거래량', '등락률']:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # 5대 퀀트 필터 적용
                res_df = df[
                    (df['거래량'] >= 1000000) & 
                    (df['종가'] > df['시가']) & 
                    (df['등락률'].between(2.0, 8.0)) & 
                    (~df['종목명'].str.contains('KODEX|TIGER|HANARO|레버리지|인버스|ETN', case=False, na=False))
                ].sort_values('거래량', ascending=False)
                
                st.success(f"✅ 필터 통과 종목: {len(res_df)}개")
                st.table(res_df[['종목명', '종가', '등락률', '거래량']])
            else:
                st.warning("💡 해당 날짜에 데이터가 없거나 인증키 권한을 확인하십시오.")
                st.write(data)
        except Exception as e:
            st.error(f"오류: {e}")
