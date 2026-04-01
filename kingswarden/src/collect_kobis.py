import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()

KOBIS_API_KEY = os.getenv("KOBIS_API_KEY")

def get_daily_boxoffice(target_date):
    """
    특정 날짜의 박스오피스 데이터를 가져옵니다.
    target_date: YYYYMMDD
    """
    url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": KOBIS_API_KEY,
        "targetDt": target_date
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        else:
            print(f"오류: {target_date} 데이터 수집 실패 ({response.status_code})")
            return []
    except Exception as e:
        print(f"예외 발생 ({target_date}): {str(e)}")
        return []

def collect_kobis_data():
    # 1. 메타데이터 로드
    metadata_path = "../docs/pilot_metadata.json"
    if not os.path.exists(metadata_path):
        print(f"오류: {metadata_path} 파일을 찾을 수 없습니다.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    movies = metadata.get("pilot_movies", [])
    
    all_data = []

    print(f"KOBIS 영화별 개봉 초기 30일 관객수 수집 시작...")

    for movie in movies:
        movie_name = movie['title']
        movie_code = movie.get('movie_code')
        opening_date_str = movie.get('opening_date')
        
        if not opening_date_str or not movie_code:
            print(f"경고: {movie_name}의 필수 정보(개봉일/코드)가 없어 건너뜜.")
            continue
            
        opening_dt = datetime.strptime(opening_date_str, "%Y%m%d")
        print(f"\n[{movie_name}] ({opening_date_str}) 수집 중 (코드: {movie_code})...")

        for i in range(0, 31):
            target_dt = (opening_dt + timedelta(days=i)).strftime("%Y%m%d")
            daily_list = get_daily_boxoffice(target_dt)
            found = False
            for item in daily_list:
                # 영화 코드로 정확히 매칭
                if item.get("movieCd") == movie_code:
                    all_data.append({
                        "movie_title": movie_name,
                        "target_date": target_dt,
                        "rank": item.get("rank"),
                        "audi_cnt": item.get("audiCnt"),
                        "audi_acc": item.get("audiAcc"),
                        "scrn_cnt": item.get("scrnCnt")
                    })
                    found = True
                    break
            if not found:
                print(f"  > {target_dt}: 박스오피스 순위권(Top 10) 밖입니다.")
        
    # 2. 결과 저장
    if all_data:
        df = pd.DataFrame(all_data)
        save_path = "../data/kobis_audience.csv"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        print(f"\n성공: 총 {len(all_data)}건의 관객수 데이터를 {save_path}에 저장했습니다.")
    else:
        print("\n경고: 최근 30일 박스오피스 결과 중 대상 영화가 없습니다.")
        print("상영 중인 영화가 아닌 경우 KOBIS 영화 상세 정보 API를 통한 기간 조회가 필요할 수 있습니다.")

if __name__ == "__main__":
    if not KOBIS_API_KEY:
        print("오류: KOBIS_API_KEY 환경 변수가 설정되지 않았습니다.")
        print(".env 파일을 확인해 주세요.")
    else:
        collect_kobis_data()
