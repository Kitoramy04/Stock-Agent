import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

st.set_page_config(page_title="AlphaPulse Quant Terminal", layout="wide")

WATCHLIST_FILE = "user_watchlist.json"

# -------------------------------------------------------------
# 1. 초기 기본 종목 마스터
# -------------------------------------------------------------
DEFAULT_KR_STOCKS = {
    "LS": "006260.KS", "두산에너빌리티": "034020.KS", "하이브": "352820.KS",
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "LS ELECTRIC": "010120.KS",
    "HD현대일렉트릭": "267260.KS", "효성중공업": "298040.KS", "LS마린솔루션": "199050.KQ",
    "LS에코에너지": "229640.KS", "SK오션플랜트": "100090.KS", "SK이터닉스": "475150.KS",
    "LG에너지솔루션": "373220.KS", "삼성SDI": "006400.KS", "율촌화학": "008730.KS",
    "서진시스템": "178320.KQ", "JYP Ent.": "035900.KQ", "에스엠": "041510.KQ",
    "와이지엔터테인먼트": "122870.KQ", "코리아써키트": "007810.KS", "현대차": "005380.KS",
    "에스엘": "005850.KS", "한국전력": "015760.KS", "한전기술": "052690.KS",
    "에코프로": "086520.KQ", "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS",
    "현대로템": "064350.KS", "HD현대중공업": "329180.KS", "한화오션": "042660.KS",
    "에이직랜드": "445090.KQ", "삼성물산": "028260.KS", "삼성생명": "032830.KS",
    "DSC인베스트먼트": "241520.KQ", "씨에스윈드": "112610.KS", "에이디테크놀로지": "200710.KQ",
    "디앤디파마텍": "347850.KQ", "키움증권": "039490.KS", "LS증권": "078020.KS", "미래에셋증권": "006800.KS"
}

DEFAULT_US_STOCKS = {
    "보잉 (BA)": "BA", "유나이티드 항공 (UAL)": "UAL", "아메리칸 항공 (AAL)": "AAL",
    "SK하이닉스 ADR (SKHY)": "SKHY", "지멘스 에너지 ADR (SMERY)": "SMERY", "무그 (MOG-A)": "MOG-A",
    "우드워드 (WWD)": "WWD", "스페이스 ETF (SPCX)": "SPCX", "인텔 (INTC)": "INTC",
    "패브리넷 (FN)": "FN", "코닝 (GLW)": "GLW", "로켓랩 (RKLB)": "RKLB",
    "팔란티어 (PLTR)": "PLTR", "센트러스 에너지 (LEU)": "LEU", "제너럴 모터스 (GM)": "GM",
    "이튼 (ETN)": "ETN", "넥스테라 에너지 (NEE)": "NEE", "콘스텔레이션 에너지 (CEG)": "CEG",
    "시에나 (CIEN)": "CIEN", "TSMC ADR (TSM)": "TSM", "오라클 (ORCL)": "ORCL",
    "버티브 홀딩스 (VRT)": "VRT", "콴타 서비스 (PWR)": "PWR", "페르미 (FRMI)": "FRMI",
    "모놀리식 파워 (MPWR)": "MPWR", "GE 버노바 (GEV)": "GEV", "마이크론 (MU)": "MU",
    "비트코인 (BTC-USD)": "BTC-USD", "테슬라 (TSLA)": "TSLA", "엔비디아 (NVDA)": "NVDA",
    "브로드컴 (AVGO)": "AVGO", "바이코 (VICR)": "VICR", "루멘텀 (LITE)": "LITE",
    "하우멧 에어로스페이스 (HWM)": "HWM", "BWX 테크놀로지스 (BWXT)": "BWXT", "블룸 에너지 (BE)": "BE",
    "뉴스케일 파워 (SMR)": "SMR", "오클로 (OKLO)": "OKLO", "제보 (GEVO)": "GEVO",
    "킨더 모건 (KMI)": "KMI", "코히런트 (COHR)": "COHR", "AMD": "AMD",
    "셈프라 에너지 (SRE)": "SRE", "아토메라 (ATOM)": "ATOM", "도어대시 (DASH)": "DASH",
    "앨버말 (ALB)": "ALB", "코인베이스 (COIN)": "COIN", "ASML": "ASML",
    "슈나이더 일렉트릭 ADR (SBGSY)": "SBGSY", "ABB ADR (ABBNY)": "ABBNY",
    "프리스미안 ADR (PRYMY)": "PRYMY", "베스타스 ADR (VWSYF)": "VWSYF", "롤스로이스 ADR (RYCEY)": "RYCEY"
}

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    initial_data = {"KR": DEFAULT_KR_STOCKS.copy(), "US": DEFAULT_US_STOCKS.copy()}
    save_watchlist(initial_data)
    return initial_data

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------------------------------------------
# 2. 매크로 6대 지표 수집 함수
# -------------------------------------------------------------
@st.cache_data(ttl=180)
def fetch_macro_indicators():
    macro_tickers = {
        "코스피": "^KS11", "코스닥": "^KQ11", "나스닥 종합": "^IXIC",
        "원/달러 환율": "KRW=X", "미 10년물 국채금리": "^TNX", "WTI 원유선물": "CL=F"
    }
    symbols = list(macro_tickers.values())
    raw = yf.download(symbols, period="5d", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
    
    results = {}
    for name, sym in macro_tickers.items():
        try:
            df = raw[sym].dropna(how="all")
            if len(df) >= 2:
                cur = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2])
                chg = cur - prev
                pct = (chg / prev) * 100
                results[name] = {"price": cur, "change": chg, "pct": pct}
            else:
                results[name] = {"price": 0.0, "change": 0.0, "pct": 0.0}
        except Exception:
            results[name] = {"price": 0.0, "change": 0.0, "pct": 0.0}
    return results

