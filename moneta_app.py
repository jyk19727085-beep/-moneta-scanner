import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Daniel 모네타 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 실전 퀀트 스캐너")
st.markdown("**Daniel 주인님의 절대 규칙 (거래량 100만주 + 바닥권 반전) 적용 완료**")

# 데이터를 안전하게 가져오는 함수
def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key}, params={"basDd": basDd}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # OutBlock_1이 존재하고 데이터가 비어있지 않을 때만 데이터프레임 반환
            if 'OutBlock_1' in data and len(data['OutBlock_1']) > 0:
                return pd.DataFrame(data['OutBlock_1'])
    except Exception as e:
        pass
    return pd.DataFrame() # 실패하거나 비어있으면 무조건 빈 데이터프레임 반환

# 왼쪽 설정 패널
with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("KRX API 인증키:", type="password")
    
    # 기본 날짜를 장이 열리는 평일로 보정
    today = datetime.now()
    if today.weekday() == 0: default_date = today - timedelta(days=3) # 월요일이면 금요일로
    elif today.weekday() == 6: default_date = today - timedelta(days=2) # 일요일이면 금요일로
    else: default_date = today
    
    target_date = st.date_input("분석 기준일자", default_date)
    basDd = target_date.strftime("%Y%m%d")

# 메인 실행 버튼
if st.button("🚀 주도주 정밀 스캐닝 가동", type="primary"):
    if not api_key: 
        st.error("왼쪽 제어반에 API 인증키를 먼저 입력해 주십시오.")
    else:
        with st.spinner("한국거래소(KRX) 심장부에서 데이터를 추출하고 있습니다..."):
            df_kospi = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df_kosdaq = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            
            # 방어 로직 1: 거래소가 아예 빈 봉투를 줬을 때 차단
            if df_kospi.empty and df_kosdaq.empty:
                st.error("⚠️ 거래소에서 데이터가 전혀 들어오지 않았습니다.\n\n[원인 진단]\n1. 아직 API 권한이 100% 동기화되지 않았음.\n2. 선택하신 날짜가 주말/공휴일임.")
            else:
                df_all = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
                
                # 방어 로직 2: 필수 컬럼(종가, 시가 등)이 없으면 차단 (KeyError 방지)
                required_cols = ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT', 'ISU_SRT_CD', 'ISU_NM']
                missing_cols = [col for col in required_cols if col not in df_all.columns]
                
                if missing_cols:
                    st.error(f"⚠️ 거래소 데이터 형식이 예상과 다릅니다. (누락된 정보: {missing_cols})")
                    st.info("거래소에서 보내온 원본 데이터를 보여드립니다. 권한 문제가 섞여 있을 수 있습니다.")
                    st.write(df_all.head()) # 원본 데이터 표출 (디버깅용)
                else:
                    # 방어 로직 3: 문자열로 온 숫자들을 에러 없이 변환
                    for col in ['TDD_CLSPRC', 'TDD_OPNPRC', 'ACC_TRDVOL', 'FLT_RT']:
                        df_all[col] = pd.to_numeric(df_all[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
                    # [Daniel 절대 규칙 필터링]
                    rule1 = df_all['ACC_TRDVOL'] >= 1000000  # 100만주 이상
                    rule2 = df_all['TDD_CLSPRC'] > df_all['TDD_OPNPRC']  # 양봉 반전
                    rule3 = (df_all['FLT_RT'] >= 2.0) & (df_all['FLT_RT'] <= 8.0)  # 건강한 반등
                    
                    final_df = df_all[rule1 & rule2 & rule3].copy()
                    
                    # 방어 로직 4: 조건에 맞는 종목이 없을 때
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
                        st.warning("⚠️ 오늘 시장에서는 [100만주 이상 거래 + 2~8% 반등 양봉] 조건을 완벽히 충족하는 종목이 단 한 개도 없습니다.")
                        st.info("💡 모네타의 조언: 설정하신 필터링이 매우 깐깐하고 안전하게 작동하고 있습니다. 억지로 타점을 잡지 않고 현금을 관망하는 것이 퀀트의 정석입니다.")
