import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="모네타 X-Ray 진단실", layout="wide")
st.title("🛠️ 모네타 X-Ray 데이터 진단실")
st.markdown("---")

with st.sidebar:
    st.header("🔑 시스템 제어반")
    api_key = st.text_input("API 인증키:", type="password")
    # 진단을 위해 6월 4일을 기본값으로 고정합니다.
    basDd = st.text_input("검색 날짜(YYYYMMDD):", "20260604")

if st.button("🚀 원본 데이터 해부 시작", type="primary", use_container_width=True):
    if not api_key:
        st.error("API 키를 입력해 주십시오.")
    else:
        def extract_raw_data(url, title):
            st.subheader(f"🔍 {title} 원본 진단")
            try:
                res = requests.get(url, headers={"AUTH_KEY": api_key.strip()}, params={"basDd": basDd}, timeout=15)
                st.write(f"**통신 상태 코드:** `{res.status_code}`")
                
                data = res.json()
                
                if 'error_msg' in data:
                    st.error(f"🚨 서버 에러 메시지: {data['error_msg']}")
                elif 'OutBlock_1' in data and data['OutBlock_1']:
                    df = pd.DataFrame(data['OutBlock_1'])
                    st.success(f"✅ 데이터 수신 완료 (총 {len(df)}개 행 발견)")
                    st.info(f"**수신된 컬럼(이름표) 목록:** {', '.join(df.columns)}")
                    st.dataframe(df.head(5), use_container_width=True)
                else:
                    st.warning("⚠️ 통신은 200(정상)이나, 데이터가 텅 비어 있습니다.")
                    st.write("서버 응답 원문:", data)
            except Exception as e:
                st.error(f"❌ 접속 자체 실패: {e}")

        # 1. 주식 코스피 단독 진단
        extract_raw_data("http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd", "1. 코스피 주식 데이터")
        st.markdown("---")
        # 2. 채권 국고채 단독 진단
        extract_raw_data("http://data-dbg.krx.co.kr/svc/apis/bnd/ktb_dd_trd", "2. 국고채 채권 데이터")
