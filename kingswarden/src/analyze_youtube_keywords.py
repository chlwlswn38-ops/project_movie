import pandas as pd
import os
import re
from collections import Counter
import json

# 한국어 형태소 분석기 (간이 정규식 기반 토큰화 또는 유틸리티 함수 사용)
# 실제 환경에서는 konlpy 등을 사용하나, 여기서는 정규식과 불용어 리스트로 구현
def get_tokens(text):
    if not isinstance(text, str): return []
    # 한글만 추출
    tokens = re.findall(r'[가-힣]+', text)
    # 2글자 이상만
    return [t for t in tokens if len(t) >= 2]

def analyze_standardized_keywords(comments_csv, metrics_csv, metadata_path):
    df_comments = pd.read_csv(comments_csv)
    df_metrics = pd.read_csv(metrics_csv)
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 영화별 제목 토큰 Blacklist 생성
    movie_blacklists = {}
    for movie in metadata['pilot_movies']:
        title = movie['title']
        movie_blacklists[title] = set(get_tokens(title))
    
    # 비디오별 제목 토큰 Blacklist 생성
    video_blacklists = {}
    video_labels = {}
    for _, row in df_metrics.iterrows():
        v_id = row['video_id']
        v_title = row['title']
        video_blacklists[v_id] = set(get_tokens(v_title))
        
        # 라벨링 (Heuristic)
        label = 'clip' # 기본값
        if '메인' in v_title and '예고' in v_title: label = 'trailer'
        elif '티저' in v_title or '런칭' in v_title: label = 'teaser'
        elif '인터뷰' in v_title or '제작보고회' in v_title: label = 'interview'
        elif '메이킹' in v_title or '비하인드' in v_title: label = 'making'
        video_labels[v_id] = label

    # 공통 불용어
    common_stopwords = {'진짜','너무','인출','영화','정말','보고','보다','하다','있다','되다','쇼박스','배급사','개봉','관객','영화관'}

    results = []
    
    for movie in df_comments['movie_title'].unique():
        m_comments = df_comments[df_comments['movie_title'] == movie]
        m_blacklist = movie_blacklists.get(movie, set())
        
        for v_id in m_comments['video_id'].unique():
            v_comments = m_comments[m_comments['video_id'] == v_id]
            v_blacklist = video_blacklists.get(v_id, set())
            label = video_labels.get(v_id, 'clip')
            
            # 모든 블랙리스트 결합
            total_blacklist = common_stopwords | m_blacklist | v_blacklist
            
            all_tokens = []
            for comment in v_comments['text']:
                tokens = get_tokens(comment)
                filtered = [t for t in tokens if t not in total_blacklist]
                all_tokens.extend(filtered)
            
            # 상위 30개 추출
            counts = Counter(all_tokens).most_common(30)
            for rank, (word, count) in enumerate(counts, 1):
                results.append({
                    'movie_title': movie,
                    'label': label,
                    'keyword': word,
                    'count': count,
                    'rank': rank,
                    'source': 'YouTube Comments'
                })
                
    result_df = pd.DataFrame(results)
    return result_df

# 실행
comments_path = '../data/youtube_comments.csv'
metrics_path = '../data/youtube_metrics.csv'
metadata_path = '../docs/pilot_metadata.json'

if os.path.exists(comments_path) and os.path.exists(metrics_path):
    print("고도화된 유튜브 키워드 분석 시작...")
    keywords_top = analyze_standardized_keywords(comments_path, metrics_path, metadata_path)
    
    # 저장
    output_path = '../data/youtube_keywords_top.csv'
    keywords_top.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"성공: {output_path} 저장 완료.")
    print("\n[샘플 결과: 왕과 사는 남자 - trailer]")
    print(keywords_top[(keywords_top['movie_title'] == '왕과 사는 남자') & (keywords_top['label'] == 'trailer')].head(5))
else:
    print("필요한 데이터 파일이 없습니다.")
