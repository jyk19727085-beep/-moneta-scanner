import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 대시보드 환경 설정
st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**필터링 완료: ETF 제거 및 개별 기업 주식 전용 모드**")
st.markdown("---")

# KRX 데이터 수집 모듈 (안정성 강화)
def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data: return pd.DataFrame(data['OutBlock_1'])
    except: pass
    return pd.DataFrame()

# 왼쪽 사이드바 제어반
with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("KRX API 인증키:", type="password")
    
    today = datetime.now()
    if today.weekday() == 0: default_date = today - timedelta(days=3)
    elif today.weekday() == 6: default_date = today - timedelta(days=2)
    else: default_date = today
    
    target_date = st.date_input("분석 기준일자", default_date)
    basDd = target_date.strftime("%Y%m%d")

# 시스템 가동
if st.button("🚀 개별 기업 주도주 정밀 스캐닝 가동", type="primary", use_container_width=True):
    if not api_key: 
        st.error("인증키를 먼저 입력해 주십시오.")
    else:
        with st.spinner("개별 주식 정밀 필터링 중..."):
            df_kospi = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df_kosdaq = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            
            if df_kospi.empty and df_kosdaq.empty:
                st.error("데이터 수신 실패. 서버 연결을 확인하십시오.")
            else:
                df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
                
                # 데이터 전처리: 숫자 변환 및 에러 방지
                for col in ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT']:
                    if col in df_all.columns:
                        df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # [Daniel 주인님을 위한 5대 절대 규칙 & 순수 주식 필터링]
                # 1. 거래량 100만 주 이상
                rule_vol = df_all['ACC_TRDVOL'] >= 1000000
                # 2. 양봉 반전 (종가 > 시가)
                rule_candle = df_all['TDD_CLSPRC'] > df_all['TDD_OPNPRC']
                # 3. 2~8% 건강한 상승
                rule_rate = (df_all['FLT_RT'] >= 2.0) & (df_all['FLT_RT'] <= 8.0)
                # 4. 개별 기업 주식 순수 필터 (ETF/인버스/레버리지/ETN 제거)
                filter_word = 'KODEX|TIGER|HANARO|KBSTAR|ACE|SOL|KOSEF|선물|인버스|레버리지|ETN|스팩'
                rule_pure = ~df_all['ISU_NM'].str.contains(filter_word, case=False, na=False)
                
                final_df = df_all[rule_vol & rule_candle & rule_rate & rule_pure].copy()
                
                if not final_df.empty:
                    final_df = final_df.sort_values(by='ACC_TRDVOL', ascending=False).head(15)
                    display_df = pd.DataFrame({
                        '종목코드': final_df['ISU_SRT_CD'],
                        '종목명': final_df['ISU_NM'],
                        '종가': final_df['TDD_CLSPRC'].apply(lambda x: f"{int(x):,}원"),
                        '등락률': final_df['FLT_RT'].apply(lambda x: f"{x:.2f}%"),
                        '당일 거래량': final_df['ACC_TRDVOL'].apply(lambda x: f"{int(x):,}주"),
                        '분석 요약': "🔥 순수 개별주 반전 포착"
                    })
                    # 행 번호 노이즈 제거: 1부터 시작하는 깔끔한 순위 표출
                    display_df.index = range(1, len(display_df) + 1)
                    
                    st.success(f"✅ ETF 제외, 개별 기업 주도주 {len(display_df)}개를 포착했습니다.")
                    st.table(display_df)
                else:
                    st.warning("⚠️ 개별 기업 중 조건에 맞는 종목이 없습니다. 관망이 최선의 퀀트 전략입니다.")
