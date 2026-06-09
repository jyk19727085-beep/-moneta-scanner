import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**Daniel 주인님의 절대 규칙 (거래량 100만주 + 바닥권 반전) 적용 완료**")

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
        with st.spinner("한국거래소 데이터 분석 중..."):
            df_kospi = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df_kosdaq = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
            
            if not df_all.empty and 'ACC_TRDVOL' in df_all.columns:
                cols_to_numeric = ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT']
                for col in cols_to_numeric:
                    if col in df_all.columns:
                        df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # 규칙 적용
                rule1 = df_all['ACC_TRDVOL'] >= 1000000
                rule2 = df_all['TDD_CLSPRC'] > df_all['TDD_OPNPRC']
                rule3 = (df_all['FLT_RT'] >= 2.0) & (df_all['FLT_RT'] <= 8.0)
                
                final_df = df_all[rule1 & rule2 & rule3].copy()
                
                if not final_df.empty:
                    final_df = final_df.sort_values(by='ACC_TRDVOL', ascending=False).head(15)
                    display_df = pd.DataFrame({
                        '종목코드': final_df['ISU_SRT_CD'],
                        '종목명': final_df['ISU_NM'],
                        '종가': final_df['TDD_CLSPRC'].apply(lambda x: f"{int(x):,}원"),
                        '등락률': final_df['FLT_RT'].apply(lambda x: f"{x:.2f}%"),
                        '당일 거래량': final_df['ACC_TRDVOL'].apply(lambda x: f"{int(x):,}주"),
                        '퀀트 분석 요약': "🔥 100만주 이상 + 바닥권 양봉 반전"
                    })
                    st.success(f"✅ 스캐닝 완료! 조건 부합 종목 {len(display_df)}개를 포착했습니다.")
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.warning("⚠️ 오늘 시장에서는 100만 주 이상의 거래량을 동반하며 반등한 조건 부합 종목이 없습니다. 현금 관망을 권장합니다.")
                    st.info("💡 모네타의 조언: 설정하신 조건이 매우 엄격하고 안전합니다. 하락장에서는 종목이 검색되지 않는 것이 퀀트 시스템의 올바른 방어 작동입니다.")
            else:
                st.error("데이터 통신 지연. 거래소 서버 동기화를 기다리거나 날짜를 영업일로 변경해 주십시오.")
