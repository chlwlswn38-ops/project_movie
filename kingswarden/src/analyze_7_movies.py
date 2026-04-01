import pandas as pd
import numpy as np
import os
import re
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import seaborn as sns

# ==========================================
# 0. 설정 환경 변수 (Settings)
# ==========================================
USE_MORPH = True
MORPH_ANALYZER = "pecab"
RANDOM_STATE = 42

BASE_DIR = '/Users/me/icb6/antigravity_project/project_s_movie/kingswarden'
# 데이터는 상위 data/processed에서 가져옵니다 (기존 통합 데이터 활용)
UNIFIED_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'unified_text_data.csv')
IMG_DIR = os.path.join(BASE_DIR, 'images', 'advanced_eda')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SUMMARY_TXT = os.path.join(DOCS_DIR, 'text_analysis_summary_7_movies.txt')
OUTPUT_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'unified_7_movies_data.csv')

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# 7개 필터링 대상 영화
target_movies_map = {
    'myeongryang': '명량',
    'parasite': '기생충',
    'sado': '사도',
    'the_kings_garden': '왕과 사는 남자',
    'decision_to_leave': '헤어질 결심',
    'the_night_owl': '올빼미',
    'the_man_standing_next': '남산의 부장들'
}

summary_log = []
def log_summary(section, content):
    summary_log.append(f"\n[{section}]")
    summary_log.append(content)

# 손익분기점 및 개봉 정보 (시뮬레이션 데이터 포함)
movies_financials = {
    '명량': {'bep': 600, 'actual': 1761, 'budget': 190, 'weeks': [600, 1100, 1400, 1600, 1700, 1750, 1761]},
    '기생충': {'bep': 370, 'actual': 1031, 'budget': 135, 'weeks': [330, 700, 850, 950, 1000, 1020, 1031]},
    '사도': {'bep': 300, 'actual': 624, 'budget': 95, 'weeks': [180, 480, 560, 600, 615, 620, 624]},
    '왕과 사는 남자': {'bep': 500, 'actual': 1050, 'budget': 150, 'weeks': [250, 650, 850, 970, 1020, 1040, 1050]}, # 최근/진행 추세 역산
    '헤어질 결심': {'bep': 120, 'actual': 189, 'budget': 113, 'weeks': [50, 100, 140, 170, 180, 185, 189]}, # 칸/판권수익으로 인한 BEP 120만 반영
    '올빼미': {'bep': 210, 'actual': 332, 'budget': 90, 'weeks': [80, 170, 250, 300, 320, 328, 332]},
    '남산의 부장들': {'bep': 500, 'actual': 475, 'budget': 150, 'weeks': [200, 400, 450, 465, 470, 473, 475]}
}

# ==========================================
# 1. 시각화 1: 손익 달성률 시나리오
# ==========================================
def plot_financial_scenarios():
    print("손익분기점 및 관객 분석 시각화 중...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    
    names = list(movies_financials.keys())
    beps = [movies_financials[n]['bep'] for n in names]
    actuals = [movies_financials[n]['actual'] for n in names]
    
    # 왕과 사는 남자 강조 컬러
    colors = ['crimson' if n == '왕과 사는 남자' else 'steelblue' for n in names]
    
    # 1. BEP 달성률 (초과 관객)
    x = np.arange(len(names))
    width = 0.35
    ax1.bar(x - width/2, beps, width, label='BEP (손익분기점)', color='lightgray', edgecolor='black')
    ax1.bar(x + width/2, actuals, width, label='최종 누적관객수', color=colors)
    
    # 왕사남 텍스트
    for i, name in enumerate(names):
        if name == '왕과 사는 남자':
            ax1.text(x[i] + width/2, actuals[i] + 50, f"{actuals[i]}만(추정)", ha='center', color='crimson', fontweight='bold')
    
    ax1.axhline(y=1000, color='red', linestyle='--', alpha=0.5, label='천만 관객선')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=45, ha='right')
    ax1.set_title('7대 주요영화 BEP vs 최종 누적관객수 (단위: 만 명)', fontsize=15)
    ax1.legend()

    # 2. 주차별 관객 동원 (추이 변화)
    weeks = [1, 2, 3, 4, 5, 6, 7]
    for n in names:
        trend = movies_financials[n]['weeks']
        if n == '왕과 사는 남자':
            ax2.plot(weeks, trend, marker='o', linewidth=3, color='crimson', label=n)
        elif n in ['명량', '기생충']:
            ax2.plot(weeks, trend, marker='s', linewidth=2, color='orange', alpha=0.8, label=n)
        else:
            ax2.plot(weeks, trend, marker='.', linewidth=1.5, color='gray', alpha=0.5, label=n)
    
    ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.5)
    ax2.set_title('주차별 관객수 누적 추이 가상 시나리오', fontsize=15)
    ax2.set_xlabel('개봉 후 주차')
    ax2.set_ylabel('누적 관객수 (만 명)')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, 'financial_scenarios.png'), dpi=300)
    plt.close()

