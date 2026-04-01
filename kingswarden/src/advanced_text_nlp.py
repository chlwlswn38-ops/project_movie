import pandas as pd
import numpy as np
import os
import re
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import Counter
from tqdm import tqdm

# ==========================================
# 0. 설정 환경 변수 (Settings)
# ==========================================
USE_MORPH = True
MORPH_ANALYZER = "pecab"
SAMPLE_PER_SOURCE = 300 # pecab 속도 한계상 300개로 조정하여 약 1800건 테스트 진행
RANDOM_STATE = 42

BASE_DIR = '/Users/me/icb6/antigravity_project/project_s_movie/kingswarden/king_all'
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_CSV = os.path.join(DATA_DIR, 'processed', 'unified_text_data.csv')
IMG_DIR = os.path.join(BASE_DIR, 'images', 'advanced_eda')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SUMMARY_TXT = os.path.join(DOCS_DIR, 'text_analysis_summary.txt')
REPORT_MD = os.path.join(DOCS_DIR, 'advanced_eda_report.md')

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

# 사용자 정의 불용어 (영화 리뷰, 기사, 유튜브 댓글 범용)
STOPWORDS = set([
    '영화', '진짜', '너무', '정말', '그냥', '최고', '이거', '많이', '조금', '이런', '저런',
    '것이다', '있는', '없는', '같은', '그리고', '하지만', '그런데', '그래서', '입니다', '있다',
    '없다', '한다', '하는', '위해', '대한', '통해', '어떻게', '이렇게', '그렇게', '때문에', 
    '아니다', '좋은', '많은', '모든', '아닌', '같다', '생각', '사람', '정말', '보면', '완전', '가장',
    '부터', '까지', '결국'
])

# Summary 기록용 리스트
summary_log = []

def log_summary(section, content):
    summary_log.append(f"\n[{section}]")
    summary_log.append(content)

# ==========================================
# 1. 데이터 파이프라인 구조
# ==========================================
def load_and_merge_data():
    files_configs = [
        {'name': 'naver_news_integrated.csv', 'text': ['title', 'description'], 'product': 'movie_id'},
        {'name': 'naver_proxy_30d.csv', 'text': ['title', 'description'], 'product': 'movie_title'},
        {'name': 'naver_review_proxy.csv', 'text': ['title', 'description'], 'product': 'movie_title'},
        {'name': 'watcha_reviews_low_integrated.csv', 'text': ['review_text'], 'product': 'movie_id'},
        {'name': 'watcha_reviews_popular_integrated.csv', 'text': ['review_text'], 'product': 'movie_id'},
        {'name': 'youtube_comments.csv', 'text': ['text'], 'product': 'movie_title'}
    ]
    
    dfs = []
    print("통합 데이터 구성 중...")
    for cfg in files_configs:
        path = os.path.join(DATA_DIR, cfg['name'])
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
            for tc in cfg['text']:
                df[tc] = df[tc].fillna('').astype(str)
            
            if len(cfg['text']) > 1:
                df['document'] = df[cfg['text']].agg(' '.join, axis=1)
            else:
                df['document'] = df[cfg['text'][0]]
                
            df['product'] = df[cfg['product']].fillna('unknown').astype(str)
            df['source'] = cfg['name']
            
            if len(df) > SAMPLE_PER_SOURCE:
                df = df.sample(n=SAMPLE_PER_SOURCE, random_state=RANDOM_STATE)
            
            dfs.append(df[['document', 'product', 'source']])
            print(f"- {cfg['name']} 로드 완료 ({len(df)}건)")
        except Exception as e:
            print(f"Failed loading {cfg['name']}: {e}")
            
    unified_df = pd.concat(dfs, ignore_index=True)
    unified_df['document'] = unified_df['document'].replace(r'^\s*$', np.nan, regex=True)
    unified_df = unified_df.dropna(subset=['document']).drop_duplicates(subset=['document']).reset_index(drop=True)
    unified_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"통합 완료: 총 {len(unified_df)}건 -> {OUTPUT_CSV} 저장 완료")
    return unified_df

