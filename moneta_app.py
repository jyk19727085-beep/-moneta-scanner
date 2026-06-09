def apply_technical_analysis(ticker, start_date, end_date):
    """단일 종목의 과거 데이터를 바탕으로 기술적 지표 계산 (Pure Pandas)"""
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        if len(df) < 20: # 볼린저 밴드 계산을 위한 최소 데이터 확인
            return None
            
        # 1. RSI (14) 수기 계산
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        
        # 지수이동평균(EMA) 방식 적용
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # 2. 볼린저 밴드 (20, 2) 수기 계산
        df['BBM_20_2.0'] = df['Close'].rolling(window=20).mean() # 중심선
        std = df['Close'].rolling(window=20).std() # 표준편차
        df['BBU_20_2.0'] = df['BBM_20_2.0'] + (std * 2) # 상단선
        df['BBL_20_2.0'] = df['BBM_20_2.0'] - (std * 2) # 하단선
        
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
