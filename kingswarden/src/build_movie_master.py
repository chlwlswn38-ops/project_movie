import pandas as pd

# 1. 히트 영화 정의
hit_movies = ['명량', '극한직업', '파묘', '서울의 봄', '범죄도시2', '신과함께-죄와 벌', '국제시장', '왕과 사는 남자']

# 2. 원천 데이터에서 영화 목록 추출 (YouTube 기준)
df_y = pd.read_csv('../data/youtube_comments.csv')
all_movies = df_y['movie_title'].unique().tolist()

# 3. KOBIS 관객 데이터에서 개봉일 추정
df_k = pd.read_csv('../data/kobis_audience.csv')
open_dt_map = df_k.groupby('movie_title')['target_date'].min().to_dict()

# 4. movie_master 생성
master_data = []
for movie in all_movies:
    group = 'Hit' if movie in hit_movies else 'Compare'
    is_10m = True if movie in hit_movies else False
    
    # 개봉일 (YYYY-MM-DD 형식으로 변환)
    odt_raw = str(open_dt_map.get(movie, "20240101"))
    odt = f"{odt_raw[:4]}-{odt_raw[4:6]}-{odt_raw[6:]}"
    
    master_data.append({
        'movie_title': movie,
        'movie_cd': "DUMMY_" + movie[:2], # 실제 코드 대신 더미 코드 부여 (검색 API 연동 전)
        'release_date': odt,
        'group': group,
        'is_10m': is_10m
    })

df_master = pd.DataFrame(master_data)
df_master.to_csv('../data/movie_master.csv', index=False, encoding='utf-8-sig')

print(f"movie_master.csv 업데이트 완료: {len(df_master)}편")
