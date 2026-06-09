import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("📊 모네타: KRX 주식 데이터 스캐너")

basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기 가동"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.krx.co.kr",
    }

    session = requests.Session()

    try:
        session.get("https://www.krx.co.kr/main/main.jsp", headers=headers, timeout=10)
    except Exception:
        pass

    otp_payload = {
        "bld":       "dbms/MDC/STAT/standard/MDCSTAT01501",
        "name":      "fileDown",
        "filetype":  "csv",
        "url":       "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId":     "ALL",
        "trdDd":     basDd,
        "share":     "1",
        "money":     "1",
        "csvxls_is": "true",
    }

    try:
        otp_res = session.post(
            "https://www.krx.co.kr/contents/COM/GenerateOTP.jspx",
            headers=headers,
            data=otp_payload,
            timeout=15,
        )
        otp_code = otp_res.text.strip()

        if not otp_code or "<html" in otp_code.lower():
            st.error("OTP 발급 실패")
            st.text(otp_res.text[:300])
            st.stop()

        st.info(f"OTP 발급 성공: {otp_code[:30]}...")

        # ✅ 다운로드 헤더 별도 구성
        dl_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Origin": "https://www.krx.co.kr",
        }

        dl_res = session.post(
            "https://file.krx.co.kr/download.jspx",
            headers=dl_headers,
            data={"code": otp_code},
            timeout=30,
        )

        st.write(f"📡 응답 크기: {len(dl_res.content)} bytes / 상태: {dl_res.status_code}")

        # ✅ 크기 조건 제거하고 내용으로 판단
        content_text = dl_res.content.decode("euc-kr", errors="replace")

        if "<html" in content_text[:200].lower():
            st.error("CSV가 아닌 HTML 반환됨 — KRX 세션 만료 또는 차단")
            st.text(content_text[:500])
        elif "," not in content_text[:200]:
            st.error("CSV 형식 아님 — 응답 내용 확인:")
            st.text(content_text[:500])
        else:
            df = pd.read_csv(StringIO(content_text))
            st.success(f"✅ {len(df)}개 종목 로드 완료!")
            st.dataframe(df.head(50))
            st.download_button(
                "📥 CSV 저장",
                data=dl_res.content,
                file_name=f"krx_{basDd}.csv",
                mime="text/csv",
            )

    except requests.exceptions.Timeout:
        st.error("⏱️ 타임아웃")
    except Exception as e:
        st.error(f"예외: {e}")
