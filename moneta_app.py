import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**Daniel 주인님의 절대 규칙 (거래량 100만주 + 바닥권 반전) 적용 완료**")

# KRX 데이터 호출 공통 모듈
def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data: return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("KRX API 인증키:", type="password")
    
    # 주말 보정 로직
    today = datetime.now()
    if today.weekday() == 0: default_date = today - timedelta(days=3)
    elif today.weekday() == 6: default_date = today - timedelta(days=2)
    else: default_date = today
    
    target_date = st.date_input("분석 기준일자", default_date)
    basDd = target_date.strftime("%Y%m%d")

if st.button("🚀 주도주 정밀 스캐닝 가동", type="primary"):
    if not api_key: 
        st.error("인증키를 입력해 주십시오.")
    else:
        with st.spinner("한국거래소 데이터 통신망 접속 중... 코스피/코스닥 전 종목 분석 중..."):
            # 코스피 & 코스닥 시세 병합
            df_kospi = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df_kosdaq = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
            
            if not df_all.empty and 'ACC_TRDVOL' in df_all.columns:
                # 숫자 데이터로 변환 (결측치 0 처리)
                cols_to_numeric = ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT']
                for col in cols_to_numeric:
                    if col in df_all.columns:
                        df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # ==========================================
                # [Daniel 주인님 전용 절대 규칙 필터링 로직]
                # ==========================================
                
                # 1. 거래량 최소 100만 주 이상 (메이저 수급 확인)
                rule1 = df_all['ACC_TRDVOL'] >= 1000000
                
                # 2. 바닥권 추세 반전 (당일 시가보다 종가가 높은 '양봉' 캔들 발생)
                rule2 = df_all['TDD_CLSPRC'] > df_all['TDD_OPNPRC']
                
                # 3. 과매도 이후 반등 (등락률이 2% ~ 8% 사이로 건강하게 고개를 든 종목)
                rule3 = (df_all['FLT_RT'] >= 2.0) & (df_all['FLT_RT'] <= 8.0)
                
                # 규칙 적용
                final_df = df_all[rule1 & rule2 & rule3].copy()
                
                if not final_df.empty:
                    # 보기 좋게 데이터 정렬 (거래량 순)
                    final_df = final_df.sort_values(by='ACC_TRDVOL', ascending=False).head(15)
                    
                    # 대시보드 출력용 테이블 생성
                    display_df = pd.DataFrame({
                        '종목코드': final_df['ISU_SRT_CD'],
                        '종목명': final_df['ISU_NM'],
                        '종가': final_df['TDD_CLSPRC'].apply(lambda x: f"{int(x):,}원"),
                        '등락률': final_df['FLT_RT'].apply(lambda x: f"{x:.2f}%"),
                        '당일 거래량': final_df['ACC_TRDVOL'].apply(lambda x: f"{int(x):,}주"),
                        '퀀트 분석 요약': "🔥 100만주 이상 + 바닥권 양봉 반전"
                    })
                    
                    st.success(f"✅ 스캐닝 완료! 거래량 100만 주 이상의 바닥권 반전 종목 {len(display_df)}개를 포착했습니다.")
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.warning("⚠️ 오늘 시장에서는 100만 주 이상의 거래량을 동반하며 반등한 조건 부합 종목이 없습니다. 현금 관망을 권장합니다.")
            else:
                st.error("데이터 통신 지연. 거래소 서버 동기화를 기다리거나 날짜를 영업일로 변경해 주십시오.")
