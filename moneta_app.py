import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 (PC/모바일 반응형) ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 캐싱을 통한 로딩 속도 최적화 ---
@st.cache_data(ttl=3600)
def get_macro_data(start_date, end_date):
    """거시경제 지표 데이터를 가져오는 함수"""
    macro_symbols = {
        'WTI 원유': 'CL=F',
        '금 (Gold)': 'GC=F',
        '미국 10년물 국채': '^TNX',
        '한국 3년물 국채': 'KR3YT=RR'
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

@st.cache_data(ttl=3600)
def get_top_institutions_foreigners(base_date, market="KOSPI", top_n=20):
    """(핵심 수정) 유효한 데이터를 찾을 때까지 과거로 역추적하는 수급 스캐너"""
    current_date = base_date
    attempts = 0
    
    # 최대 7일 전까지 역추적하며 데이터가 있는 영업일을 찾음
    while attempts < 7:
        date_str = current_date.strftime("%Y%m%d")
        try:
            df_foreign = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "외국인")
            df_inst = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "기관합계")
            
            # 두 데이터가 모두 존재할 경우에만 처리
            if not df_foreign.empty and not df_inst.empty:
                df_merged = pd.DataFrame({
                    '종목명': df_foreign['종목명'],
                    '외국인순매수': df_foreign['순매수거래대금'],
                    '기관순매수': df_inst['순매수거래대금']
                })
                df_merged['쌍끌이합계'] = df_merged['외국인순매수'] + df_merged['기관순매수']
                
                # 순매수 금액 기준 상위 N개 추출
                top_stocks = df_merged.sort_values(by='쌍끌이합계', ascending=False).head(top_n)
                
                if not top_stocks.empty and top_stocks['쌍끌이합계'].max() > 0:
                    return top_stocks, current_date # 유효한 데이터프레임과 해당 날짜 반환
        except Exception:
            pass
        
        # 데이터가 없으면 하루 전으로 이동
        current_date -= timedelta(days=1)
        attempts += 1
        
    return pd.DataFrame(), None

