import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Daniel 모네타 퀀트 시스템", layout="wide")
st.title("📊 모네타(Moneta) - 주식 & 채권 통합 스캐너")
st.markdown("---")

# 1. 절대 죽지 않는 안전한 데이터 호출 모듈
def get_krx_data(url, api_key, basDd):
    try:
        res = requests.get(url, headers={"AUTH_KEY": api_key.strip()}, params={"basDd": basDd}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data and data['OutBlock_1']:
                return pd.DataFrame(data['OutBlock_1'])
            elif 'error_msg' in data:
                st.warning(f"서버 응답: {data['error_msg']}")
    except Exception:
        pass
    return pd.DataFrame() # 오류 시 무조건 빈 데이터프레임 반환

# 2. 사이드바 제어반
with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("API 인증키:", type="password")
    basDd = st.text_input("검색 날짜(YYYYMMDD):", datetime.now().strftime("%Y%m%d"))

# 3. 메인 엔진 가동
if st.button("🚀 통합 스캐닝 가동", type="primary", use_container_width=True):
    if not api_key: 
        st.error("API 키를 입력해 주십시오.")
    else:
        st.info("📡 한국거래소(KRX) 서버와 실시간 통신 중입니다...")
        
        # 전체 로직을 감싸서 앱이 뻗는 것을 100% 방지
        try:
            # ==========================================
            # 🟢 [섹션 1] 채권 시장 동향 (국고채 + 일반채권)
            # ==========================================
            st.subheader("🌐 채권 시장 스캐닝 (안전 자산 모니터링)")
            
            bond_ktb = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/bnd/ktb_dd_trd", api_key, basDd)
            bond_gen = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/bnd/gen_bnd_dd_trd", api_key, basDd)
            
            # [핵심 수정] 데이터가 있을 때만 합치기 (ValueError 원천 차단)
            bond_list = [df for df in [bond_ktb, bond_gen] if not df.empty]
            bond_df = pd.concat(bond_list, ignore_index=True) if bond_list else pd.DataFrame()
            
            if not bond_df.empty:
                bond_cols = {'ISU_NM': '채권명', 'TDD_CLSPRC': '종가(원)', 'YLD_FOR_OPNPRC': '수익률(%)', 'ACC_TRDVOL': '거래량'}
                bond_df = bond_df.rename(columns={k:v for k,v in bond_cols.items() if k in bond_df.columns})
                
                if '거래량' in bond_df.columns:
                    bond_df['거래량'] = pd.to_numeric(bond_df['거래량'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    display_bond = bond_df.sort_values('거래량', ascending=False).head(5)
                    display_bond.index = range(1, len(display_bond) + 1)
                    
                    st.success("✅ 채권 데이터 수신 및 정제 완료")
                    show_bond_cols = [c for c in ['채권명', '종가(원)', '수익률(%)', '거래량'] if c in display_bond.columns]
                    st.table(display_bond[show_bond_cols])
            else:
                st.warning("💡 해당 날짜에 수신된 채권 데이터가 없습니다.")

            st.markdown("---")

            # ==========================================
            # 🔴 [섹션 2] 개별 주식 주도주 스캐닝 (5대 절대 규칙)
            # ==========================================
            st.subheader("🎯 개별 주식 주도주 스캐너 (퀀트 필터링)")
            
            df1 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", api_key, basDd)
            df2 = get_krx_data("http://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd", api_key, basDd)
            
            # [핵심 수정] 데이터가 있을 때만 합치기 (ValueError 원천 차단)
            stock_list = [df for df in [df1, df2] if not df.empty]
            stock_df = pd.concat(stock_list, ignore_index=True) if stock_list else pd.DataFrame()
            
            if not stock_df.empty:
                stock_cols = {'ISU_SRT_CD': '종목코드', 'ISU_NM': '종목명', 'TDD_CLSPRC': '당일종가', 'TDD_OPNPRC': '당일시가', 'ACC_TRDVOL': '당일거래량', 'FLT_RT': '등락률(%)'}
                stock_df = stock_df.rename(columns={k:v for k,v in stock_cols.items() if k in stock_df.columns})
                
                for c in ['당일종가', '당일시가', '당일거래량', '등락률(%)']:
                    if c in stock_df.columns:
                        stock_df[c] = pd.to_numeric(stock_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                
                # 모든 필수 컬럼이 정상적으로 있는지 검증 후 필터링
                if all(c in stock_df.columns for c in ['당일거래량', '당일종가', '당일시가', '등락률(%)', '종목명']):
                    res = stock_df[
                        (stock_df['당일거래량'] >= 1000000) & 
                        (stock_df['당일종가'] > stock_df['당일시가']) & 
                        (stock_df['등락률(%)'].between(2.0, 8.0)) & 
                        (~stock_df['종목명'].str.contains('KODEX|TIGER|HANARO|KBSTAR|ACE|SOL|KOSEF|레버리지|인버스|ETN|스팩', case=False, na=False))
                    ]
                    
                    if not res.empty:
                        res = res.sort_values('당일거래량', ascending=False).head(15)
                        res.index = range(1, len(res) + 1)
                        
                        st.success(f"✅ 퀀트 필터 통과! 시장 주도주 {len(res)}개 포착 완료")
                        show_stock_cols = [c for c in ['종목코드', '종목명', '당일종가', '등락률(%)', '당일거래량'] if c in res.columns]
                        st.dataframe(res[show_stock_cols], use_container_width=True)
                    else:
                        st.info("💡 오늘 시장에서는 주인님의 '엄격한 기준(100만주 이상+양봉+ETF제외)'을 완벽히 충족하는 주식이 없습니다.")
                else:
                    st.error("⚠️ 데이터 항목이 부족하여 필터링을 수행할 수 없습니다.")
            else:
                st.error("⚠️ 거래소가 주식 데이터를 반환하지 않았습니다.")

        # [안전망] 어떤 알 수 없는 시스템 충돌이 와도 화면에 에러를 표시하고 죽지 않게 함
        except Exception as e:
            st.error(f"🚨 시스템 작동 중 예기치 않은 오류 발생: {e}")
            st.info("💡 위 붉은색 글씨(오류 내용)를 복사해서 제게 알려주시면 1초 만에 원인을 진단해 드리겠습니다.")