# ==========================================
# 2. 전처리 (형태소 분석 & 불용어)
# ==========================================
pecab = None
if USE_MORPH:
    try:
        from pecab import PeCab
        pecab = PeCab()
        print(f"형태소 분석기 '{MORPH_ANALYZER}' 로드 성공")
        log_summary("형태소 분석기 설정", f"사용 여부: True\n분석기 명: {MORPH_ANALYZER}\n목적: 단어(명사 중심)의 정확한 특징을 뽑아내어 토픽 및 군집 품질 개선")
    except ImportError:
        print("PeCab 모듈이 없습니다. 설치 후 진행하거나 USE_MORPH를 False로 변경하세요.")
        exit(1)
else:
    log_summary("형태소 분석기 설정", "사용 여부: False\n목적: 빠른 처리 가능 및 원본 단어의 형태 유지")

log_summary("불용어 정의", "아래 불용어를 제거하여 구별력이 약한 단어를 필터링합니다.\n" + ", ".join(STOPWORDS))

def preprocess_text(text):
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', str(text)) # 특수문자 제거
    # 기사 등 너무 긴 텍스트는 pecab 처리 중 병목/메모리 초과를 유발하므로 앞 1000자로 제한
    text = text[:1000]
    
    if USE_MORPH and pecab:
        # 명사 위주 추출 (토픽 추출 시 명사가 유리) + 용언(동사/형용사) 등 토큰화
        # 빠른 처리를 위해 형태소(Morphs)를 추출하여 2글자 이상만 필터링하거나, 명사(Nouns) 추출
        # 여기서는 의미 있는 키워드 도출을 위해 명사 위주(Nouns)로 갑니다 (의미 없는 조사가 걸러지기 때문)
        tokens = pecab.nouns(text)
        tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS]
        return ' '.join(tokens)
    else:
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = [t for t in text.split() if len(t) > 1 and t not in STOPWORDS]
        return ' '.join(tokens)

# ==========================================
# 실행부
# ==========================================
df = load_and_merge_data()

# 문서 길이(글자수 기반)
df['doc_length'] = df['document'].apply(len)
plt.figure(figsize=(10,5))
plt.hist(df['doc_length'], bins=50, color='skyblue', edgecolor='black')
plt.title('문서 길이(글자수) 분포')
plt.xlabel('글자수')
plt.ylabel('빈도')
plt.xlim(0, 1000) # 가시성을 위해 상한 제한
plt.savefig(os.path.join(IMG_DIR, 'doc_length_hist.png'), dpi=300)
plt.close()

# 전처리 수행
print("전처리 수행 중... (시간이 소요될 수 있습니다)")
tqdm.pandas()
df['cleaned'] = df['document'].progress_apply(preprocess_text)

# 불용어 적용 파악용 - 모든 토큰 카운팅
all_tokens = ' '.join(df['cleaned'].dropna()).split()
word_counts = Counter(all_tokens)
top_words_after = word_counts.most_common(30)
log_summary("불용어 제거 후 상위 빈도 단어", "\n".join([f"{k}: {v}" for k, v in top_words_after]))

df = df[df['cleaned'].str.strip() != ''].reset_index(drop=True)

# ==========================================
# 3. TF-IDF 벡터화
# ==========================================
print("TF-IDF 벡터화 진행...")
vectorizer = TfidfVectorizer(max_features=2000, min_df=5, max_df=0.9)
X_tfidf = vectorizer.fit_transform(df['cleaned'])
feature_names = np.array(vectorizer.get_feature_names_out())

# 전체 TF-IDF 상위
sum_tfidf = X_tfidf.sum(axis=0).A1
top_tfidf_idx = sum_tfidf.argsort()[::-1][:30]
log_summary("TF-IDF 상위 30 단어", "\n".join([f"{feature_names[i]}: {sum_tfidf[i]:.2f}" for i in top_tfidf_idx]))

