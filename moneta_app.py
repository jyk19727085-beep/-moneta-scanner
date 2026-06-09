import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 캐싱을 통한 최적화 (거시 지표) ---
@st.cache_data(ttl=3600)
def get_macro_data(start_date, end_date):
    """거시경제 지표 데이터를 안정적으로 가져오는 함수"""
    macro_symbols = {
        'WTI 원유 (USD/bbl)': 'CL=F',
        '금 (USD/oz)': 'GC=F',
        '미국 10년물 국채 (%)': '^TNX',
        '한국 3년물 국채 (%)': 'KR3YT=RR'
    }
    
    data_dict = {}
    for name, symbol in macro_symbols.items():
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if not df.empty:
                data_dict[name] = df['Close']
        except Exception:
            pass 
    return data_dict

# --- [핵심] 수급(거래대금) 기반 모멘텀 스캐닝 (KRX 우회) ---
@st.cache_data(ttl=3600)
def get_momentum_stocks(market="KOSPI", top_n=15):
    """
    KRX IP 차단을 완벽 우회하기 위해, 당일 거래대금(자금 유입)과 
    상승률을 기반으로 주도주를 스캐닝하는 객관적 함수입니다.
    """
    try:
        # 시장 전체 상장 종목의 오늘자(또는 가장 최근 마감일) 데이터 스냅샷 획득
        df_list = fdr.StockListing(market)
        
        # 조건 1: 오늘 상승한 종목 (모멘텀)
        # 조건 2: 거래대금(Amount) 기준 내림차순 (외국인/기관 메이저 자금 유입의 증거)
        # 조건 3: ETF, 스팩(SPAC) 등 제외, 순수 주식만 필터링 (선택적)
        df_up = df_list[df_list['ChagesRatio'] > 0].sort_values('Amount', ascending=False).head(top_n)
        
        return df_up
    except Exception as e:
        return pd.DataFrame()

# --- 기술적 분석 엔진 (Pure Pandas) ---
@st.cache_data(ttl=3600)
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
st.markdown("객관적 자금 유입(거래대금)과 기술적 분석을 결합한 프로페셔널 퀀트 시스템")

# 사이드바
st.sidebar.header("⚙️ 스캐닝 설정")
market_type = st.sidebar.selectbox("스캐닝 시장 선택", ["KOSPI", "KOSDAQ"])

tab1, tab2 = st.tabs(["📊 거시(Macro) 동향", "🎯 자금유입/모멘텀 스캐닝"])

# --- 탭 1: 거시경제 동향 (가독성/안정성 극대화) ---
with tab1:
    st.subheader("글로벌 핵심 자산 동향 (최근 6개월)")
    today = datetime.today()
    macro_start = today - timedelta(days=180) 
    macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    if macro_data:
        # 모바일에 최적화된 2열 그리드 배치
        cols = st.columns(2)
        
        for i, (name, series) in enumerate(macro_data.items()):
            with cols[i % 2]:
                if len(series) > 1:
                    # 데이터 추출 (Pandas Series 호환성 완벽 대응)
                    current_val = float(series.iloc[-1])
                    prev_val = float(series.iloc[-2])
                    pct_change = ((current_val - prev_val) / prev_val) * 100
                    
                    # 지표 카드
                    st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{pct_change:.2f}%")
                    
                    # 네이티브 라인 차트 (절대 깨지지 않음)
                    # 차트 디자인을 위해 DataFrame으로 변환
                    chart_df = pd.DataFrame(series)
                    st.line_chart(chart_df, height=150)
    else:
        st.info("데이터를 수집 중입니다. (서버 상태에 따라 수 초 소요될 수 있습니다)")

# --- 탭 2: 자금 유입 모멘텀 스캐닝 ---
with tab2:
    st.subheader(f"🔍 {market_type} 메이저 자금 유입 스캐닝")
    st.markdown("당일 **거래대금 폭발** 및 **상승 모멘텀**이 발생한 주도주를 포착합니다.")
    
    if st.button("🚀 정밀 스캐닝 시작", type="primary", use_container_width=True):
        with st.spinner(f"{market_type} 시장의 자금 흐름과 기술적 지표를 분석 중입니다..."):
            
            # 거래소 IP 차단을 우회하는 FDR 모멘텀 스캐너 가동
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
                        # 억 단위 거래대금 계산
                        amount_100m = int(row['Amount'] / 100000000)
                        
                        combined = {
                            '종목명': row['Name'],
                            '현재가': f"{row['Close']:,.0f}",
                            '등락(%)': f"{row['ChagesRatio']:.2f}%",
                            '거래대금(억)': f"{amount_100m:,}",
                            'RSI': ta_data['RSI(14)']
                        }
                        
                        # 기술적 위치 판단 (객관적 지표)
                        if ta_data['RSI(14)'] < 45 and ta_data['현재가'] <= ta_data['BB하단'] * 1.05:
                            combined['차트위치'] = "🟢 바닥권 반등"
                        elif ta_data['RSI(14)'] > 70 or ta_data['현재가'] >= ta_data['BB상단'] * 0.95:
                            combined['차트위치'] = "🔴 단기 과열"
                        else:
                            combined['차트위치'] = "⚪ 상승 추세"
                            
                        results.append(combined)
                    
                    progress_bar.progress((idx + 1) / len(top_df))
                
                # 최종 데이터프레임 표출
                if results:
                    final_df = pd.DataFrame(results)
                    st.dataframe(
                        final_df.style.map(lambda x: 'color: #ff4b4b' if '🔴' in str(x) else ('color: #2ca02c' if '🟢' in str(x) else ''), subset=['차트위치']),
                        use_container_width=True,
                        hide_index=True
                    )
