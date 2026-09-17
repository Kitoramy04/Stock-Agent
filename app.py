import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AlphaPulse 포트폴리오 & 퀀트 낙폭감시", layout="wide")

# -------------------------------------------------------------
# 1. 영구 저장된 종목 마스터 딕셔너리 (종목명: 티커)
# -------------------------------------------------------------
KR_STOCKS_MASTER = {
    "LS": "006260.KS",
    "두산에너빌리티": "034020.KS",
    "하이브": "352820.KS",
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LS ELECTRIC": "010120.KS",
    "HD현대일렉트릭": "267260.KS",
    "효성중공업": "298040.KS",
    "LS마린솔루션": "199050.KQ",
    "LS에코에너지": "229640.KS",
    "SK오션플랜트": "100090.KS",
    "SK이터닉스": "475150.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성SDI": "006400.KS",
    "율촌화학": "008730.KS",
    "서진시스템": "178320.KQ",
    "JYP Ent.": "035900.KQ",
    "에스엠": "041510.KQ",
    "와이지엔터테인먼트": "122870.KQ",
    "코리아써키트": "007810.KS",
    "현대차": "005380.KS",
    "에스엘": "005850.KS",
    "한국전력": "015760.KS",
    "한전기술": "052690.KS",
    "에코프로": "086520.KQ",
    "한화에어로스페이스": "012450.KS",
    "LIG넥스원": "079550.KS",
    "현대로템": "064350.KS",
    "HD현대중공업": "329180.KS",
    "한화오션": "042660.KS",
    "에이직랜드": "445090.KQ",
    "삼성물산": "028260.KS",
    "삼성생명": "032830.KS",
    "DSC인베스트먼트": "241520.KQ",
    "씨에스윈드": "112610.KS",
    "에이디테크놀로지": "200710.KQ",
    "디앤디파마텍": "347850.KQ",
    "키움증권": "039490.KS",
    "LS증권": "078020.KS",
    "미래에셋증권": "006800.KS"
}

US_STOCKS_MASTER = {
    "보잉 (BA)": "BA",
    "유나이티드 항공 (UAL)": "UAL",
    "아메리칸 항공 (AAL)": "AAL",
    "SK하이닉스 ADR (SKHY)": "SKHY",
    "지멘스 에너지 ADR (SMERY)": "SMERY",
    "무그 (MOG-A)": "MOG-A",
    "우드워드 (WWD)": "WWD",
    "스페이스 ETF (SPCX)": "SPCX",
    "인텔 (INTC)": "INTC",
    "패브리넷 (FN)": "FN",
    "코닝 (GLW)": "GLW",
    "로켓랩 (RKLB)": "RKLB",
    "팔란티어 (PLTR)": "PLTR",
    "센트러스 에너지 (LEU)": "LEU",
    "제너럴 모터스 (GM)": "GM",
    "이튼 (ETN)": "ETN",
    "넥스테라 에너지 (NEE)": "NEE",
    "콘스텔레이션 에너지 (CEG)": "CEG",
    "시에나 (CIEN)": "CIEN",
    "TSMC ADR (TSM)": "TSM",
    "오라클 (ORCL)": "ORCL",
    "버티브 홀딩스 (VRT)": "VRT",
    "콴타 서비스 (PWR)": "PWR",
    "페르미 (FRMI)": "FRMI",
    "모놀리식 파워 (MPWR)": "MPWR",
    "GE 버노바 (GEV)": "GEV",
    "마이크론 (MU)": "MU",
    "비트코인 (BTC-USD)": "BTC-USD",
    "테슬라 (TSLA)": "TSLA",
    "엔비디아 (NVDA)": "NVDA",
    "브로드컴 (AVGO)": "AVGO",
    "바이코 (VICR)": "VICR",
    "루멘텀 (LITE)": "LITE",
    "하우멧 에어로스페이스 (HWM)": "HWM",
    "BWX 테크놀로지스 (BWXT)": "BWXT",
    "블룸 에너지 (BE)": "BE",
    "뉴스케일 파워 (SMR)": "SMR",
    "오클로 (OKLO)": "OKLO",
    "제보 (GEVO)": "GEVO",
    "킨더 모건 (KMI)": "KMI",
    "코히런트 (COHR)": "COHR",
    "AMD": "AMD",
    "셈프라 에너지 (SRE)": "SRE",
    "아토메라 (ATOM)": "ATOM",
    "도어대시 (DASH)": "DASH",
    "앨버말 (ALB)": "ALB",
    "코인베이스 (COIN)": "COIN",
    "ASML": "ASML",
    "슈나이더 일렉트릭 ADR (SBGSY)": "SBGSY",
    "ABB ADR (ABBNY)": "ABBNY",
    "프리스미안 ADR (PRYMY)": "PRYMY",
    "베스타스 ADR (VWSYF)": "VWSYF",
    "롤스로이스 ADR (RYCEY)": "RYCEY"
}

