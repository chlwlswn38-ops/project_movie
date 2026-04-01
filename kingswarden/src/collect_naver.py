import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_naver_search_results(query, display=100, start=1, sort='date', target='blog'):
    """
    네이버 검색 API를 호출하여 결과를 반환합니다.
    target: 'blog' 또는 'cafearticle'
    """
    url = f"https://openapi.naver.com/v1/search/{target}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print(f"오류 발생 ({target}): {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"예외 발생: {str(e)}")
        return []

def filter_by_date(items, days=30):
    """
    최근 n일 이내의 데이터만 필터링합니다.
    """
    filtered_items = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for item in items:
        # 네이버 'postdate' 형식: YYYYMMDD
        try:
            postdate_str = item.get('postdate')
            if postdate_str:
                post_dt = datetime.strptime(postdate_str, '%Y%m%d')
                if post_dt >= cutoff_date:
                    filtered_items.append(item)
        except Exception:
            # 날짜 형식이 다르거나 없는 경우 (카페 등은 다를 수 있음)
            filtered_items.append(item)
            
    return filtered_items

def collect_naver_data():
    # 1. 메타데이터 로드
    metadata_path = "../docs/pilot_metadata.json"
    if not os.path.exists(metadata_path):
        print(f"오류: {metadata_path} 파일을 찾을 수 없습니다.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    movies = metadata.get("pilot_movies", [])
    blog_target = metadata.get("collection_targets", {}).get("naver_blog_per_movie", 200)
    cafe_target = metadata.get("collection_targets", {}).get("naver_cafe_per_movie", 200)
    filter_days = metadata.get("collection_targets", {}).get("naver_date_filter_days", 30)

    all_data = []

    for movie in movies:
        movie_name = movie['title']
        print(f"\n[{movie_name}] 수집 시작...")

        # 블로그 수집
        print(f"- 블로그 수집 중 (목표: {blog_target})...")
        blogs = []
        for start in range(1, blog_target + 1, 100):
            res = get_naver_search_results(movie_name, display=100, start=start, target='blog')
            blogs.extend(res)
            if len(res) < 100: break
        
        filtered_blogs = filter_by_date(blogs, days=filter_days)
        for b in filtered_blogs:
            all_data.append({
                "movie_title": movie_name,
                "channel": "blog",
                "title": b.get("title"),
                "link": b.get("link"),
                "description": b.get("description"),
                "postdate": b.get("postdate")
            })

        # 카페 수집
        print(f"- 카페 수집 중 (목표: {cafe_target})...")
        cafes = []
        for start in range(1, cafe_target + 1, 100):
            res = get_naver_search_results(movie_name, display=100, start=start, target='cafearticle')
            cafes.extend(res)
            if len(res) < 100: break
            
        filtered_cafes = filter_by_date(cafes, days=filter_days)
        for c in filtered_cafes:
            all_data.append({
                "movie_title": movie_name,
                "channel": "cafe",
                "title": c.get("title"),
                "link": c.get("link"),
                "description": c.get("description"),
                "postdate": c.get("postdate")
            })

    # 2. 결과 저장
    if all_data:
        df = pd.DataFrame(all_data)
        save_path = "../data/naver_review_proxy.csv"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        print(f"\n성공: 총 {len(all_data)}건의 데이터를 {save_path}에 저장했습니다.")
    else:
        print("\n경고: 수집된 데이터가 없습니다. API 키나 검색어를 확인하세요.")

if __name__ == "__main__":
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("오류: NAVER_CLIENT_ID 및 NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")
        print(".env 파일을 확인해 주세요.")
    else:
        collect_naver_data()
