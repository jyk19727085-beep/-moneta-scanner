import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 캐싱을 통한 최적화 (거시 지표) ---
# 실시간성을 높이기 위해 캐시 유지 시간을 30분(1800초)으로 단축
@st.cache_data(ttl=1800)
def get_macro_data(start_date, end_date):
    """거시경제 지표 데이터를 안정적으로 가져오는 함수"""
    # 미국 및 한국의 장/단기 국채 지표 완벽 반영
    macro_symbols = {
        'WTI 원유 (USD/bbl)': 'CL=F',
        '금 (USD/oz)': 'GC=F',
        '미국 2년물 국채 (%)': '^US2Y',     # 미 단기 금리 (유동성 민감)
        '미국 10년물 국채 (%)': '^TNX',      # 미 장기 금리 (경기 전망)
        '한국 2년물 국채 (%)': 'KR2YT=RR',   # 한 단기 금리 (야후 지원 유동적)
        '한국 3년물 국채 (%)': 'KR3YT=RR',   # 한 단기 벤치마크
        '한국 10년물 국채 (%)': 'KR10YT=RR'  # 한 장기 벤치마크
    }
    
    data_dict = {}
    for name, symbol in macro_symbols.items():
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if not df.empty:
                # 다중 인덱스로 들어오는 데이터를 1차원으로 강제 압축(squeeze)하여 에러 영구 차단
                data_dict[name] = df['Close'].squeeze()
        except Exception:
            pass 
    return data_dict

# --- 수급(거래대금) 기반 모멘텀 실시간/당일 마감 스캐닝 ---
@st.cache_data(ttl=1800)
def get_momentum_stocks(market="KOSPI", top_n=15):
    """당일(실시간) 거래대금 및 상승률 기반 주도주 스캐닝"""
    try:
        # 네이버 금융 실시간 시세 보드 기반 데이터 스크래핑 (데이터 지연 없음)
        df_list = fdr.StockListing(market)
        
        # 조건 1: 상승 종목 (ChagesRatio > 0)
        # 조건 2: 당일 거래대금(Amount) 기준 내림차순 정렬 (자금 유입 증거)
        df_up = df_list[df_list['ChagesRatio'] > 0].sort_values('Amount', ascending=False).head(top_n)
        return df_up
    except Exception as e:
        return pd.DataFrame()

# --- 기술적 분석 엔진 (Pure Pandas) ---
@st.cache_data(ttl=1800)
def apply_technical_analysis(ticker, start_date, end_date):
    """기술적 지표 계산"""
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: return None
            
        # RSI (14)
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # 볼린저 밴드 (20, 2)
        df['BBM'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BBU'] = df['BBM'] + (std * 2)
        df['BBL'] = df['BBM'] - (std * 2)
        
        latest = df.iloc[-1]
        return {
            '현재가': latest['Close'],
            'RSI(14)': round(latest['RSI_14'], 2),
            'BB하단': round(latest['BBL'], 2),
            'BB상단': round(latest['BBU'], 2)
        }
    except:
        return None

# --- UI 레이아웃 ---
st.title("📈 Daniel's Quant Dashboard")
st.markdown("객관적 자금 유입(실시간/당일)과 기술적 분석을 결합한 프로페셔널 퀀트 시스템")

# 사이드바
st.sidebar.header("⚙️ 스캐닝 설정")
market_type = st.sidebar.selectbox("스캐닝 시장 선택", ["KOSPI", "KOSDAQ"])

tab1, tab2 = st.tabs(["📊 거시(Macro) 동향", "🎯 자금유입/모멘텀 스캐닝"])

# --- 탭 1: 거시경제 동향 ---
with tab1:
    st.subheader("글로벌 핵심 자산 및 장·단기 국채 금리")
    today = datetime.today()
    macro_start = today - timedelta(days=180) 
    macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    if macro_data:
        cols = st.columns(2)
        
        for i, (name, series) in enumerate(macro_data.items()):
            with cols[i % 2]:
                if len(series) > 1:
                    # 표 형태(Series)로 들어올 경우 순수 숫자(Scalar)만 안전하게 추출
                    val_cur = series.iloc[-1]
                    val_prv = series.iloc[-2]
                    
                    if isinstance(val_cur, pd.Series): val_cur = val_cur.iloc[0]
                    if isinstance(val_prv, pd.Series): val_prv = val_prv.iloc[0]
                    
                    current_val = float(val_cur)
                    prev_val = float(val_prv)
                    
                    # 수학적 오류 사전 차단
                    pct_change = ((current_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0.0
                    
                    st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{pct_change:.2f}%")
                    
                    chart_df = pd.DataFrame(series)
                    st.line_chart(chart_df, height=150)
    else:
        st.info("데이터를 수집 중입니다. (서버 상태에 따라 수 초 소요될 수 있습니다)")

# --- 탭 2: 자금 유입 모멘텀 스캐닝 ---
with tab2:
    st.subheader(f"🔍 {market_type} 메이저 자금 유입 스캐닝")
    st.markdown("당일 **거래대금 폭발** 및 **상승 모멘텀**이 발생한 주도주를 포착합니다. (실시간/당일 마감 완벽 반영)")
    
    if st.button("🚀 정밀 스캐닝 시작", type="primary", use_container_width=True):
        with st.spinner(f"{market_type} 시장의 자금 흐름과 기술적 지표를 분석 중입니다..."):
            
            top_df = get_momentum_stocks(market=market_type, top_n=15)
            
            if top_df.empty:
                st.error("데이터를 불러오지 못했습니다. 장이 열리지 않았거나 통신 오류입니다.")
            else:
                st.success("✅ 메이저 자금(거래대금 상위)이 강하게 유입되며 상승한 주도주 포착 완료")
                
                results = []
                ta_start = datetime.today() - timedelta(days=90) 
                progress_bar = st.progress(0)
                
                for idx, (index, row) in enumerate(top_df.iterrows()):
                    ticker = row['Code']
                    ta_data = apply_technical_analysis(ticker, ta_start.strftime("%Y-%m-%d"), datetime.today().strftime("%Y-%m-%d"))
                    
                    if ta_data:
                        amount_100m = int(row['Amount'] / 100000000)
                        
                        combined = {
                            '종목명': row['Name'],
                            '현재가': f"{row['Close']:,.0f}",
                            '등락(%)': f"{row['ChagesRatio']:.2f}%",
                            '거래대금(억)': f"{amount_100m:,}",
                            'RSI': ta_data['RSI(14)']
                        }
                        
                        if ta_data['RSI(14)'] < 45 and ta_data['현재가'] <= ta_data['BB하단'] * 1.05:
                            combined['차트위치'] = "🟢 바닥권 반등"
                        elif ta_data['RSI(14)'] > 70 or ta_data['현재가'] >= ta_data['BB상단'] * 0.95:
                            combined['차트위치'] = "🔴 단기 과열"
                        else:
                            combined['차트위치'] = "⚪ 상승 추세"
                            
                        results.append(combined)
                    
                    progress_bar.progress((idx + 1) / len(top_df))
                
                if results:
                    final_df = pd.DataFrame(results)
                    st.dataframe(
                        final_df.style.map(lambda x: 'color: #ff4b4b' if '🔴' in str(x) else ('color: #2ca02c' if '🟢' in str(x) else ''), subset=['차트위치']),
                        use_container_width=True,
                        hide_index=True
                    )
