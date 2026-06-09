import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(page_title="Daniel's Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 캐싱을 통한 최적화 ---
@st.cache_data(ttl=3600)
def get_macro_data(start_date, end_date):
    """거시경제 지표 데이터를 가져오는 함수"""
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

@st.cache_data(ttl=3600)
def get_institutional_foreign_buys(base_date, market="KOSPI", top_n=20):
    """외국인, 기관, 쌍끌이 수급을 개별적으로 포착하는 고도화 엔진"""
    current_date = base_date
    attempts = 0
    
    while attempts < 7:
        date_str = current_date.strftime("%Y%m%d")
        try:
            # KRX 해외 IP 차단을 대비한 예외 처리 포함
            df_f = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "외국인")
            df_i = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "기관합계")
            
            if not df_f.empty and not df_i.empty:
                # 데이터 병합 (어느 한쪽만 산 종목도 포함하기 위해 인덱스 기준 병합)
                df_merged = pd.DataFrame(index=df_f.index.union(df_i.index))
                df_merged['종목명'] = df_f['종목명'].combine_first(df_i['종목명'])
                df_merged['외국인순매수'] = df_f['순매수거래대금'].fillna(0)
                df_merged['기관순매수'] = df_i['순매수거래대금'].fillna(0)
                df_merged['총합계'] = df_merged['외국인순매수'] + df_merged['기관순매수']
                
                # 수급 주체별 태그 달기
                def tag_buyer(row):
                    if row['외국인순매수'] > 0 and row['기관순매수'] > 0:
                        return "🔥 쌍끌이"
                    elif row['외국인순매수'] > 0:
                        return "🔵 외국인"
                    elif row['기관순매수'] > 0:
                        return "🔴 기관"
                    else:
                        return "⚪ 관망"
                        
                df_merged['수급주체'] = df_merged.apply(tag_buyer, axis=1)
                
                # 총합계 기준 상위 N개 추출 (매도 우위 제외)
                top_stocks = df_merged[df_merged['총합계'] > 0].sort_values(by='총합계', ascending=False).head(top_n)
                
                if not top_stocks.empty:
                    return top_stocks, current_date
        except Exception:
            pass
            
        current_date -= timedelta(days=1)
        attempts += 1
        
    return pd.DataFrame(), None

@st.cache_data(ttl=3600)
def apply_technical_analysis(ticker, start_date, end_date):
    """기술적 지표 계산 (Pandas 수기 계산)"""
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: return None
            
        # RSI
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # 볼린저 밴드
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

# --- UI 레이아웃 ---
st.title("📈 Daniel's Quant Dashboard")
st.markdown("객관적 지표와 입체적 수급 분석을 결합한 프로페셔널 퀀트 시스템")

# 사이드바
st.sidebar.header("⚙️ 스캐닝 설정")
today = datetime.today()
target_date = st.sidebar.date_input("기준일자 선택", today)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

tab1, tab2 = st.tabs(["📊 거시(Macro) 독립 차트", "🎯 수급주체별 스캐닝"])

# --- 탭 1: 거시경제 분리형 차트 (가독성 극대화) ---
with tab1:
    st.subheader("글로벌 핵심 자산 동향 (최근 6개월)")
    macro_start = today - timedelta(days=180) 
    macro_data = get_macro_data(macro_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    if macro_data:
        # 모바일에 최적화된 2열 그리드 배치
        cols = st.columns(2)
        chart_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for i, (name, series) in enumerate(macro_data.items()):
            with cols[i % 2]:
                # 가격 변화량 카드
                current_val = series.iloc[-1].item() if isinstance(series.iloc[-1], pd.Series) else series.iloc[-1]
                prev_val = series.iloc[-2].item() if isinstance(series.iloc[-2], pd.Series) else series.iloc[-2]
                pct_change = ((current_val - prev_val) / prev_val) * 100
                st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{pct_change:.2f}%")
                
                # 개별 미니 차트 (가독성 최고)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=series.index, y=series.values, mode='lines', line=dict(color=chart_colors[i], width=2)))
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=120,
                    xaxis=dict(visible=False), # X축 텍스트 숨김 (깔끔함 유지)
                    yaxis=dict(visible=False), # Y축 텍스트 숨김
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("데이터를 수집 중입니다.")

# --- 탭 2: 입체적 수급 스캐닝 ---
with tab2:
    st.subheader(f"🔍 {market_type} 세력 수급 스캐닝")
    st.markdown("KRX 데이터 기반: 쌍끌이, 외국인, 기관 단독 매수세력 포착")
    
    if st.button("🚀 정밀 스캐닝 시작", type="primary", use_container_width=True):
        with st.spinner("해외 IP 우회 및 수급 세력을 분석 중입니다..."):
            top_df, valid_date = get_institutional_foreign_buys(target_date, market=market_type, top_n=20)
            
            if top_df.empty or valid_date is None:
                st.error("⚠️ 한국거래소(KRX) 서버가 현재 클라우드 접근을 제한하고 있거나 데이터가 없습니다. 평일 장 마감 이후에 다시 시도해 주십시오.")
            else:
                st.success(f"✅ 포착일자: **{valid_date.strftime('%Y-%m-%d')}** (KRX 장 마감 데이터)")
                
                results = []
                ta_start = valid_date - timedelta(days=90) 
                progress_bar = st.progress(0)
                
                for idx, (ticker, row) in enumerate(top_df.iterrows()):
                    ta_data = apply_technical_analysis(ticker, ta_start.strftime("%Y-%m-%d"), valid_date.strftime("%Y-%m-%d"))
                    if ta_data:
                        combined = {
                            '종목명': row['종목명'],
                            '수급주체': row['수급주체'],
                            '현재가': f"{ta_data['현재가']:,.0f}",
                            '총순매수(억)': f"{int(row['총합계'] / 100000000):,}",
                            'RSI': ta_data['RSI(14)']
                        }
                        
                        # 기술적 위치 판단
                        if ta_data['RSI(14)'] < 45 and ta_data['현재가'] <= ta_data['BB하단'] * 1.05:
                            combined['차트위치'] = "🟢 바닥권"
                        elif ta_data['RSI(14)'] > 70 or ta_data['현재가'] >= ta_data['BB상단'] * 0.95:
                            combined['차트위치'] = "🔴 과열권"
                        else:
                            combined['차트위치'] = "⚪ 허리(추세)"
                            
                        results.append(combined)
                    
                    progress_bar.progress((idx + 1) / len(top_df))
                
                if results:
                    final_df = pd.DataFrame(results)
                    st.dataframe(
                        final_df,
                        use_container_width=True,
                        hide_index=True
                    )
