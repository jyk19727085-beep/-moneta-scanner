import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from datetime import datetime, timedelta
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 안전한 숫자 추출을 위한 방어 함수 ---
def extract_scalar(val):
    try:
        if isinstance(val, pd.Series): return float(val.iloc[0])
        elif isinstance(val, (list, tuple)): return float(val[0])
        else: return float(val)
    except:
        return 0.0

# --- 재시도(Retry) 로직이 탑재된 하이브리드 수집 엔진 ---
def fetch_with_retry(symbol, start_date, end_date, engine='yf', retries=3):
    for attempt in range(retries):
        try:
            if engine == 'yf':
                df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            else:
                df = fdr.DataReader(symbol, start_date, end_date)
                
            if df is not None and not df.empty and len(df) >= 2:
                return df['Close'].dropna().squeeze()
        except Exception:
            time.sleep(1)
    return None

@st.cache_data(ttl=1800)
def get_macro_data(start_date, end_date):
    data_dict = {}
    
    yf_symbols = {
        '금 (USD/oz)': 'GC=F',
        'WTI 원유 (USD/bbl)': 'CL=F',
        '미국 10년물 국채 (%)': '^TNX',
        '미국 2년물 국채 (%)': '^US2Y',
        '한국 10년물 국채 (%)': 'KR10YT=RR',
        '한국 2년물 국채 (%)': 'KR2YT=RR'
    }
    
    for name, symbol in yf_symbols.items():
        result = fetch_with_retry(symbol, start_date, end_date, engine='yf')
        if result is not None:
            data_dict[name] = result
            
    fdr_symbols = {
        '미국 10년물 국채 (%)': 'US10YT',
        '미국 2년물 국채 (%)': 'US2YT',
        '한국 10년물 국채 (%)': 'KR10YT',
        '한국 2년물 국채 (%)': 'KR2YT'
    }
    
    for name, symbol in fdr_symbols.items():
        if name not in data_dict or len(data_dict.get(name, [])) < 2:
            result = fetch_with_retry(symbol, start_date, end_date, engine='fdr')
            if result is not None:
                data_dict[name] = result
                
    return data_dict

# --- 수급 기반 모멘텀 스캐닝 ---
@st.cache_data(ttl=1800)
def get_momentum_stocks(market="KOSPI", top_n=15):
    try:
        df_list = fdr.StockListing(market)
        df_up = df_list[df_list['ChagesRatio'] > 0].sort_values('Amount', ascending=False).head(top_n)
        return df_up
    except:
        return pd.DataFrame()

# --- 기술적 분석 엔진 ---
@st.cache_data(ttl=1800)
def apply_technical_analysis(ticker, start_date, end_date):
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: return None
            
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

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

# --- UI를 그리는 공통 함수 (코드 중복 방지 및 모바일 방어) ---
def render_macro_card(name, macro_data):
    if name in macro_data and len(macro_data[name]) >= 2:
        series = macro_data[name]
        current_val = extract_scalar(series.iloc[-1])
        prev_val = extract_scalar(series.iloc[-2])
        
        pct_change = ((current_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0.0
        
        st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{pct_change:.2f}%")
        chart_df = pd.DataFrame(series)
        st.line_chart(chart_df, height=120)
    else:
        st.metric(label=name, value="수집 지연", delta="-")
        st.markdown(
            "<div style='height: 120px; display: flex; align-items: center; justify-content: center; "
            "color: gray; font-size: 0.8em; border: 1px dashed #444; border-radius: 5px;'>"
            "서버 일시 차단(재시도 중)</div>", 
            unsafe_allow_html=True
        )

# --- UI 레이아웃 시작 ---
st.title("📈 Daniel's Quant Dashboard")
st.markdown("객관적 자금 유입과 입체적 장단기 스프레드를 결합한 시스템")

st.sidebar.header("⚙️ 스캐닝 설정")
market_type = st.sidebar.selectbox("스캐닝 시장 선택", ["KOSPI", "KOSDAQ"])

tab1, tab2 = st.tabs(["📊 글로벌 거시 및 국채 금리", "🎯 자금유입/모멘텀 스캐닝"])

# --- 탭 1: 거시경제 동향 ---
with tab1:
    st.subheader("글로벌 핵심 자산 및 장·단기 국채 스프레드")
    st.markdown("10년물(좌)-2년물(우) 배치를 통해 금리 역전 현상을 즉각 확인합니다.")
    
    # 💡 [핵심] 가로줄(Row) 단위로 묶어서 모바일 환경에서도 절대 순서가 꼬이지 않도록 뼈대 재구축
    ordered_rows = [
        ('금 (USD/oz)', 'WTI 원유 (USD/bbl)'),           # 1행
        ('미국 10년물 국채 (%)', '미국 2년물 국채 (%)'),  # 2행
        ('한국 10년물 국채 (%)', '한국 2년물 국채 (%)')   # 3행
    ]
    
    today = datetime.today()
    macro_start = today - timedelta(days=180) 
    
    with st.spinner("다중 우회 엔진을 통해 글로벌 데이터를 수집 중입니다..."):
        macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        
        # 가로줄(Row) 단위로 화면에 출력 (PC는 좌우, 모바일은 완벽한 상하 순서 보장)
        for left_item, right_item in ordered_rows:
            col1, col2 = st.columns(2)
            with col1:
                render_macro_card(left_item, macro_data)
            with col2:
                render_macro_card(right_item, macro_data)
            st.write("---") # 각 행을 구분하는 연한 실선 추가 (가독성 향상)

# --- 탭 2: 자금 유입 모멘텀 스캐닝 ---
with tab2:
    st.subheader(f"🔍 {market_type} 메이저 자금 유입 스캐닝")
    
    if st.button("🚀 정밀 스캐닝 시작", type="primary", use_container_width=True):
        with st.spinner(f"{market_type} 시장의 자금 흐름을 분석 중입니다..."):
            top_df = get_momentum_stocks(market=market_type, top_n=15)
            
            if top_df.empty:
                st.error("데이터를 불러오지 못했습니다. 통신 오류입니다.")
            else:
                st.success("✅ 자금 유입 주도주 포착 완료")
                
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
