import os
import json
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_youtube_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def fetch_video_metrics(youtube, video_ids):
    """
    영상 ID 목록에 대한 조회수, 좋아요, 댓글수 등의 지표를 수집합니다.
    """
    request = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    )
    response = request.execute()
    
    metrics = []
    for item in response.get("items", []):
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        metrics.append({
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "view_count": stats.get("viewCount"),
            "like_count": stats.get("likeCount"),
            "comment_count": stats.get("commentCount")
        })
    return metrics

def fetch_video_comments(youtube, video_id, max_results=500):
    """
    특정 영상의 댓글을 수집합니다.
    """
    comments = []
    next_page_token = None
    
    while len(comments) < max_results:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        try:
            response = request.execute()
            for item in response.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                comments.append({
                    "video_id": video_id,
                    "author": snippet.get("authorDisplayName"),
                    "text": snippet.get("textDisplay"),
                    "published_at": snippet.get("publishedAt"),
                    "like_count": snippet.get("likeCount")
                })
                if len(comments) >= max_results:
                    break
            
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        except Exception as e:
            print(f"댓글 수집 중 오류 (VideoId: {video_id}): {str(e)}")
            break
            
    return comments

def collect_youtube_data():
    # 1. 메타데이터 로드
    metadata_path = "../docs/pilot_metadata.json"
    if not os.path.exists(metadata_path):
        print(f"오류: {metadata_path} 파일을 찾을 수 없습니다.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    movies = metadata.get("pilot_movies", [])
    comment_range = metadata.get("collection_targets", {}).get("youtube_comments_per_video", [200, 500])
    max_comments = comment_range[1]

    youtube = get_youtube_client()
    
    all_metrics = []
    all_comments = []

    for movie in movies:
        movie_name = movie['title']
        video_ids = movie['youtube_video_ids']
        print(f"\n[{movie_name}] 유튜브 데이터 수집 시작...")

        # 영상 지표 수집
        print(f"- 영상 지표 수집 중 (영상수: {len(video_ids)})...")
        metrics = fetch_video_metrics(youtube, video_ids)
        for m in metrics:
            m['movie_title'] = movie_name
            all_metrics.append(m)

        # 댓글 수집
        for vid in video_ids:
            print(f"  > 비디오 ID {vid} 댓글 수집 중 (목표: {max_comments})...")
            comments = fetch_video_comments(youtube, vid, max_results=max_comments)
            for c in comments:
                c['movie_title'] = movie_name
                all_comments.append(c)

    # 2. 결과 저장
    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        metrics_save_path = "../data/youtube_metrics.csv"
        os.makedirs(os.path.dirname(metrics_save_path), exist_ok=True)
        metrics_df.to_csv(metrics_save_path, index=False, encoding="utf-8-sig")
        print(f"\n성공: 영상 지표 {len(all_metrics)}건 저장 완료 ({metrics_save_path})")

    if all_comments:
        comments_df = pd.DataFrame(all_comments)
        comments_save_path = "../data/youtube_comments.csv"
        os.makedirs(os.path.dirname(comments_save_path), exist_ok=True)
        comments_df.to_csv(comments_save_path, index=False, encoding="utf-8-sig")
        print(f"성공: 댓글 {len(all_comments)}건 저장 완료 ({comments_save_path})")

if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        print("오류: YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print(".env 파일을 확인해 주세요.")
    else:
        # google-api-python-client 라이브러리가 필요합니다.
        try:
            collect_youtube_data()
        except ImportError:
            print("오류: 'google-api-python-client' 라이브러리가 설치되어 있지 않습니다.")
            print("'uv pip install google-api-python-client' 명령어로 설치하세요.")