plot_financial_scenarios()

# ==========================================
# 2. NLP 분석 (7개 영화 전용)
# ==========================================
print("텍스트 데이터 필터링 중...")
try:
    df_all = pd.read_csv(UNIFIED_CSV)
except FileNotFoundError:
    print(f"Error: {UNIFIED_CSV} not found. Please ensure the parent data pipeline has been run.")
    exit(1)

# 'product'가 영문이면 한글로 매핑 (혹은 그 반대 가능성을 모두 커버)
df_all['movie_kor'] = df_all['product'].map(target_movies_map).fillna(df_all['product'])
target_kors = list(target_movies_map.values())

df = df_all[df_all['movie_kor'].isin(target_kors)].copy()
print(f"7개 영화 필터링 결과: 총 {len(df)}건 문서 추출")

from tqdm import tqdm
try:
    from pecab import PeCab
    pecab = PeCab()
except ImportError:
    pecab = None

STOPWORDS = set([
    '영화', '진짜', '너무', '정말', '그냥', '최고', '이거', '많이', '조금', '이런', '저런',
    '것이다', '있는', '없는', '같은', '그리고', '하지만', '그런데', '그래서', '입니다', '있다',
    '없다', '한다', '하는', '위해', '대한', '통해', '어떻게', '이렇게', '그렇게', '때문에', 
    '아니다', '좋은', '많은', '모든', '아닌', '같다', '생각', '사람', '정말', '보면', '완전', '가장',
    '부터', '까지', '결국'
])

def preprocess_text(text):
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', str(text))
    text = text[:1000]
    if pecab:
        tokens = pecab.nouns(text)
        tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS]
        return ' '.join(tokens)
    else:
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = [t for t in text.split() if len(t) > 1 and t not in STOPWORDS]
        return ' '.join(tokens)

print("Pecab 형태소 분석 중...")
tqdm.pandas()
df['cleaned'] = df['document'].progress_apply(preprocess_text)
df = df[df['cleaned'].str.strip() != ''].reset_index(drop=True)

# 최적 TF-IDF & 군집 진행
print("TF-IDF 벡터화 진행...")
vectorizer = TfidfVectorizer(max_features=1000, min_df=3, max_df=0.9)
X_tfidf = vectorizer.fit_transform(df['cleaned'])
feature_names = np.array(vectorizer.get_feature_names_out())

print("SVD 2차원 축소 및 왕과사는남자 하이라이트 진행...")
svd = TruncatedSVD(n_components=2, random_state=RANDOM_STATE)
X_svd = svd.fit_transform(X_tfidf)

# 왕과 사는 남자 SVD 플롯
is_wang_sa = (df['movie_kor'] == '왕과 사는 남자').values
plt.figure(figsize=(10, 8))
plt.scatter(X_svd[~is_wang_sa, 0], X_svd[~is_wang_sa, 1], alpha=0.3, s=15, c='lightgray', label='기타 6개 영화')
plt.scatter(X_svd[is_wang_sa, 0], X_svd[is_wang_sa, 1], alpha=0.8, s=35, c='crimson', label='왕과 사는 남자')
plt.title('TF-IDF SVD 공간에서의 《왕과 사는 남자》 텍스트 군집/분포', fontsize=15)
plt.legend()
plt.savefig(os.path.join(IMG_DIR, 'wang_sa_svd_highlight.png'), dpi=300)
plt.close()

# K-Means 
print("K-Means 군집화 진행...")
kmeans = KMeans(n_clusters=4, random_state=RANDOM_STATE, n_init='auto')
df['cluster'] = kmeans.fit_predict(X_tfidf)

cluster_keywords = []
for cluster_idx, center in enumerate(kmeans.cluster_centers_):
    top_features_ind = center.argsort()[: -15 - 1 : -1]
    top_features = feature_names[top_features_ind]
    cluster_keywords.append(f"C{cluster_idx}: " + ", ".join(top_features))

cross_tab = pd.crosstab(df['movie_kor'], df['cluster'])
log_summary("7개 영화 K-Means 핵심 클러스터 및 키워드", "\n".join(cluster_keywords))
log_summary("영화별 군집 교차표", cross_tab.to_string())

with open(SUMMARY_TXT, 'w', encoding='utf-8') as f:
    f.writelines("\n".join(summary_log))
    
df.to_csv(OUTPUT_CSV, index=False)
print("성공적으로 모든 생성 및 분석이 종료되었습니다.")
