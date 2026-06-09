import streamlit as st
import pandas as pd

st.title("📊 모네타: KRX 주식 데이터 스캐너")

basDd = st.sidebar.text_input("날짜(YYYYMMDD)", "20260604")

if st.button("🚀 데이터 긁어오기 가동"):
    try:
        from pykrx import stock

        with st.spinner("KRX 데이터 수신 중..."):
            df_kospi  = stock.get_market_ohlcv_by_ticker(basDd, market="KOSPI")
            df_kospi["시장"] = "KOSPI"
            df_kosdaq = stock.get_market_ohlcv_by_ticker(basDd, market="KOSDAQ")
            df_kosdaq["시장"] = "KOSDAQ"
            df = pd.concat([df_kospi, df_kosdaq]).reset_index()

        if df.empty:
            st.warning("⚠️ 데이터 없음 (휴장일 또는 미래 날짜)")
        else:
            st.success(f"✅ {len(df)}개 종목 로드!")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 CSV 저장", data=csv.encode("utf-8-sig"),
                               file_name=f"krx_{basDd}.csv", mime="text/csv")

    except ImportError:
        st.error("pykrx 미설치!")
        st.code("pip install pykrx")
    except Exception as e:
        st.error(f"오류: {e}")