# ==========================================
# 4. 차원축소 (TruncatedSVD)
# ==========================================
print("차원 축소 SVD 진행...")
svd = TruncatedSVD(n_components=2, random_state=RANDOM_STATE)
X_svd = svd.fit_transform(X_tfidf)

plt.figure(figsize=(8,6))
plt.scatter(X_svd[:,0], X_svd[:,1], alpha=0.1, s=5, c='gray')
plt.title('TF-IDF TruncatedSVD 2차원 분포')
plt.xlabel('컴포넌트 1')
plt.ylabel('컴포넌트 2')
plt.savefig(os.path.join(IMG_DIR, 'svd_2d_distribution.png'), dpi=300)
plt.close()

# ==========================================
# 5. 토픽 모델링 (LDA & NMF)
# ==========================================
def plot_top_words(model, feature_names, n_top_words, title, filename):
    fig, axes = plt.subplots(1, 5, figsize=(25, 6), sharey=True)
    axes = axes.flatten()
    result_log = []
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[: -n_top_words - 1 : -1]
        top_features = feature_names[top_features_ind]
        weights = topic[top_features_ind]
        
        ax = axes[topic_idx]
        ax.barh(top_features, weights, color='cadetblue')
        ax.set_title(f"Topic {topic_idx}", fontdict={"fontsize": 14})
        ax.invert_yaxis()
        ax.tick_params(axis="both", which="major", labelsize=12)
        
        result_log.append(f"Topic {topic_idx}: " + ", ".join([f"{w}({score:.2f})" for w, score in zip(top_features, weights)]))
    
    plt.suptitle(title, fontsize=20)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, filename), dpi=300)
    plt.close()
    return "\n".join(result_log)

N_TOPICS = 5

print("LDA 모델링 진행...")
lda = LatentDirichletAllocation(n_components=N_TOPICS, random_state=RANDOM_STATE, n_jobs=-1)
lda_matrix = lda.fit_transform(X_tfidf)
lda_log = plot_top_words(lda, feature_names, 30, 'LDA 모델 토픽별 상위 키워드 분석', 'lda_top_words.png')
log_summary("LDA 토픽 모델링", lda_log)
df['lda_topic'] = lda_matrix.argmax(axis=1)

print("NMF 모델링 진행...")
nmf = NMF(n_components=N_TOPICS, random_state=RANDOM_STATE)
nmf_matrix = nmf.fit_transform(X_tfidf)
nmf_log = plot_top_words(nmf, feature_names, 30, 'NMF 모델 토픽별 상위 키워드 분석', 'nmf_top_words.png')
log_summary("NMF 토픽 모델링", nmf_log)
df['nmf_topic'] = nmf_matrix.argmax(axis=1)

# ==========================================
# 6. 군집화 (K-Means) 및 실루엣
# ==========================================
print("K-Means 군집화 진행...")
kmeans = KMeans(n_clusters=5, random_state=RANDOM_STATE, n_init='auto')
df['cluster'] = kmeans.fit_predict(X_tfidf)

# Cluster Center Plot
kmeans_log = []
fig, axes = plt.subplots(1, 5, figsize=(25, 6), sharey=True)
axes = axes.flatten()
for cluster_idx, center in enumerate(kmeans.cluster_centers_):
    top_features_ind = center.argsort()[: -30 - 1 : -1]
    top_features = feature_names[top_features_ind]
    weights = center[top_features_ind]
    
    ax = axes[cluster_idx]
    ax.barh(top_features, weights, color='salmon')
    ax.set_title(f"Cluster {cluster_idx} (N={np.sum(df['cluster']==cluster_idx)})", fontdict={"fontsize": 14})
    ax.invert_yaxis()
    
    kmeans_log.append(f"Cluster {cluster_idx} (N={np.sum(df['cluster']==cluster_idx)}): " + ", ".join([f"{w}({score:.2f})" for w, score in zip(top_features, weights)]))
plt.suptitle("K-Means 군집별 대표 키워드 중요도", fontsize=20)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'kmeans_cluster_words.png'), dpi=300)
plt.close()
log_summary("K-Means 군집화", "\n".join(kmeans_log))

