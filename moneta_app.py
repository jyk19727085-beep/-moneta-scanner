import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. 시각적 설정을 강화한 페이지
st.set_page_config(page_title="Daniel 모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타 퀀트 스캐너 - 대용량 분석 엔진")
st.markdown("**엄격한 5대 퀀트 필터링 엔진이 가동 중입니다.**")

# 2. 고도화된 데이터 호출 및 오류 진단 로직
def fetch_krx_data(api_key, basDd):
    results = []
    # 코스피와 코스닥 경로를 명확히 분리
    targets = ["http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", "http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd"]
    
    for url in targets:
        try:
            res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=20)
            if res.status_code == 200:
                data = res.json()
                if 'OutBlock_1' in data and data['OutBlock_1']:
                    results.append(pd.DataFrame(data['OutBlock_1']))
        except Exception as e:
            st.sidebar.error(f"서버 연결 오류: {url}")
            
    if not results: return None
    return pd.concat(results, ignore_index=True)

with st.sidebar:
    api_key = st.text_input("🔑 API 인증키", type="password")
    basDd = st.date_input("기준 날짜", datetime.now()).strftime("%Y%m%d")

# 3. 메인 분석 엔진
if st.button("🚀 전체 데이터 심층 스캐닝"):
    if not api_key: st.error("인증키가 필요합니다.")
    else:
        with st.spinner("한국거래소 전 종목 데이터 연산 중..."):
            df = fetch_krx_data(api_key, basDd)
            
            if df is None or df.empty:
                st.error("데이터 수신 실패. 1) 거래소 서버 점검 중 2) API 승인 동기화 대기 3) 공휴일 여부를 확인하십시오.")
            else:
                # 데이터 명칭 자동 매핑 (에러 방지)
                rename_map = {
                    'ISU_SRT_CD': '종목코드', 'ISU_NM': '종목명',
                    'TDD_CLSPRC': '종가', 'TDD_OPNPRC': '시가', 
                    'ACC_TRDVOL': '거래량', 'FLT_RT': '등락률'
                }
                df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
                
                # 데이터 타입 강제 변환
                for col in ['종가', '시가', '거래량', '등락률']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # 4. 강력한 5대 필터링 규칙 (절대 규칙)
                filtered_df = df[
                    (df['거래량'] >= 1000000) &               # 1. 거래량 100만주 이상
                    (df['종가'] > df['시가']) &                 # 2. 양봉
                    (df['등락률'].between(2.0, 8.0)) &          # 3. 건강한 상승
                    (~df['종목명'].str.contains('KODEX|TIGER|KOSEF|선물|인버스|레버리지', case=False, na=False)) # 4. ETF 배제
                ].sort_values('거래량', ascending=False)
                
                # 5. 결과 표출
                if not filtered_df.empty:
                    st.success(f"✅ 분석 완료! 철칙을 만족하는 종목 {len(filtered_df)}개를 발견했습니다.")
                    st.table(filtered_df[['종목코드', '종목명', '종가', '등락률', '거래량']])
                else:
                    st.warning("⚠️ 모든 조건(100만주, 양봉, 적정 반등)을 만족하는 개별 주식이 없습니다.")
                    st.markdown("---")
                    st.write("분석된 원본 데이터 일부:")
                    st.write(df[['종목명', '거래량']].head(5))
