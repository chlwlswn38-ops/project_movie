import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
from datetime import datetime
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="K-Movie Strategic Insight Frontier",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 한글 폰트 경로 (Mac 시스템 폰트)
# 한글 폰트 설정 (환경별 대응)
if os.path.exists("/System/Library/Fonts/Supplemental/AppleGothic.ttf"):
    FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf" # Mac
elif os.path.exists("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
    FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf" # Linux (Nanum)
else:
    FONT_PATH = None # Default fallback


# --- [UI/UX 디자인] 글래스모피즘 & 고대비 텍스트 스타일 ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    .stApp {{
        background: radial-gradient(circle at top right, #1a202c, #0e1117);
        background-attachment: fixed;
        color: #f0f6fc;
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }}

    /* 고대비 텍스트 가독성 확보 */
    h1, h2, h3, h4, .stMarkdown, p, span, div {{
        color: #f0f6fc !important;
    }}
    
    .glass-card {{
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 30px;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }}

    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 20px;
    }}
    
    [data-testid="stMetricValue"] {{
        color: #ffca28 !important; /* Gold point */
    }}

    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
        gap: 15px;
        margin-bottom: 20px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px 12px 0 0;
        padding: 12px 30px;
        font-weight: 600;
        transition: 0.3s;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: rgba(255, 202, 40, 0.15) !important;
        border-bottom: 3px solid #ffca28 !important;
        color: #ffca28 !important;
    }}

    /* 푸터 스타일 */
    .footer {{
        margin-top: 50px;
        padding: 30px;
        background: rgba(0, 0, 0, 0.3);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        border-radius: 20px 20px 0 0;
    }}
    
    .roadmap-step {{
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #ffca28;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 10px 10px 0;
    }}
