import streamlit as st
import pandas as pd
import requests

st.set_page_config(layout="wide")
st.title("📊 모네타 스캐너 (통신 진단 모드)")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 스캐닝 가동"):
    if not api_key: 
        st.error("API 키를 입력하세요.")
    else:
        # 키 앞뒤의 실수 빈칸(공백) 자동 제거
        clean_key = api_key.strip()
        url = "http://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"
        
        try:
            res = requests.get(url, headers={"AUTH_KEY": clean_key}, params={"basDd": basDd}, timeout=10)
            data = res.json()
            
            # 거래소에서 에러 메시지를 보냈는지 최우선 확인
            if 'error_msg' in data:
                st.error(f"🛑 한국거래소(KRX) 서버 응답: {data['error_msg']}")
                st.warning("💡 조치 방법: KRX Data Marketplace 홈페이지 로그인 -> 마이페이지 -> API 키 상태 및 시세 데이터 신청 여부 확인")
            elif 'OutBlock_1' in data and data['OutBlock_1']:
                st.success("✅ 통신 대성공! 인증키가 유효합니다. 데이터를 불러옵니다.")
                df = pd.DataFrame(data['OutBlock_1'])
                st.dataframe(df.head(10))
            else:
                st.info("통신은 정상이나 해당 날짜에 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"서버 접속 자체 실패: {e}")
