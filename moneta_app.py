import streamlit as st
import pandas as pd
import requests
import json

st.title("📊 모네타: KRX 주식 데이터 스캐너")

basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기 가동"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.krx.co.kr/main/main.jsp",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.krx.co.kr",
    }

    session = requests.Session()

    # 1단계: 메인 페이지로 쿠키 획득
    try:
        session.get("https://www.krx.co.kr/main/main.jsp", headers=headers, timeout=10)
    except Exception:
        pass

    # 2단계: 실제 KRX OTP 발급 → 데이터 조회 2단계 방식
    otp_url = "https://www.krx.co.kr/nas/ut/etcLook/utCmnLookUpGnrlCd.do"
    data_url = "https://file.krx.co.kr/download.jspx"

    # KRX 공식 전종목 시세 OTP 요청
    otp_payload = {
        "bld":     "dbms/MDC/STAT/standard/MDCSTAT01501",
        "name":    "fileDown",
        "filetype": "csv",
        "url":     "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId":   "ALL",
        "trdDd":   basDd,
        "share":   "1",
        "money":   "1",
        "csvxls_is": "true",
    }

    try:
        # OTP 코드 발급
        otp_res = session.post(
            "https://www.krx.co.kr/contents/COM/GenerateOTP.jspx",
            headers=headers,
            data=otp_payload,
            timeout=15,
        )
        otp_code = otp_res.text.strip()
        st.info(f"OTP 발급: {otp_code[:30]}...")

        if not otp_code or "<html" in otp_code.lower():
            st.error("OTP 발급 실패 — KRX가 접근을 차단했습니다.")
            st.text(otp_res.text[:300])
        else:
            # OTP로 CSV 다운로드
            download_headers = headers.copy()
            download_headers["Referer"] = "https://www.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"

            dl_res = session.post(
                data_url,
                headers=download_headers,
                data={"code": otp_code},
                timeout=30,
            )

            if dl_res.status_code == 200 and len(dl_res.content) > 100:
                # CSV 파싱
                from io import StringIO
                decoded = dl_res.content.decode("euc-kr", errors="replace")
                df = pd.read_csv(StringIO(decoded))
                st.success(f"✅ {len(df)}개 종목 로드 완료!")
                st.dataframe(df.head(50))

                # CSV 다운로드 버튼
                st.download_button(
                    "📥 CSV 저장",
                    data=dl_res.content,
                    file_name=f"krx_{basDd}.csv",
                    mime="text/csv",
                )
            else:
                st.error(f"다운로드 실패: {dl_res.status_code}")
                st.text(dl_res.text[:500])

    except requests.exceptions.Timeout:
        st.error("⏱️ 타임아웃 — KRX 서버 응답 없음")
    except Exception as e:
        st.error(f"예외 발생: {e}")
