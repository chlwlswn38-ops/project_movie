import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv('../.env')
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_valid_video_ids(movie_name, max_results=5):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    query = f"영화 {movie_name} 공식 예고편"
    
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        order="viewCount" # 조회수 높은 순으로 검색
    )
    response = request.execute()
    
    video_ids = []
    for item in response.get("items", []):
        video_ids.append(item['id']['videoId'])
    
    return video_ids

def update_metadata_with_real_ids():
    metadata_path = "../docs/pilot_metadata.json"
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    for movie in metadata['pilot_movies']:
        print(f"[{movie['title']}] 유효한 영상 ID 검색 중...")
        real_ids = search_valid_video_ids(movie['title'])
        if real_ids:
            movie['youtube_video_ids'] = real_ids
            print(f"  > 발견된 ID: {real_ids}")
        else:
            print(f"  > 검색 결과 없음")
            
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print("\n메타데이터 업데이트 완료!")

if __name__ == "__main__":
    update_metadata_with_real_ids()
