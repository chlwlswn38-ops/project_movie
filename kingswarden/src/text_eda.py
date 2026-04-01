import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. 파일 경로 설정
BASE_DIR = '/Users/me/icb6/antigravity_project/project_s_movie/kingswarden/king_all'
DATA_PATH = os.path.join(BASE_DIR, 'data/watcha_reviews_popular_integrated.csv')
OUTPUT_IMG_DIR = os.path.join(BASE_DIR, 'images/eda')
OUTPUT_DOC_DIR = os.path.join(BASE_DIR, 'docs')

os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DOC_DIR, exist_ok=True)

print("1. 데이터 파악 및 정제")
df = pd.read_csv(DATA_PATH)
text_col = 'review_text'

# 기본 EDA 정보 문자열 생성
eda_info = []
eda_info.append("## 1. 기본 EDA 결과\n")
eda_info.append(f"- 총 데이터 수: {len(df)}")
eda_info.append(f"- 결측치 수 ({text_col}): {df[text_col].isnull().sum()}")

# 데이터 정제 (결측치 제거)
df_clean = df.dropna(subset=[text_col]).copy()
eda_info.append(f"- 분석 대상 데이터 수 (결측치 제거 후): {len(df_clean)}\n")
eda_info.append("### 데이터 샘플 (상위 5건)\n")
eda_info.append(df_clean.head().to_markdown(index=False) + "\n\n")

print("\n".join(eda_info))

# 2. 전처리 및 TF-IDF 벡터화 (형태소 분석기 미사용)
print("2. 텍스트 전처리 및 TF-IDF 벡터화")

def simple_preprocess(text):
    if not isinstance(text, str):
        return ""
    # 한글, 영문, 숫자, 공백만 남기고 제거
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
    # 다중 공백은 단일 공백으로 치환
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df_clean['cleaned_text'] = df_clean[text_col].apply(simple_preprocess)

# TF-IDF 벡터화
# min_df 은 5, 단어 토큰은 2글자 이상 단어로 제한 (한글 특징상)
vectorizer = TfidfVectorizer(
    min_df=5,
    max_features=1000, 
    token_pattern=r"(?u)\b[가-힣a-zA-Z0-9]{2,}\b" # 2글자 이상
)

tfidf_matrix = vectorizer.fit_transform(df_clean['cleaned_text'])
feature_names = vectorizer.get_feature_names_out()

# 3. 빈도수 추출 (TF-IDF 합산 기준)
sums = tfidf_matrix.sum(axis=0).A1
word_scores = pd.DataFrame({'word': feature_names, 'score': sums})
top_30_words = word_scores.sort_values(by='score', ascending=False).head(30)

print("3. 상위 30개 단어 처리")
# 시각화: 상위 30개 단어 빈도(TF-IDF 누적) 막대 그래프
plt.figure(figsize=(12, 8))
plt.bar(top_30_words['word'], top_30_words['score'], color='skyblue')
plt.title('상위 30개 단어 TF-IDF 중요도 빈도')
plt.xlabel('단어')
plt.ylabel('TF-IDF 합산 점수')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_IMG_DIR, 'top30_words_tfidf.png'), dpi=300)
plt.close()

top_30_md = top_30_words.to_markdown(index=False)

# 4. TF-IDF 매트릭스 히트맵 시각화 및 표 출력 (상위 10개 행, 열 50개)
print("4. 상위 10행, 50열 히트맵 처리")
top_50_words = word_scores.sort_values(by='score', ascending=False).head(50)['word'].tolist()
top_50_indices = [vectorizer.vocabulary_[word] for word in top_50_words]

# 상위 10개 행 (단순 순서 기준 or 제일 점수가 높은 문서? 문서 중요도를 단순히 순번(0~9)으로 설정)
# 리뷰 텍스트가 긴 상위 10개나, 단순 인덱스 10개를 선정함 (여기서는 0~9번 문서)
top_10_matrix = tfidf_matrix[0:10, top_50_indices].toarray()
heatmap_df = pd.DataFrame(top_10_matrix, columns=top_50_words, index=[f"Doc {i}" for i in range(10)])

# 히트맵 시각화
plt.figure(figsize=(15, 5))
plt.imshow(heatmap_df.values, cmap='YlGnBu', aspect='auto')
plt.colorbar(label='TF-IDF Score')
plt.title('TF-IDF 매트릭스 상위 10문서 x 상위 50단어 히트맵')
plt.xticks(ticks=np.arange(len(top_50_words)), labels=top_50_words, rotation=90)
plt.yticks(ticks=np.arange(10), labels=heatmap_df.index)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_IMG_DIR, 'tfidf_heatmap.png'), dpi=300)
plt.close()

heatmap_md = heatmap_df.to_markdown()

# 5. 리포트 저장
print("5. 리포트 생성 중")
report_content = [
    "# 영화 리뷰 데이터 (Watcha) 기본 EDA 및 TF-IDF 분석\n",
    "\n".join(eda_info),
    "## 2. 전처리 및 TF-IDF 분석\n",
    "- 형태소 분석기 미사용, 특수문자 제거 후 띄어쓰기 기준 (2글자 이상) 토큰화 진행.\n",
    "- TF-IDF를 통해 문서-단어 행렬 계산 후 상위 30개 단어 도출.\n\n",
    "### 상위 30개 단어 (TF-IDF Sum 기준)\n",
    "![Top 30 Words](../images/eda/top30_words_tfidf.png)\n",
    "\n#### 표 결과\n",
    top_30_md,
    "\n\n## 3. TF-IDF 매트릭스 히트맵 (상위 10개 문서 x 상위 50개 단어)\n",
    "![Heatmap](../images/eda/tfidf_heatmap.png)\n",
    "\n#### 히트맵 표 결과\n",
    heatmap_md
]

with open(os.path.join(OUTPUT_DOC_DIR, 'eda_report.md'), 'w', encoding='utf-8') as f:
    f.writelines('\n'.join(report_content))

print("완료되었습니다. 결과물은 images/eda와 docs/에 저장되었습니다.")