# -------------------------------------------------------------
# 3. 기술적 지표 계산 로직
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
    df['BB_PctB'] = (close - df['BB_Lower']) / ((df['BB_Upper'] - df['BB_Lower']) + 1e-9)
    
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
# 4. 종합 퀀트 스코어링 엔진 (지수 보정 포함)
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_market_data(stock_dict, is_korean=True, peak_period_days=120):
    tickers = list(stock_dict.values())
    inv_map = {v: k for k, v in stock_dict.items()}
    
    if not tickers:
        return pd.DataFrame(), {}, 0.0
        
    bench_symbol = "^KS11" if is_korean else "^GSPC"
    all_tickers = tickers + [bench_symbol]
    
    data_raw = yf.download(all_tickers, period="1y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
    
    # 벤치마크 지수 낙폭 계산
    bench_drawdown = 0.0
    try:
        b_df = data_raw[bench_symbol].dropna(how="all")
        b_cur = float(b_df['Close'].iloc[-1])
        b_peak = float(b_df['High'].tail(peak_period_days).max())
        bench_drawdown = ((b_cur - b_peak) / b_peak) * 100
    except Exception:
        bench_drawdown = 0.0

    summary_list = []
    processed_dfs = {}
    
    for ticker in tickers:
        name = inv_map[ticker]
        try:
            df = data_raw[ticker].dropna(how="all")
            if df.empty or len(df) < 25:
                continue
            
            df = calculate_indicators(df)
            processed_dfs[name] = df
            
            cur_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            pct_change = ((cur_price - prev_price) / prev_price) * 100
            diff_price = cur_price - prev_price
            
            peak_window = df.tail(peak_period_days)
            peak_price = float(peak_window['High'].max())
            drawdown = ((cur_price - peak_price) / peak_price) * 100
            
            # ★ 핵심: 지수 보정 초과 낙폭
            excess_drawdown = drawdown - bench_drawdown
            
            rsi = float(df['RSI'].iloc[-1])
            pct_b = float(df['BB_PctB'].iloc[-1])
            vol_ratio = float(df['Vol_Ratio'].iloc[-1])
            macd = float(df['MACD'].iloc[-1])
            macd_sig = float(df['MACD_Signal'].iloc[-1])
            macd_hist = float(df['MACD_Hist'].iloc[-1])
            prev_hist = float(df['MACD_Hist'].iloc[-2])
            
            # --- 퀀트 스코어 산출 로직 (-100 ~ +100점) ---
            score = 0
            
            # 1) 지수 보정 초과 낙폭 (최대 35점)
            if excess_drawdown <= -20.0: score += 35
            elif excess_drawdown <= -15.0: score += 25
            elif excess_drawdown <= -10.0: score += 18
            elif excess_drawdown <= -5.0: score += 10
            elif excess_drawdown >= 15.0: score -= 20  # 지수 대비 지나친 급등
            
            # 2) RSI 역발상 모멘텀 (최대 25점)
            if rsi <= 25: score += 25
            elif rsi <= 35: score += 18
            elif rsi <= 45: score += 8
            elif rsi >= 75: score -= 25
            elif rsi >= 65: score -= 12
            
            # 3) 볼린저밴드 %B (최대 20점)
            if pct_b <= 0.0: score += 20
            elif pct_b <= 0.15: score += 12
            elif pct_b <= 0.30: score += 5
            elif pct_b >= 1.0: score -= 20
            elif pct_b >= 0.85: score -= 10
            
            # 4) MACD 모멘텀 반전 (최대 10점)
            if macd > macd_sig and macd_hist > 0 and prev_hist <= 0:
                score += 10  # 골든크로스
                macd_desc = "골든크로스"
            elif macd_hist > prev_hist and macd_hist < 0:
                score += 6   # 하락폭 축소
                macd_desc = "하락둔화"
            elif macd < macd_sig and macd_hist < 0 and prev_hist >= 0:
                score -= 10  # 데드크로스
                macd_desc = "데드크로스"
            else:
                macd_desc = "추세유지"
                
            # 5) 거래량 실림 여부 (최대 10점)
            if vol_ratio >= 2.0 and (rsi <= 40 or pct_b <= 0.2):
                score += 10  # 과매도 구간 거래량 폭증 (손바뀜)
            elif vol_ratio >= 1.5 and (rsi <= 40 or pct_b <= 0.2):
                score += 5
            elif vol_ratio >= 2.0 and rsi >= 70:
                score -= 10  # 과열 구간 상투 거래량
                
            # 최종 액션 등급 판정
            if score >= 60:
                action = "🚨 강력 분할매수"
            elif score >= 35:
                action = "🟢 분할매수 적기"
            elif score >= 10:
                action = "🟡 매수 고려"
            elif score >= -15:
                action = "⚪ 보유 / 관망"
            elif score >= -40:
                action = "🟠 분할익절 고려"
            else:
                action = "🔴 적극 매도 / 과열"
                
            price_fmt = f"{int(cur_price):,}원" if is_korean else f"${cur_price:,.2f}"
            diff_fmt = f"{int(diff_price):+,}원" if is_korean else f"${diff_price:+,.2f}"
            peak_fmt = f"{int(peak_price):,}원" if is_korean else f"${peak_price:,.2f}"
            
            summary_list.append({
                "종목명": name,
                "티커": ticker,
                "현재가": price_fmt,
                "전일비": diff_fmt,
                "전일대비(%)": round(pct_change, 2),
                "전고점": peak_fmt,
                "명목 고점대비(%)": round(drawdown, 2),
                "지수보정 낙폭(%)": round(excess_drawdown, 2),
                "퀀트 점수": score,
                "추천 액션": action,
                "RSI": round(rsi, 1),
                "볼밴%B": round(pct_b, 2),
                "MACD": macd_desc,
                "거래량": f"{vol_ratio:.1f}x"
            })
        except Exception:
            continue
            
    df_res = pd.DataFrame(summary_list)
    if not df_res.empty:
        # 점수 높은 순(매수 1순위)으로 랭킹 정렬
        df_res = df_res.sort_values(by="퀀트 점수", ascending=False).reset_index(drop=True)
        df_res.index = df_res.index + 1
        df_res.index.name = "순위"
        
    return df_res, processed_dfs, bench_drawdown

# -------------------------------------------------------------
# 5. 차트 렌더링 함수
# -------------------------------------------------------------
def render_stock_chart(df, name, peak_days):
    plot_df = df.tail(160)
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
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA120'], line=dict(color='purple', width=1.5), name='120일선'), row=1, col=1)
    
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
# 6. 메인 UI 및 사이드바
# -------------------------------------------------------------
watchlist_data = load_watchlist()

with st.sidebar:
    st.title("AlphaPulse")
    menu = st.radio("📌 화면 네비게이션", ["🏆 퀀트 매수/매도 순위 랭킹", "📊 종합 시장 & 관심종목", "📈 개별 종목 정밀 차트"])
    
    st.markdown("---")
    st.header("⚙️ 분석 기준 설정")
    peak_days = st.slider("전고점 산정 기간 (거래일)", 30, 250, 120, 10, help="최근 120거래일(약 6개월) 최고가를 기준으로 낙폭을 계산합니다.")
    
    if st.button("🔄 실시간 시세 강제 갱신", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.header("📌 관심종목 관리 (서버 영구저장)")
    
    with st.expander("➕ 새 종목 추가", expanded=False):
        add_market = st.selectbox("추가할 시장", ["🇰🇷 국내 주식", "🇺🇸 미국 / 해외 주식"])
        add_name = st.text_input("종목명 (예: 한화시스템, 애플)")
        add_ticker = st.text_input("티커 (예: 272210.KS, AAPL)")
        if st.button("종목 등록", use_container_width=True):
            if add_name.strip() and add_ticker.strip():
                m_key = "KR" if "국내" in add_market else "US"
                clean_ticker = add_ticker.strip().upper() if not (add_ticker.endswith(".KS") or add_ticker.endswith(".KQ")) else add_ticker.strip()
                watchlist_data[m_key][add_name.strip()] = clean_ticker
                save_watchlist(watchlist_data)
                st.cache_data.clear()
                st.success(f"'{add_name}' 등록 완료!")
                st.rerun()
            else:
                st.error("종목명과 티커를 모두 입력하세요.")

    with st.expander("🗑️ 등록 종목 삭제", expanded=False):
        del_market = st.selectbox("삭제할 시장", ["🇰🇷 국내 주식", "🇺🇸 미국 / 해외 주식"], key="del_market_key")
        m_key = "KR" if "국내" in del_market else "US"
        current_names = list(watchlist_data[m_key].keys())
        if current_names:
            del_name = st.selectbox("삭제할 종목 선택", current_names)
            if st.button("선택 종목 영구 삭제", use_container_width=True):
                del watchlist_data[m_key][del_name]
                save_watchlist(watchlist_data)
                st.cache_data.clear()
                st.warning(f"'{del_name}' 삭제 완료!")
                st.rerun()
        else:
            st.info("등록된 종목이 없습니다.")

    with st.expander("⚠️ 기본 종목으로 초기화"):
        if st.button("전체 초기화 실행", type="secondary", use_container_width=True):
            watchlist_data = {"KR": DEFAULT_KR_STOCKS.copy(), "US": DEFAULT_US_STOCKS.copy()}
            save_watchlist(watchlist_data)
            st.cache_data.clear()
            st.success("초기화 완료!")
            st.rerun()

# 시장 선택 탭
market_mode = st.radio("🌍 시장 구분", ["🇰🇷 국내 주식", "🇺🇸 미국 / 해외 주식"], horizontal=True)
is_kr = (market_mode == "🇰🇷 국내 주식")
target_dict = watchlist_data["KR"] if is_kr else watchlist_data["US"]
bench_name = "KOSPI(코스피)" if is_kr else "S&P 500"

with st.spinner(f"{market_mode} 시세 및 지수 보정 퀀트 스코어링 분석 중..."):
    df_summary, dict_dfs, b_drawdown = fetch_market_data(target_dict, is_korean=is_kr, peak_period_days=peak_days)

# -------------------------------------------------------------
# PAGE 1: 🏆 퀀트 매수/매도 순위 랭킹 (메인)
# -------------------------------------------------------------
if menu == "🏆 퀀트 매수/매도 순위 랭킹":
    st.subheader(f"🏆 {market_mode} 퀀트 매수·매도 종합 랭킹")
    
    # 벤치마크 지수 현황 배너
    st.info(f"💡 **기준 벤치마크**: {bench_name} 120일 고점 대비 현재 낙폭은 **`{b_drawdown:+.2f}%`** 입니다. (종목 낙폭에서 이 수치를 차감하여 지수 보정 초과 낙폭을 산출합니다.)")
    
    col1, col2 = st.columns(2)
    with col1:
        grade_filter = st.multiselect(
            "추천 등급 필터",
            ["전체", "🚨 강력 분할매수", "🟢 분할매수 적기", "🟡 매수 고려", "⚪ 보유 / 관망", "🟠 분할익절 고려", "🔴 적극 매도 / 과열"],
            default=["전체"]
        )
    with col2:
        buy_only_mode = st.checkbox("🔥 매수 유효 종목만 정렬 (35점 이상)", value=False)
        
    display_df = df_summary.copy()
    if not display_df.empty:
        if "전체" not in grade_filter:
            display_df = display_df[display_df["추천 액션"].isin(grade_filter)]
        if buy_only_mode:
            display_df = display_df[display_df["퀀트 점수"] >= 35]
            
        st.dataframe(
            display_df,
            use_container_width=True
        )
    else:
        st.info("분석할 종목 데이터가 없습니다.")
        
    with st.expander("📖 퀀트 팩터 점수 산정 체계 (-100 ~ +100점)"):
        st.markdown("""
        - **지수 보정 초과 낙폭 (가중치 35점)**: 단순히 주가가 빠진 것이 아니라 지수 대비 초과 하락한 폭을 평가 (-20% 초과 하락 시 +35점, 반대로 지수 대비 +15% 급등 시 -20점)
        - **RSI(14) 역발상 (가중치 25점)**: 극심 과매도(≤25) 시 +25점, 과매도(25~35) 시 +18점, 과열(≥70) 시 -25점
        - **볼린저밴드 %B (가중치 20점)**: 밴드 하단 이탈(%B ≤ 0) 시 +20점, 밴드 상단 돌파(%B ≥ 1.0) 시 -20점
        - **MACD 모멘텀 (가중치 10점)**: 골든크로스 및 히스토그램 양전환 시 +10점, 데드크로스 시 -10점
        - **거래량 폭증도 (가중치 10점)**: 바닥권에서 20일 평균 거래량 1.5x~2.0x 이상 수급 폭증(투매 소화) 시 +10점
        """)

# -------------------------------------------------------------
# PAGE 2: 📊 종합 시장 & 관심종목 (시세 보드)
# -------------------------------------------------------------
elif menu == "📊 종합 시장 & 관심종목":
    st.subheader("🌐 글로벌 핵심 매크로 지표")
    macro_data = fetch_macro_indicators()
    
    m_cols = st.columns(6)
    idx = 0
    for m_name, m_info in macro_data.items():
        with m_cols[idx]:
            if "환율" in m_name: val_str = f"{m_info['price']:,.1f}원"
            elif "국채" in m_name: val_str = f"{m_info['price']:.2f}%"
            elif "WTI" in m_name: val_str = f"${m_info['price']:.2f}"
            else: val_str = f"{m_info['price']:,.2f}"
            st.metric(label=m_name, value=val_str, delta=f"{m_info['pct']:+.2f}%")
        idx += 1
        
    st.markdown("---")
    st.subheader(f"📋 {market_mode} 관심종목 실시간 시세 보드 ({len(df_summary)}개)")
    
    if not df_summary.empty:
        board_df = df_summary[["종목명", "티커", "현재가", "전일비", "전일대비(%)", "전고점", "명목 고점대비(%)", "지수보정 낙폭(%)", "거래량"]].copy()
        st.dataframe(
            board_df.sort_values(by="전일대비(%)", ascending=False),
            use_container_width=True
        )
    else:
        st.info("등록된 종목이 없습니다.")

# -------------------------------------------------------------
# PAGE 3: 📈 개별 종목 정밀 차트
# -------------------------------------------------------------
elif menu == "📈 개별 종목 정밀 차트":
    st.subheader(f"📈 {market_mode} 개별 종목 기술적 분석 정밀 차트")
    
    if len(dict_dfs) > 0:
        selected_name = st.selectbox("분석할 종목을 선택하세요", list(dict_dfs.keys()))
        if selected_name in dict_dfs:
            render_stock_chart(dict_dfs[selected_name], selected_name, peak_days)
    else:
        st.warning("표시할 수 있는 종목 데이터가 없습니다.")