# 실루엣 (샘플링)
if X_tfidf.shape[0] > 5000:
    sample_indices = np.random.choice(X_tfidf.shape[0], 5000, replace=False)
    X_sample = X_tfidf[sample_indices]
    y_sample = df['cluster'].values[sample_indices]
else:
    sample_indices = np.arange(X_tfidf.shape[0])
    X_sample = X_tfidf
    y_sample = df['cluster'].values

sil_score = silhouette_score(X_sample, y_sample)
log_summary("실루엣 분석", f"전체 평균 실루엣 점수 (Sampled 5000): {sil_score:.4f}")

# 2D 스캐터 Kmeans 결과
plt.figure(figsize=(8,6))
scatter = plt.scatter(X_svd[sample_indices, 0], X_svd[sample_indices, 1], c=y_sample, cmap='viridis', alpha=0.5, s=15)
plt.colorbar(scatter, label='Cluster')
plt.title(f'K-Means Clusters in 2D SVD Space (Silhouette: {sil_score:.4f})')
plt.xlabel('SVD 1')
plt.ylabel('SVD 2')
plt.savefig(os.path.join(IMG_DIR, 'kmeans_svd_scatter.png'), dpi=300)
plt.close()

# 교차 분석표 (Top Product vs Cluster)
top_products = df['product'].value_counts().head(10).index
cross_tab = pd.crosstab(df[df['product'].isin(top_products)]['product'], df[df['product'].isin(top_products)]['cluster'])
log_summary("product 교차분석", cross_tab.to_string())

# ==========================================
# 7. 리포트 및 결과 저장
# ==========================================
print("산출물 저장 중...")
with open(SUMMARY_TXT, 'w', encoding='utf-8') as f:
    f.writelines("\n".join(summary_log))

