import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="Quant Technical & Drawdown Dashboard", layout="wide")

# -------------------------------------------------------------
# 1. 관심종목 리스트 (미국 + 국내)
# -------------------------------------------------------------
DEFAULT_TICKERS = [
    # 미국 주요 종목
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "COHR", "QQQ", "SPY",
    # 국내 코스피 (.KS)
    "005930.KS", "000660.KS", "042670.KS", "028260.KS", "012330.KS", "005380.KS",
    # 국내 코스닥 (.KQ)
    "247540.KQ", "086520.KQ", "068270.KQ", "035900.KQ"
]

# -------------------------------------------------------------
# 2. 지표 계산 함수
# -------------------------------------------------------------
def calculate_indicators(df):
    close = df['Close']
    
    # 1) 이평선
    df['SMA5'] = close.rolling(5).mean()
    df['SMA20'] = close.rolling(20).mean()
    df['SMA60'] = close.rolling(60).mean()
    df['SMA120'] = close.rolling(120).mean()
    
    # 2) 볼린저밴드 (20일, 2-std)
    std = close.rolling(20).std()
    df['BB_Mid'] = df['SMA20']
    df['BB_Upper'] = df['BB_Mid'] + (std * 2)
    df['BB_Lower'] = df['BB_Mid'] - (std * 2)
    
    # 3) RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 4) MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 5) 거래량 20일 평균 대비 배수
    df['Vol_Ratio'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
    
    return df

# -------------------------------------------------------------
# 3. 데이터 일괄 수집 엔진 (5분 캐시)
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_all_market_data(ticker_list, peak_period_days=120):
    # 한 번에 50여 개 티커를 묶어서 일괄 다운로드
    data_raw = yf.download(ticker_list, period="1y", interval="1d", group_by='ticker', auto_adjust=True)
    
    summary_list = []
    processed_dfs = {}
    
    for t in ticker_list:
        try:
            df = data_raw[t].dropna(how="all") if len(ticker_list) > 1 else data_raw.dropna(how="all")
            if df.empty or len(df) < 30:
                continue
            
            df = calculate_indicators(df)
            processed_dfs[t] = df
            
            # 최근 데이터 추출
            cur_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            pct_change = ((cur_price - prev_price) / prev_price) * 100
            
            # 전고점 계산 (지정된 기간 내 최고가)
            peak_window = df.tail(peak_period_days)
            peak_price = float(peak_window['High'].max())
            drawdown = ((cur_price - peak_price) / peak_price) * 100
            
            rsi = float(df['RSI'].iloc[-1])
            macd = float(df['MACD'].iloc[-1])
            macd_sig = float(df['MACD_Signal'].iloc[-1])
            bb_lower = float(df['BB_Lower'].iloc[-1])
            vol_ratio = float(df['Vol_Ratio'].iloc[-1])
            
            # 하락 단계 산출
            buy_tier = "대기"
            if drawdown <= -30: buy_tier = "🚨 5차 (-30%)"
            elif drawdown <= -25: buy_tier = "🔴 4차 (-25%)"
            elif drawdown <= -20: buy_tier = "🟠 3차 (-20%)"
            elif drawdown <= -15: buy_tier = "🟡 2차 (-15%)"
            elif drawdown <= -10: buy_tier = "🟢 1차 (-10%)"
            
            # 매수/매도 추천 신호 생성
            signal = "중립"
            if buy_tier != "대기":
                if rsi <= 35 or cur_price <= bb_lower:
                    signal = "🔥 분할매수 적기 (과매도/볼밴하단)"
                else:
                    signal = "매수 구간 진입 (지표 대기)"
            elif rsi >= 70 or cur_price >= df['BB_Upper'].iloc[-1]:
                signal = "⚠️ 단기 과열 / 분할익절 고려"
                
            summary_list.append({
                "티커": t,
                "현재가": f"{cur_price:,.2f}" if ".KS" not in t and ".KQ" not in t else f"{int(cur_price):,}원",
                "전일대비(%)": round(pct_change, 2),
                "전고점": f"{peak_price:,.2f}" if ".KS" not in t and ".KQ" not in t else f"{int(peak_price):,}원",
                "전고대비(%)": round(drawdown, 2),
                "매수단계": buy_tier,
                "RSI": round(rsi, 1),
                "볼밴하단대비(%)": round(((cur_price - bb_lower) / bb_lower) * 100, 2),
                "거래량배수": f"{vol_ratio:.1f}x",
                "신호/추천": signal
            })
        except Exception:
            continue
            
    return pd.DataFrame(summary_list), processed_dfs

# -------------------------------------------------------------
# 4. 대시보드 UI
# -------------------------------------------------------------
st.title("📈 퀀트 기술적분석 & 전고점 낙폭 분할매수 대시보드")

with st.sidebar:
    st.header("⚙️ 설정")
    tickers_input = st.text_area("종목 티커 (쉼표로 구분)", value=", ".join(DEFAULT_TICKERS), height=150)
    current_tickers = [x.strip() for x in tickers_input.split(",") if x.strip()]
    peak_days = st.slider("전고점 산정 기간 (거래일 기준)", min_value=30, max_value=250, value=120, step=10)
    
    if st.button("🔄 실시간 데이터 갱신"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("50여 개 종목 시세 및 팩터 데이터 계산 중..."):
    df_summary, dict_dfs = fetch_all_market_data(current_tickers, peak_period_days=peak_days)

tab1, tab2 = st.tabs(["📋 전체 종목 스크리너", "📊 개별 종목 정밀 차트"])

# [탭 1: 스크리너]
with tab1:
    st.markdown(f"### 감시 종목 현황 ({len(df_summary)}개)")
    
    # 필터 옵션
    col1, col2 = st.columns(2)
    with col1:
        tier_filter = st.multiselect("매수 단계 필터", ["전체", "1차 (-10%)", "2차 (-15%)", "3차 (-20%)", "4차 (-25%)", "5차 (-30%)"], default=["전체"])
    with col2:
        signal_only = st.checkbox("매수 구간 진입 종목만 보기", value=False)
        
    filtered_df = df_summary.copy()
    if "전체" not in tier_filter:
        filtered_df = filtered_df[filtered_df["매수단계"].apply(lambda x: any(f in x for f in tier_filter))]
    if signal_only:
        filtered_df = filtered_df[filtered_df["매수단계"] != "대기"]
        
    st.dataframe(
        filtered_df.sort_values(by="전고대비(%)", ascending=True),
        use_container_width=True,
        hide_index=True
    )

# [탭 2: 개별 차트 상세 분석]
with tab2:
    selected_ticker = st.selectbox("종목 선택", current_tickers)
    
    if selected_ticker in dict_dfs:
        df = dict_dfs[selected_ticker].tail(180) # 최근 6개월 표시
        peak_val = df['High'].tail(peak_days).max()
        
        # 3단 서브플롯 (1: 캔들+볼밴+낙폭선, 2: MACD, 3: RSI)
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # 1) 메인 캔들 & 볼린저밴드 & 이평선
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(150,150,150,0.5)', dash='dash'), name='BB Upper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(150,150,150,0.5)', dash='dash'), fill='tonexty', fillcolor='rgba(200,200,200,0.05)', name='BB Lower'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.5), name='SMA 20'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA60'], line=dict(color='blue', width=1.5), name='SMA 60'), row=1, col=1)
        
        # 전고점 기준 분할매수 수평선 표시
        drawdown_levels = [(-10, "#10b981"), (-15, "#f59e0b"), (-20, "#f97316"), (-25, "#ef4444"), (-30, "#b91c1c")]
        for dd, color in drawdown_levels:
            target_price = peak_val * (1 + dd / 100)
            fig.add_hline(y=target_price, line_dash="dot", line_color=color, annotation_text=f"{dd}% ({target_price:,.1f})", row=1, col=1)
            
        # 2) MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan', width=1.5), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='red', width=1.2), name='Signal'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color='gray', name='Hist'), row=2, col=1)
        
        # 3) RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(height=800, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
