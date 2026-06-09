import streamlit as st
import requests
import pandas as pd

st.title("📊 모네타: 최후의 브라우저 모방 스캐너")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 강제 호출"):
    # 1. 세션 생성 (브라우저 쿠키를 유지하는 '사람'처럼 행동)
    session = requests.Session()
    url_base = "http://data.krx.co.kr/"
    url_data = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
    
    # 2. 헤더 설정 (사람인 것처럼 위장)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"
    }
    
    # 3. 데이터 요청 규격 (가장 정확한 형태)
    payload = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId": "STK",
        "trdDd": basDd,
        "share": "1",
        "csvxls_is": "false"
    }
    
    try:
        # 인증키 헤더 추가
        headers["AUTH_KEY"] = api_key.strip()
        
        # 호출
        res = session.post(url_data, headers=headers, data=payload)
        
        st.write("응답 코드:", res.status_code)
        
        if res.status_code == 200:
            data = res.json()
            if 'OutBlock_1' in data:
                st.success("✅ 데이터 확보 완료!")
                st.dataframe(pd.DataFrame(data['OutBlock_1']))
            else:
                st.error("데이터 없음:")
                st.write(data)
        else:
            st.error(f"서버 거부 (코드: {res.status_code})")
    except Exception as e:
        st.error(f"시스템 예외: {e}")
