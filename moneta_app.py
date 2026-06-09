import streamlit as st
import requests
import pandas as pd

st.title("📊 모네타: 최종 무결점 스캐너")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 강제 호출"):
    if not api_key:
        st.error("API 키를 입력하세요.")
    else:
        # 거래소 데이터 마켓 공식 엔드포인트
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # 거래소가 100% 만족할 최적의 파라미터 구성
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK", # 코스피 시장
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        headers = {"AUTH_KEY": api_key.strip()}
        
        try:
            # 거래소는 POST 방식을 선호합니다.
            res = requests.post(url, headers=headers, data=payload)
            
            # 서버 응답 분석
            if res.status_code == 200:
                data = res.json()
                if 'OutBlock_1' in data:
                    st.success("✅ 통신 성공! 데이터 추출 시작")
                    df = pd.DataFrame(data['OutBlock_1'])
                    st.dataframe(df.head(10))
                else:
                    st.error("데이터 없음. 서버 응답 메시지 확인:")
                    st.json(data)
            else:
                st.error(f"서버 접속 오류 (코드: {res.status_code})")
                
        except Exception as e:
            st.error(f"시스템 오류: {e}")
