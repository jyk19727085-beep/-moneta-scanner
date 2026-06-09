import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="모네타 주식 스캐너", layout="wide")
st.title("📈 모네타: 주식 전용 퀀트 레이더")

# API 정보 입력
api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", datetime.now().strftime("%Y%m%d"))

def fetch_stock_data(mkt_id):
    """채권을 제외하고 주식 시장(코스피, 코스닥) 데이터만 호출"""
    url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    # 주식 시세 블록코드
    params = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501", 
        "mktId": mkt_id, # STK: 코스피, KSQ: 코스닥
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    headers = {"AUTH_KEY": api_key.strip()}
    res = requests.post(url, headers=headers, data=params)
    return res.json()

if st.button("🚀 주식 전용 데이터 호출"):
    if not api_key:
        st.error("인증키를 입력하세요.")
    else:
        st.write("📡 주식 데이터 호출 중...")
        try:
            # 코스피와 코스닥 데이터만 가져오기 (채권 제외)
            kospi_json = fetch_stock_data("STK")
            kosdaq_json = fetch_stock_data("KSQ")
            
            # DataFrame 합치기
            df_kospi = pd.DataFrame(kospi_json.get('OutBlock_1', []))
            df_kosdaq = pd.DataFrame(kosdaq_json.get('OutBlock_1', []))
            final_df = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
            
            st.success(f"✅ 주식 시장 데이터 수집 완료! (총 {len(final_df)} 종목)")
            
            # 퀀트 필터링 적용 (거래량 50만주 이상 등)
            final_df['ACC_TRDVOL'] = pd.to_numeric(final_df['ACC_TRDVOL'].str.replace(',', ''), errors='coerce')
            result = final_df[final_df['ACC_TRDVOL'] > 500000]
            
            st.dataframe(result[['ISU_NM', 'TDD_CLSPRC', 'FLT_RT', 'ACC_TRDVOL']])
            
        except Exception as e:
            st.error(f"데이터 호출 중 오류가 발생했습니다: {e}")
            st.info("※ 오류가 계속되면, KRX 사이트에서 해당 데이터를 엑셀로 저장 후 파일을 직접 업로드해 주십시오.")
