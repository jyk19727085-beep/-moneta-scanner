import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 (PC/모바일 반응형) ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 캐싱을 통한 로딩 속도 최적화 ---
@st.cache_data(ttl=3600)
def get_macro_data(start_date, end_date):
    """거시경제 지표 데이터를 가져오는 함수"""
    macro_symbols = {
        'WTI 원유 (USD/bbl)': 'CL=F',
        '금 (USD/oz)': 'GC=F',
        '미국 10년물 국채 수익률 (%)': '^TNX',
        '한국 3년물 국채 수익률 (%)': 'KR3YT=RR'
    }
    
    data_dict = {}
    for name, symbol in macro_symbols.items():
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if not df.empty:
                data_dict[name] = df['Close']
        except Exception as e:
            st.error(f"{name} 데이터를 불러오는 중 오류가 발생했습니다: {e}")
            
    return data_dict

@st.cache_data(ttl=3600)
def get_top_institutions_foreigners(date_str, market="KOSPI", top_n=30):
    """특정 일자 기준 외국인+기관 순매수 상위 종목 추출 (pykrx 활용)"""
    try:
        # 외국인 순매수
        df_foreign = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "외국인")
        # 기관합계 순매수
        df_inst = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "기관합계")
        
        if df_foreign.empty or df_inst.empty:
            return pd.DataFrame()

        # 순매수 금액(순매수거래대금) 기준으로 데이터 결합
        df_merged = pd.DataFrame({
            '종목명': df_foreign['종목명'],
            '외국인순매수(원)': df_foreign['순매수거래대금'],
            '기관순매수(원)': df_inst['순매수거래대금']
        })
        
        # 쌍끌이 매수 (외국인 + 기관 합산)
        df_merged['쌍끌이순매수(원)'] = df_merged['외국인순매수(원)'] + df_merged['기관순매수(원)']
        
        # 합산 대금 기준 상위 N개 추출
        top_stocks = df_merged.sort_values(by='쌍끌이순매수(원)', ascending=False).head(top_n)
        return top_stocks
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def apply_technical_analysis(ticker, start_date, end_date):
    """단일 종목의 과거 데이터를 바탕으로 기술적 지표 계산"""
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: # 볼린저 밴드 계산을 위한 최소 데이터 확인
            return None
            
        # pandas_ta를 활용한 기술적 지표 계산
        df.ta.rsi(length=14, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        
        latest = df.iloc[-1]
        
        # 현재가, RSI, 볼린저 밴드 상/하단, 등락률 반환
        return {
            '현재가': latest['Close'],
            '전일비(%)': round(df['Change'].iloc[-1] * 100, 2) if 'Change' in df.columns else 0,
            'RSI(14)': round(latest['RSI_14'], 2),
            'BB_하단': round(latest['BBL_20_2.0'], 2),
            'BB_중심': round(latest['BBM_20_2.0'], 2),
            'BB_상단': round(latest['BBU_20_2.0'], 2)
        }
    except:
        return None

# --- UI 레이아웃 구성 ---
st.title("📈 Daniel's K-Market & Macro Dashboard")
st.markdown("객관적 수급 데이터와 기술적 분석을 결합한 투자 인사이트 시스템입니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 검색 설정")
today = datetime.today()

# 주말일 경우 가장 최근 금요일로 조정
if today.weekday() == 5:
    today -= timedelta(days=1)
elif today.weekday() == 6:
    today -= timedelta(days=2)

target_date = st.sidebar.date_input("기준일자 선택", today)
date_str = target_date.strftime("%Y%m%d")

market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

# 탭 구성
tab1, tab2 = st.tabs(["📊 거시경제(Macro) 동향", "🎯 수급 및 기술적 스캐닝 (종목 발굴)"])

# --- 탭 1: 거시경제 동향 ---
with tab1:
    st.subheader("글로벌 핵심 자산 동향 (금, 석유, 국채)")
    st.markdown("시장의 전반적인 유동성과 위험 선호도를 파악하기 위한 지표입니다.")
    
    macro_start = today - timedelta(days=180) # 6개월 데이터
    macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    if macro_data:
        cols = st.columns(2)
        for i, (name, series) in enumerate(macro_data.items()):
            col = cols[i % 2]
            with col:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=series.index, y=series.values, mode='lines', name=name, line=dict(color='#1f77b4')))
                fig.update_layout(title=name, xaxis_title="날짜", yaxis_title="가격/수익률", template="plotly_white", height=300, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("거시경제 데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요.")

# --- 탭 2: 수급 및 기술적 스캐닝 ---
with tab2:
    st.subheader(f"🔥 {target_date.strftime('%Y-%m-%d')} 기준 {market_type} 시장 주도주 스캐닝")
    st.markdown("당일 외국인/기관 쌍끌이 매수 상위 종목을 추출하고, 기술적 위치(RSI, 볼린저 밴드)를 분석합니다.")
    
    with st.spinner("KRX 수급 데이터 및 기술적 지표를 분석 중입니다. 약 10~20초 소요됩니다..."):
        # 1. 수급 상위 종목 추출
        top_df = get_top_institutions_foreigners(date_str, market=market_type, top_n=20)
        
        if top_df.empty:
            st.warning("선택하신 날짜의 데이터가 아직 업데이트되지 않았거나 휴장일입니다.")
        else:
            # 2. 기술적 지표 결합을 위한 리스트 생성
            results = []
            ta_start = target_date - timedelta(days=90) # TA 계산을 위한 과거 90일 데이터
            
            progress_bar = st.progress(0)
            
            for idx, (ticker, row) in enumerate(top_df.iterrows()):
                ta_data = apply_technical_analysis(ticker, ta_start.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d"))
                if ta_data:
                    combined_data = {
                        '종목코드': ticker,
                        '종목명': row['종목명'],
                        '현재가': ta_data['현재가'],
                        '전일비(%)': ta_data['전일비(%)'],
                        '외국인순매수(억)': round(row['외국인순매수(원)'] / 100000000, 1),
                        '기관순매수(억)': round(row['기관순매수(원)'] / 100000000, 1),
                        'RSI(14)': ta_data['RSI(14)'],
                        'BB하단': ta_data['BB_하단'],
                        'BB상단': ta_data['BB_상단']
                    }
                    
                    # 투자 판단 로직 (단순 참고용)
                    if ta_data['RSI(14)'] < 40 and ta_data['현재가'] <= ta_data['BB_하단'] * 1.05:
                        combined_data['기술적분석'] = "🔵 과매도/반등기대"
                    elif ta_data['RSI(14)'] > 70 or ta_data['현재가'] >= ta_data['BB_상단'] * 0.95:
                        combined_data['기술적분석'] = "🔴 과매수/조정주의"
                    else:
                        combined_data['기술적분석'] = "⚪ 추세형성중"
                        
                    results.append(combined_data)
                
                # 진행률 업데이트
                progress_bar.progress((idx + 1) / len(top_df))
            
            # 3. 최종 결과 출력
            if results:
                final_df = pd.DataFrame(results)
                
                # 데이터프레임 스타일링
                st.dataframe(
                    final_df.style.applymap(lambda x: 'color: red' if isinstance(x, str) and '🔴' in x else ('color: blue' if isinstance(x, str) and '🔵' in x else ''), subset=['기술적분석'])
                                  .format({"전일비(%)": "{:.2f}%", "현재가": "{:,.0f}"}),
                    use_container_width=True,
                    height=500
                )
                
                st.caption("※ 본 데이터는 장 마감 후 업데이트된 수치 기준이며, 기술적 분석 의견은 투자를 위한 절대적 지표가 아닌 참고용입니다.")
            else:
                st.error("종목 분석 중 오류가 발생했습니다.")
