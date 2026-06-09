import streamlit as st
import requests
import pandas as pd

st.title("📊 모네타: 표준 데이터 호출기")

api_key = st.sidebar.text_input("🔑 API 인증키", type="password")
basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 표준 호출 가동"):
    if not api_key:
        st.error("API 키 입력 필수")
    else:
        # 한국거래소 공식 표준 호출 방식
        url = "http://data.krx.co.kr/commbldtop/WhlSvc.ctrl"
        
        # 주식시장 표준 파라미터 (코스피: STK, 코스닥: KSQ)
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "mktId": "STK",
            "trdDd": basDd,
            "share": "1",
            "csvxls_is": "false"
        }
        
        headers = {"AUTH_KEY": api_key.strip()}
        
        try:
            res = requests.get(url, headers=headers, params=params)
            # 결과 확인
            data = res.json()
            st.write("응답 코드:", res.status_code)
            
            if 'OutBlock_1' in data:
                df = pd.DataFrame(data['OutBlock_1'])
                st.success(f"데이터 {len(df)}개 확보!")
                st.dataframe(df)
            else:
                st.error("데이터 블록을 찾을 수 없습니다. 응답 내용 확인:")
                st.write(data)
        except Exception as e:
            st.error(f"오류: {e}")