# -------------------------------------------------------------
# 2. 지표 계산 엔진
# -------------------------------------------------------------
def calculate_indicators(df):
    close = df['Close']
    df['SMA5'] = close.rolling(5).mean()
    df['SMA20'] = close.rolling(20).mean()
    df['SMA60'] = close.rolling(60).mean()
    df['SMA120'] = close.rolling(120).mean()
    
    std = close.rolling(20).std()
    df['BB_Mid'] = df['SMA20']
    df['BB_Upper'] = df['BB_Mid'] + (std * 2)
    df['BB_Lower'] = df['BB_Mid'] - (std * 2)
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    df['Vol_Ratio'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
    return df

# -------------------------------------------------------------
# 3. 데이터 일괄 수집 엔진 (5분 캐시)
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_market_data(stock_dict, peak_period_days=120):
    tickers = list(stock_dict.values())
    inv_map = {v: k for k, v in stock_dict.items()}
    
    data_raw = yf.download(tickers, period="1y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
    
    summary_list = []
    processed_dfs = {}
    
    for ticker in tickers:
        name = inv_map[ticker]
        try:
            df = data_raw[ticker].dropna(how="all") if len(tickers) > 1 else data_raw.dropna(how="all")
            if df.empty or len(df) < 25:
                continue
            
            df = calculate_indicators(df)
            processed_dfs[name] = df
            
            cur_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            pct_change = ((cur_price - prev_price) / prev_price) * 100
            
            peak_window = df.tail(peak_period_days)
            peak_price = float(peak_window['High'].max())
            drawdown = ((cur_price - peak_price) / peak_price) * 100
            
            rsi = float(df['RSI'].iloc[-1])
            bb_lower = float(df['BB_Lower'].iloc[-1])
            vol_ratio = float(df['Vol_Ratio'].iloc[-1])
            
            buy_tier = "정상"
            if drawdown <= -30: buy_tier = "🚨 5차 (-30%)"
            elif drawdown <= -25: buy_tier = "🔴 4차 (-25%)"
            elif drawdown <= -20: buy_tier = "🟠 3차 (-20%)"
            elif drawdown <= -15: buy_tier = "🟡 2차 (-15%)"
            elif drawdown <= -10: buy_tier = "🟢 1차 (-10%)"
            
            signal = "중립"
            if buy_tier != "정상":
                if rsi <= 35 or cur_price <= bb_lower:
                    signal = "🔥 분할매수 적기 (과매도)"
                else:
                    signal = "매수 구간 (추가확인)"
            elif rsi >= 70 or cur_price >= df['BB_Upper'].iloc[-1]:
                signal = "⚠️ 단기 과열 / 분할익절"
                
            is_kr = ".KS" in ticker or ".KQ" in ticker
            price_fmt = f"{int(cur_price):,}원" if is_kr else f"${cur_price:,.2f}"
            peak_fmt = f"{int(peak_price):,}원" if is_kr else f"${peak_price:,.2f}"
            
            summary_list.append({
                "종목명": name,
                "현재가": price_fmt,
                "전일대비(%)": round(pct_change, 2),
                "전고점": peak_fmt,
                "전고대비(%)": round(drawdown, 2),
                "기계적 매수단계": buy_tier,
                "RSI(14)": round(rsi, 1),
                "볼밴하단괴리(%)": round(((cur_price - bb_lower) / bb_lower) * 100, 2),
                "거래량배수": f"{vol_ratio:.1f}x",
                "추천 신호": signal
            })
        except Exception:
            continue
            
    return pd.DataFrame(summary_list), processed_dfs

# -------------------------------------------------------------
# 4. 차트 렌더링 헬퍼 함수
# -------------------------------------------------------------
def render_stock_chart(df, name, peak_days):
    plot_df = df.tail(150)
    peak_val = plot_df['High'].tail(peak_days).max()
    
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # 1) 메인 캔들 & 볼린저밴드 & 이평선
    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='가격'), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['BB_Upper'], line=dict(color='rgba(150,150,150,0.5)', dash='dash'), name='볼밴 상단'), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['BB_Lower'], line=dict(color='rgba(150,150,150,0.5)', dash='dash'), fill='tonexty', fillcolor='rgba(200,200,200,0.05)', name='볼밴 하단'), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA20'], line=dict(color='orange', width=1.5), name='20일선'), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA60'], line=dict(color='blue', width=1.5), name='60일선'), row=1, col=1)
    
    # 낙폭 수평선 (-10% ~ -30%)
    levels = [(-10, "#10b981"), (-15, "#f59e0b"), (-20, "#f97316"), (-25, "#ef4444"), (-30, "#b91c1c")]
    for dd, color in levels:
        target = peak_val * (1 + dd / 100)
        fig.add_hline(y=target, line_dash="dot", line_color=color, annotation_text=f"{dd}% ({target:,.1f})", row=1, col=1)
        
    # 2) MACD
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD'], line=dict(color='cyan', width=1.5), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD_Signal'], line=dict(color='red', width=1.2), name='시그널'), row=2, col=1)
    fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['MACD_Hist'], marker_color='gray', name='오실레이터'), row=2, col=1)
    
    # 3) RSI
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    fig.update_layout(height=750, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=30, b=20), title=f"<b>{name}</b> 기술적 분석 차트")
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# 5. UI 메인 대시보드
# -------------------------------------------------------------
st.title("📊 AlphaPulse 기술적 분석 & 전고 낙폭 분할매수 대시보드")

