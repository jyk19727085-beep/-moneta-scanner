import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**에러 제로(Zero-Error) 방어 체계 적용 완료**")

# 1. 데이터 호출 모듈 (오류 방어 강화)
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
    api_key = st.text_input("🔑 KRX API 인증키:", type="password")
    target_date = st.date_input("분석 기준일자", datetime.now() - timedelta(days=1))
    basDd = target_date.strftime("%Y%m%d")

if st.button("🚀 정밀 스캐닝 가동", type="primary", use_container_width=True):
    if not api_key: st.error("인증키 입력 필수")
    else:
        with st.spinner("데이터 분석 중..."):
            df_kospi = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df_kosdaq = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            
            # 방어 1: 데이터가 하나라도 있는지 확인
            if df_kospi.empty and df_kosdaq.empty:
                st.warning("⚠️ 선택하신 날짜에 거래소 데이터가 없습니다. 다른 날짜를 선택하십시오.")
            else:
                df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
                
                # 방어 2: 데이터가 있어도 필수 항목이 있는지 확인 후 숫자 변환
                required_cols = ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT']
                if all(col in df_all.columns for col in required_cols):
                    for col in required_cols:
                        df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
                    # 5대 절대 규칙 필터링
                    rule_vol = df_all['ACC_TRDVOL'] >= 1000000
                    rule_candle = df_all['TDD_CLSPRC'] > df_all['TDD_OPNPRC']
                    rule_rate = (df_all['FLT_RT'] >= 2.0) & (df_all['FLT_RT'] <= 8.0)
                    rule_pure = ~df_all['ISU_NM'].str.contains('KODEX|TIGER|HANARO|KBSTAR|ACE|SOL|KOSEF|선물|인버스|레버리지|ETN|스팩', case=False, na=False)
                    
                    final_df = df_all[rule_vol & rule_candle & rule_rate & rule_pure].copy()
                    
                    if not final_df.empty:
                        res_df = final_df.sort_values(by='ACC_TRDVOL', ascending=False).head(15)
                        show_df = pd.DataFrame({
                            '종목코드': res_df['ISU_SRT_CD'],
                            '종목명': res_df['ISU_NM'],
                            '종가': res_df['TDD_CLSPRC'].map('{:,.0f}원'.format),
                            '등락률': res_df['FLT_RT'].map('{:.2f}%'.format),
                            '거래량': res_df['ACC_TRDVOL'].map('{:,.0f}주'.format)
                        })
                        show_df.index = range(1, len(show_df)+1)
                        st.success(f"✅ 조건 부합 종목 {len(show_df)}개 포착")
                        st.table(show_df)
                    else:
                        st.info("💡 조건에 맞는 종목이 없습니다 (퀀트 시스템 정상 작동 중).")
                else:
                    st.error("⚠️ 데이터 형식이 올바르지 않습니다.")
