import streamlit as st
import requests

st.title("📊 모네타: 최종 통신 엔진 (Form 전송 모드)")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 폼 전송 가동"):
    if not api_key:
        st.error("API 키 입력 필수")
    else:
        # 거래소 운영 서버의 표준 호출 주소
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # [핵심] 거래소가 필수라고 요구하는 폼 데이터 형태
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        headers = {"AUTH_KEY": api_key.strip()}
        
        try:
            # POST 방식으로 폼 데이터 전송 (표준 가이드)
            res = requests.post(url, headers=headers, data=payload)
            st.write("응답 상태 코드:", res.status_code)
            
            # 서버가 보낸 원본 내용을 그대로 화면에 띄웁니다.
            st.text("서버 응답 결과:")
            st.json(res.json())
        except Exception as e:
            st.error(f"오류: {e}")