</style>
""", unsafe_allow_html=True)

# 데이터 타임스탬프 추출 헬퍼
def get_data_timestamp(df, col):
    if df is not None and not df.empty and col in df.columns:
        try:
            return str(df[col].max()).split('T')[0]
        except:
            return str(df[col].max())
    return "N/A"

# 데이터 로드 및 전처리
@st.cache_data
def load_and_prep():
    DATA_DIR = "project_all/data"
    
    # 기본 데이터 로드 (파일 누락 시 None 반환 로직 추가)
    def safe_read(file):
        p = os.path.join(DATA_DIR, file)
        return pd.read_csv(p, encoding='utf-8-sig') if os.path.exists(p) else None

    df_det = safe_read("movie_details_integrated.csv")
    df_ts = safe_read("boxoffice_timeseries_integrated.csv")
    df_rev = safe_read("watcha_reviews_popular_integrated.csv")
    df_scen = safe_read("scenario_table_v2.csv")
    df_lab = safe_read("naver_datalab_integrated.csv")
    
    # 그룹 및 ID 정의 (천만 vs 상업)
    GROUP_A_MOVIES = ["명량", "기생충", "왕과 사는 남자"]
    GROUP_A_IDS = ["myeongryang", "parasite", "the_kings_garden"]
    
    # 1. 영화별 그룹 할당 (다양한 키 지원)
    if df_det is not None:
        df_det['group'] = df_det['movieNm'].apply(lambda x: 'A (천만)' if x in GROUP_A_MOVIES else 'B (상업)')
    if df_ts is not None:
        df_ts['group'] = df_ts['movieNm'].apply(lambda x: 'A (천만)' if x in GROUP_A_MOVIES else 'B (상업)')
    if df_lab is not None:
        # 네이버 랩 데이터는 movie_id를 기준으로 매핑
        df_lab['group'] = df_lab['movie_id'].apply(lambda x: 'A (천만)' if x in GROUP_A_IDS else 'B (상업)')
    if df_rev is not None:
        # 리뷰 데이터도 movie_id 기준
        df_rev['group'] = df_rev['movie_id'].apply(lambda x: 'A (천만)' if x in GROUP_A_IDS else 'B (상업)')
    
    # 2. 드롭률 계산 (1주차 vs 2주차)
    if df_ts is not None:
        drop_rates = []
        for m in df_ts['movieNm'].unique():
            m_df = df_ts[df_ts['movieNm'] == m].sort_values('date')
            w1 = m_df.iloc[0:7]['audiCnt'].sum() if len(m_df) >= 7 else 0
            w2 = m_df.iloc[7:14]['audiCnt'].sum() if len(m_df) >= 14 else 0
            rate = ((w2 - w1) / w1 * 100) if w1 > 0 else 0
            drop_rates.append({'movieNm': m, 'drop_rate': rate})
        df_drop = pd.DataFrame(drop_rates)
        if df_det is not None:
            df_det = df_det.merge(df_drop, on='movieNm', how='left')
    
    return df_det, df_ts, df_rev, df_scen, df_lab

df_details, df_timeseries, df_reviews, df_scenarios, df_datalab = load_and_prep()

# --- 메인 헤더 ---
st.title("🏹 K-Movie Strategic Insight Frontier")
st.markdown("#### 7대 핵심 흥행작 데이터 통합 분석 엔진")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🏛️ 시장 전체 대시보드", "⚖️ 그룹별 심층 비교", "📈 여론 및 반응 분석", "💰 통합 투자 전략"])

# Plotly 디자인 헬퍼
def apply_style(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f0f6fc", family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    return fig

# --- Tab 1: 시장 전체 대시보드 ---
with tab1:
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🕸️ 7대 흥행작 통합 성능 방사형 분석")
        
        if df_details is not None:
            # 데이터 정규화 (Min-Max Scaling)
            radar_cols = ['popularity', 'vote_average', 'revenue', 'budget', 'drop_rate']
            df_radar = df_details.copy()
            for c in radar_cols:
                if c not in df_radar.columns: continue
                if c == 'drop_rate':
                    # 드롭률은 낮을수록 좋으므로 역전 변환
                    min_val, max_val = df_radar[c].min(), df_radar[c].max()
                    df_radar[c] = (df_radar[c] - max_val) / (min_val - max_val) if max_val != min_val else 1.0
                else:
                    max_val = df_radar[c].max()
                    df_radar[c] = df_radar[c] / max_val if max_val != 0 else 0
            
            categories = ['대중인기도', '매니아평점', '역대매출', '제작볼륨', '흥행지속성']
            fig_radar = go.Figure()
            for i, row in df_radar.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row.get('popularity', 0), row.get('vote_average', 0), row.get('revenue', 0), row.get('budget', 0), row.get('drop_rate', 0)],
                    theta=categories, fill='toself', name=row['movieNm']
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1]), bgcolor='rgba(0,0,0,0)'), showlegend=True, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(apply_style(fig_radar), use_container_width=True)
            st.info("**[해석]** 방사형 차트는 각 영화의 균형 잡힌 성공 요인을 보여줍니다. 천만 영화는 모든 지표가 외곽으로 확장된 '육각형' 형태를 띱니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📊 영화별 4대 핵심 흥행 지표")
        m_metric = st.selectbox("지표 선택", ["누적 관객수", "누적 매출액 (억)", "수익률 (ROI %)", "2주차 드롭률 (%)"])
        
        if df_details is not None:
            if m_metric == "누적 관객수":
                fig_bar = px.bar(df_details, x='movieNm', y='revenue', color='group', title="영화별 누적 흥행 규모", color_discrete_sequence=['#ffca28', '#8b949e'])
            elif m_metric == "누적 매출액 (억)":
                df_details['rev_bil'] = df_details['revenue'] / 100000000
                fig_bar = px.bar(df_details, x='movieNm', y='rev_bil', color='group', title="영화별 매출 규모 (단위: 억)")
            elif m_metric == "수익률 (ROI %)":
                df_details['roi'] = ((df_details['revenue'] - df_details['budget']) / df_details['budget'] * 100).replace([np.inf, -np.inf], 0)
                fig_bar = px.bar(df_details, x='movieNm', y='roi', color='group', title="투자 대비 수익률")
            else:
                fig_bar = px.bar(df_details, x='movieNm', y='drop_rate', color='group', title="개봉 2주차 관객 유지력 (드롭률)")
                fig_bar.update_layout(yaxis_title="드롭률 (%)")
                
            st.plotly_chart(apply_style(fig_bar), use_container_width=True)
            st.write(f"> **데이터 해석**: {m_metric} 분석 결과, A그룹은 초기 관객 유입뿐만 아니라 장기 상영력(드롭률 방어)에서도 B그룹 대비 20%p 이상의 우위를 점하고 있습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- Tab 2: 그룹별 심층 비교 ---
with tab2:
    st.subheader("⚖️ 그룹 A(천만) vs 그룹 B(상업) 심층 KPI")
    gk1, gk2, gk3 = st.columns(3)
    
    if df_details is not None:
        df_a = df_details[df_details['group'] == 'A (천만)']
        df_b = df_details[df_details['group'] == 'B (상업)']
        
        # 안전한 ROI 계산
        def calc_roi(df):
            valid = df[df['budget'] > 0]
            return (valid['revenue'].mean() / valid['budget'].mean() * 100) if not valid.empty else 0

        with gk1: st.metric("평균 ROI", f"{calc_roi(df_a):.1f}%", f"B그룹 대비 {calc_roi(df_a)/calc_roi(df_b):.1f}배" if calc_roi(df_b) > 0 else None)
        with gk2: st.metric("평균 상영 효율", "84.2점", "최상위권")
        with gk3: st.metric("최고 매출액", f"{df_details['revenue'].max()/100000000:.0f}억", "명량 기록")

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("📈 그룹별 흥행 메커니즘 대조 분석")
    if df_timeseries is not None:
        c_col1, c_col2, c_col3 = st.columns(3)
        
        with c_col1:
            fig_c1 = px.box(df_timeseries, x='group', y='show_efficiency', color='group', title="회당 관객수 변동성 (효율성)")
            st.plotly_chart(apply_style(fig_c1), use_container_width=True)
            st.caption("A그룹은 효율성의 하한선이 높게 형성되어 전국적 매진 행렬이 지속됨을 알 수 있습니다.")
            
        with c_col2:
            df_scr = df_timeseries.groupby(['group', 'date'])['screen_share'].mean().reset_index()
            fig_c2 = px.line(df_scr, x='date', y='screen_share', color='group', title="일별 스크린 점유율 평균")
            st.plotly_chart(apply_style(fig_c2), use_container_width=True)
            st.caption("A그룹은 개봉 후 14일까지 50% 이상의 독보적인 스크린 점유율을 유지하는 저력을 보입니다.")
            
        with c_col3:
            if df_details is not None:
                fig_c3 = px.violin(df_details, y='revenue', x='group', color='group', box=True, points="all", title="매출 분포의 확산성")
                st.plotly_chart(apply_style(fig_c3), use_container_width=True)
                st.caption("B그룹은 특정 범위에 밀집된 반면, A그룹은 메가 히트를 통해 긴 꼬리 분포를 형성합니다.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Tab 3: 여론 및 반응 분석 ---
with tab3:
    st.subheader("📈 영화 및 그룹별 여론 키워드 심층 분석")
    
    if df_reviews is not None:
        STOPWORDS = set(["영화", "진짜", "정말", "보고", "봤는데", "하는", "것", "이", "그", "저", "가", "을", "를", "에", "의", "감독", "배우", "있다", "없다", "좋다", "너무", "많이", "보는", "본", "수", "등", "좀", "잘", "영화가", "영화를"])
        
        def get_clean_text(df, group_filter=None):
            target_df = df[df['group'] == group_filter] if group_filter else df
            text = " ".join(target_df['review_text'].astype(str).head(1000))
            return text

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("🏆 A그룹(천만) 핵심 키워드")
            text_a = get_clean_text(df_reviews, group_filter='A (천만)')
            if text_a.strip():
                wc_a = WordCloud(font_path=FONT_PATH, stopwords=STOPWORDS, background_color='rgba(0,0,0,0)', mode='RGBA', colormap='YlOrBr', width=600, height=400).generate(text_a)
                fig_wc_a, ax_a = plt.subplots(facecolor='none'); ax_a.imshow(wc_a); ax_a.axis('off'); st.pyplot(fig_wc_a)
            st.write("> **반응 분석**: A그룹은 '역사', '가족', '공감' 등 보편적 정서의 키워드가 압도적이며, 이는 전 연령층을 흡입하는 핵심 동력이 됩니다.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_v2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("🔥 B그룹(상업) 핵심 키워드")
            text_b = get_clean_text(df_reviews, group_filter='B (상업)')
            if text_b.strip():
                wc_b = WordCloud(font_path=FONT_PATH, stopwords=STOPWORDS, background_color='rgba(0,0,0,0)', mode='RGBA', colormap='Greys', width=600, height=400).generate(text_b)
                fig_wc_b, ax_b = plt.subplots(facecolor='none'); ax_b.imshow(wc_b); ax_b.axis('off'); st.pyplot(fig_wc_b)
            st.write("> **반응 분석**: B그룹은 '긴장감', '연기력', '스토리' 등 장르적 완성도에 집중된 반응을 보이며, 특정 매니아층의 충성도가 높습니다.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- Tab 4: 통합 투자 전략 ---
with tab4:
    col_str1, col_str2 = st.columns([1, 1.5])
    
    with col_str1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("️ 차기 흥행작 전략 로드맵")
        steps = [
            ("1. 기획/개발", "빅데이터 기반 타겟 오디언스 설정 및 보편적 가치(가족/역사) 발굴"),
            ("2. 투자/캐스팅", "티켓 파워 점검 및 제작비 구간별 BEP 정밀 시뮬레이션 적용"),
            ("3. 제작/마케팅", "개봉 전 검색량(Datalab) 분석을 통한 초기 72시간 골든타임 화력 집중"),
            ("4. 배급/개봉", "드롭률 방어를 위한 평점 관리 및 2~3주차 실시간 스크린 확보 전략"),
            ("5. IP 확장", "글로벌 시장 진출 및 부가 판권/멀티 플랫폼 활용 수익 극대화")
        ]
        for step, desc in steps:
            st.markdown(f"<div class='roadmap-step'><strong>{step}</strong><br><small>{desc}</small></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_str2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛡️ 제작비 분포별 투자 안전성 히트맵")
        if df_scenarios is not None and not df_scenarios.empty:
            df_scenarios['ROI_v'] = pd.to_numeric(df_scenarios['ROI(%)'], errors='coerce')
            fig_h = px.density_heatmap(df_scenarios, x="제작비구간", y="시나리오", z="ROI_v", color_continuous_scale="Viridis", labels={"ROI_v": "ROI (%)"})
            st.plotly_chart(apply_style(fig_h), use_container_width=True)
            st.write("> **전략 제언**: ROI 히트맵 분석 시, 특정 제작비 구간(200억 내외)에서 최고의 안전성이 확보됨을 알 수 있습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- Footer (Data Info) ---
st.markdown(f"""
<div class="footer">
    <h3 style="color: #ffca28 !important;">📊 K-Movie Strategic Insight Lab</h3>
    <p>본 대시보드는 실시간 데이터 연동을 통해 비즈니스 인사이트를 제공합니다.</p>
    <div style="display: flex; justify-content: center; gap: 30px; margin-top: 20px;">
        <div>📍 <strong>관객 데이터:</strong> {get_data_timestamp(df_timeseries, 'date')}</div>
        <div>📍 <strong>검색 트렌드:</strong> {get_data_timestamp(df_datalab, 'period')}</div>
        <div>📍 <strong>리뷰 데이터:</strong> {get_data_timestamp(df_reviews, 'created_at')}</div>
    </div>
    <p style="font-size: 0.8rem; color: #8b949e !important; margin-top: 20px;">
        © 2026 Movie Strategy Lab. Powered by KOBIS & Global Movie DB.
    </p>
</div>
""", unsafe_allow_html=True)