@st.cache_data(ttl=3600)
def apply_technical_analysis(ticker, start_date, end_date):
    """단일 종목의 과거 데이터를 바탕으로 기술적 지표 계산 (Pure Pandas)"""
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: 
            return None
            
        # 1. RSI (14) 수기 계산
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # 2. 볼린저 밴드 (20, 2) 수기 계산
        df['BBM'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BBU'] = df['BBM'] + (std * 2)
        df['BBL'] = df['BBM'] - (std * 2)
        
        latest = df.iloc[-1]
        
        return {
            '현재가': latest['Close'],
            '전일비(%)': round(df['Change'].iloc[-1] * 100, 2) if 'Change' in df.columns else 0,
            'RSI(14)': round(latest['RSI_14'], 2),
            'BB하단': round(latest['BBL'], 2),
            'BB상단': round(latest['BBU'], 2)
        }
    except:
        return None

# --- UI 레이아웃 구성 ---
st.title("📈 Daniel's Quant Dashboard")
st.markdown("객관적 지표와 수급에 기반한 냉철한 투자 인사이트")

# 사이드바 설정
st.sidebar.header("⚙️ 스캐닝 설정")
today = datetime.today()
target_date = st.sidebar.date_input("기준일자 선택", today)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

tab1, tab2 = st.tabs(["📊 거시(Macro) 동향", "🎯 수급/기술적 스캐닝"])

# --- 탭 1: 거시경제 동향 (모바일 최적화) ---
with tab1:
    st.subheader("글로벌 핵심 자산 동향")
    
    macro_start = today - timedelta(days=180) 
    macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    if macro_data:
        # 1. 상단 지표 카드 (모바일에선 2열로 깔끔하게)
        cols = st.columns(2)
        normalized_data = {} # 차트를 위한 정규화 데이터 저장
        
        for i, (name, series) in enumerate(macro_data.items()):
            if len(series) > 1:
                current_val = series.iloc[-1].item() if isinstance(series.iloc[-1], pd.Series) else series.iloc[-1]
                prev_val = series.iloc[-2].item() if isinstance(series.iloc[-2], pd.Series) else series.iloc[-2]
                
                pct_change = ((current_val - prev_val) / prev_val) * 100
                
                # 지표 출력 (소수점 정리)
                cols[i % 2].metric(label=name, value=f"{current_val:,.2f}", delta=f"{pct_change:.2f}%")
                
                # 6개월 전(첫 데이터)을 100으로 맞춘 수익률 곡선 계산
                normalized_data[name] = (series / series.iloc[0]) * 100

        # 2. 단일 통합 차트 (가독성 극대화)
        st.markdown("<br><b>📈 6개월 자산별 상대 수익률 추이 (Base=100)</b>", unsafe_allow_html=True)
        fig = go.Figure()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for i, (name, norm_series) in enumerate(normalized_data.items()):
            # 시리즈가 DataFrame 형태일 경우 1차원으로 변환
            if isinstance(norm_series, pd.DataFrame):
                norm_series = norm_series.squeeze()
            fig.add_trace(go.Scatter(x=norm_series.index, y=norm_series.values, mode='lines', name=name, line=dict(color=colors[i % 4], width=2)))
            
        fig.update_layout(
            template="plotly_white", 
            height=350, 
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # 범례를 위로
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("현재 시장 데이터를 수집 중입니다.")

# --- 탭 2: 수급 및 기술적 스캐닝 ---
with tab2:
    st.subheader(f"🔥 {market_type} 쌍끌이 수급 스캐닝")
    
    if st.button("🚀 종목 스캐닝 시작", type="primary", use_container_width=True):
        with st.spinner("최근 유효한 수급 데이터를 역추적하여 분석 중입니다..."):
            # 1. 자동 역추적 알고리즘 적용
            top_df, valid_date = get_top_institutions_foreigners(target_date, market=market_type, top_n=15)
            
            if top_df.empty or valid_date is None:
                st.error("최근 7일 내에 유효한 수급 데이터를 찾지 못했습니다. 거래소 업데이트가 지연되고 있습니다.")
            else:
                # 실제로 데이터를 찾은 날짜 명시
                st.success(f"✅ 데이터 발견: **{valid_date.strftime('%Y년 %m월 %d일')}** 장 마감 기준 외국인/기관 쌍끌이 상위 종목입니다.")
                
                results = []
                ta_start = valid_date - timedelta(days=90) 
                
                progress_bar = st.progress(0)
                
                for idx, (ticker, row) in enumerate(top_df.iterrows()):
                    ta_data = apply_technical_analysis(ticker, ta_start.strftime("%Y-%m-%d"), valid_date.strftime("%Y-%m-%d"))
                    if ta_data:
                        combined = {
                            '종목명': row['종목명'],
                            '현재가': f"{ta_data['현재가']:,.0f}",
                            '등락(%)': f"{ta_data['전일비(%)']}%",
                            '순매수합계': f"{int(row['쌍끌이합계'] / 100000000):,}억", # 억원 단위 직관적 표기
                            'RSI': ta_data['RSI(14)']
                        }
                        
                        # 투자의견 객관적 도출
                        if ta_data['RSI(14)'] < 40 and ta_data['현재가'] <= ta_data['BB하단'] * 1.05:
                            combined['기술적의견'] = "🔵 반등기대"
                        elif ta_data['RSI(14)'] > 70 or ta_data['현재가'] >= ta_data['BB상단'] * 0.95:
                            combined['기술적의견'] = "🔴 조정주의"
                        else:
                            combined['기술적의견'] = "⚪ 추세형성"
                            
                        results.append(combined)
                    
                    progress_bar.progress((idx + 1) / len(top_df))
                
                # 결과 출력
                if results:
                    final_df = pd.DataFrame(results)
                    st.dataframe(
                        final_df.style.map(lambda x: 'color: #ff4b4b' if '🔴' in x else ('color: #1f77b4' if '🔵' in x else ''), subset=['기술적의견']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("기술적 지표를 계산할 수 있는 종목이 부족합니다.")