with st.sidebar:
    st.header("⚙️ 분석 기준 설정")
    peak_days = st.slider("전고점 산정 기간 (거래일)", min_value=30, max_value=250, value=120, step=10, help="최근 120거래일(약 6개월) 내 최고가를 기준으로 낙폭을 계산합니다.")
    if st.button("🔄 실시간 시세 즉시 갱신"):
        st.cache_data.clear()
        st.rerun()

market_mode = st.radio("🌍 시장 선택", ["🇰🇷 국내 주식", "🇺🇸 미국 / 해외 주식"], horizontal=True)

if market_mode == "🇰🇷 국내 주식":
    target_dict = KR_STOCKS_MASTER
    title_suffix = "국내 코스피 / 코스닥"
else:
    target_dict = US_STOCKS_MASTER
    title_suffix = "미국 및 해외 ADR"

with st.spinner(f"{title_suffix} {len(target_dict)}개 종목 데이터 분석 중..."):
    df_summary, dict_dfs = fetch_market_data(target_dict, peak_period_days=peak_days)

tab1, tab2 = st.tabs([f"📋 {title_suffix} 전종목 스크리너", "📈 개별 종목 정밀 차트"])

with tab1:
    col1, col2 = st.columns()  # 수정 완료된 부분
    with col1:
        st.subheader(f"총 {len(df_summary)}개 감시 종목 현황")
    with col2:
        buy_only = st.checkbox("🔥 분할매수 구간 진입 종목만 보기 (-10% 이하)", value=False)
        
    display_df = df_summary.copy()
    if buy_only:
        display_df = display_df[display_df["기계적 매수단계"] != "정상"]
        
    if not display_df.empty:
        st.dataframe(
            display_df.sort_values(by="전고대비(%)", ascending=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("조건에 부합하는 종목이 없습니다.")

with tab2:
    if len(dict_dfs) > 0:
        selected_name = st.selectbox("분석할 종목을 선택하세요", list(dict_dfs.keys()))
        if selected_name in dict_dfs:
            render_stock_chart(dict_dfs[selected_name], selected_name, peak_days)
    else:
        st.warning("표시할 수 있는 종목 데이터가 없습니다.")