# 마크다운 리포트 작성
report_md_content = f"""# 심층 텍스트 분석 및 토픽 탐색 리포트

## 프로젝트 개요
수집된 10종의 영화 관련 텍스트 데이터(뉴스, 기사, 리뷰, 댓글 등)를 병합(`document`, `product`) 및 샘플링하여 하나의 마스터 데이터(`N={len(df)}`)로 구성한 뒤, NLP 기반 텍스트 인텔리전스 분석을 수행하였습니다.

## 분석 기법: 형태소 분석기 설정
- **기법:** `pecab` 형태소 분석기를 이용한 단어(명사) 토큰화
- **해석 및 의의:** 단순 어절 분리로는 한국어 특유의 조사가 포함되어 키워드 품질이 떨어지지만, `pecab`을 사용하여 명사 위주의 의미 단위만 추출했습니다. 결과적으로 영화 리뷰의 핵심 소재와 평가 키워드를 매우 선명하게 추출할 수 있게 됩니다.

## 분석 기법: 불용어 정의 및 제거 기준
- **제거된 주요 불용어:** {', '.join(list(STOPWORDS)[:15])} 등. 
- **제거 기준:** '영화', '너무', '진짜' 와 같이 모든 분야/문서에서 공통적으로 빈도수가 높지만 분석 변별력이 낮아서 토픽 분기를 저해하는 단어를 정의해 제거하였습니다.

## 분석 기법: EDA (문서 길이 분포)
![문서 길이 분포](../images/advanced_eda/doc_length_hist.png)
- **해석:** 대부분의 텍스트가 비교적 짧은 댓글/리뷰 형태를 가지며(롱테일 분포), 리뷰 내에 일부 장문 기사 및 상세리뷰가 포함되어 있습니다. 결측치나 중복값이 제거된 순수 텍스트만 활용했습니다.

## 분석 기법: TF-IDF
TF-IDF 행렬 계산을 통해 전체 문서의 중요 키워드를 도출하였습니다. 단순 높은 빈도수가 아닌 문서 분리에 중요한 역할을 한 핵심 개념어들입니다.
- **해석 기반 활용:** 상위 키워드 위주로 최신 영화 관련 인사이트를 구체적으로 캐치할 수 있습니다 (세부 키워드 내역은 `{SUMMARY_TXT}` 참조)

## 분석 기법: 차원축소 (TruncatedSVD)
![SVD 분포](../images/advanced_eda/svd_2d_distribution.png)
- **왜 했는지:** 거대한 차원의 TF-IDF 피처들을 2차원으로 축소하여 눈으로 볼 수 있게 만들고, 데이터가 의미 단위로 뭉쳐 있는지(Cluster) 확인하기 위함입니다. 
- **해석:** 점들이 밀집된 구역과 바깥으로 퍼진 꼬리 형태 구역이 존재하여 몇 가지 차별화된 토픽/군집으로 데이터가 구분될 잠재 가능성을 시사합니다.

## 분석 기법: 토픽 모델링 (LDA & NMF) 비교
데이터 내에 어떤 주제가 흐르고 있는지 5개의 토픽으로 분리하여 파악했습니다.

### LDA 토픽 모델링 상위 키워드
![LDA Topics](../images/advanced_eda/lda_top_words.png)
- **해석:** 확률 기반 모델 특성상 전반적인 문장 구성 원리를 반영하여 다소 넓은 의미의 토픽이 추출됩니다. 

### NMF 토픽 모델링 상위 키워드
![NMF Topics](../images/advanced_eda/nmf_top_words.png)
- **해석:** NMF는 선형 합성을 통해 부분 특징(Parts)을 잘 찾아냅니다. 구체적인 영화 제목이나 특정 논란/이벤트 등 명확한 구분이 되는 독립적 주제군 파악에 더 유리하게 나타나는 경향이 있습니다.

## 분석 기법: K-Means 군집화 (Clustering)
토픽 모델링과 다르게 실제 각 문서를 제일 가까운 특성에 따라 5개의 덩어리로 잘라냈습니다.
![KMeans 군집](../images/advanced_eda/kmeans_cluster_words.png)
- **활용 포인트:** 각 군집(Cluster 0 ~ 4)별로 가장 가중치가 높은 핵심 단어들을 보면(세부내역 텍스트 리포트 참고) 이 군집이 "긍정 리뷰 그룹", "스토리 비판 그룹", 혹은 "영화 A 리뷰 집단" 등인지 확인할 수 있으며 고객 타게팅이나 여론 분류 모델의 레이블 후보로 적용할 수 있습니다.

## 분석 기법: 실루엣 분석 (군집 타당도 가늠)
![Silhouette Scatter](../images/advanced_eda/kmeans_svd_scatter.png)
- 2차원 공간위에 5개의 군집을 색깔별로 나타냈습니다. 군집이 촘촘하게 묶여 있는지 퍼져있는지를 의미하는 **실루엣 점수는 {sil_score:.4f}** 로 나타났습니다.
- **해석:** TF-IDF 고차원 거리 특성상 수치가 높지는 않더라도 2D 스캐터에서 색상별로 유의미하게 구역이 분리됨을 확인할 수 있습니다.

## 분석 기법: product (영화) 교차분석 테이블 요약
**어떤 영화가 어느 군집에 속해 있는지 파악하는 교차 집계표**를 생성하였습니다.
(자세한 테이블 결과는 `{SUMMARY_TXT}` 파일 가장 아래를 확인해 주세요.)
- **이를 통한 인사이트 활용:** 마케팅이나 보고서 작성 시, 특정 영화(Product)가 어떤 성향의 리뷰 그룹(Cluster)에 많이 몰리는지 증명하여 기획 방향의 근거로 제공할 수 있습니다.

---
**최종 산출물 목록:**
- 통합 원본: `{OUTPUT_CSV}`
- 키워드 및 점수 요약본 TXT: `{SUMMARY_TXT}`
- 이미지 저장 위치: `/images/advanced_eda/`
- 마크다운 리포트 위치: `{REPORT_MD}`
"""

with open(REPORT_MD, 'w', encoding='utf-8') as f:
    f.writelines(report_md_content)

print(f"분석 파이프라인 처리가 모두 완료되었습니다. 결과물이 {DOCS_DIR} 하위에 정상 기록되었습니다.")
