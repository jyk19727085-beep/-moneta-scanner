import streamlit as st
import requests
import pandas as pd

st.title("📊 모네타: 브라우저 위장 통신 엔진")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기"):
    if not api_key:
        st.error("API 키를 입력하십시오.")
    else:
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # [핵심] 봇이 아니라 브라우저라고 서버를 속이는 'User-Agent' 설정
        headers = {
            "AUTH_KEY": api_key.strip(),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        try:
            res = requests.post(url, headers=headers, data=payload)
            
            if "OutBlock_1" in res.text:
                data = res.json()
                st.success("✅ 통신 성공! 데이터 추출 완료")
                st.dataframe(pd.DataFrame(data['OutBlock_1']))
            else:
                st.error("데이터를 가져오는 데 실패했습니다. 서버 응답 전문:")
                st.text(res.text[:500]) # HTML 코드 등 원인 확인
        except Exception as e:
            st.error(f"오류 발생: {e}")
