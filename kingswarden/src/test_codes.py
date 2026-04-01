import os
import requests
from dotenv import load_dotenv

# .env 파일에서 KOBIS_API_KEY 로드
load_dotenv('../.env')
api_key = os.getenv('KOBIS_API_KEY')
url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json'

movies = ['파묘', '서울의 봄', '범죄도시2', '신과함께', '국제시장']
print("--- KOBIS 영화 코드 검색 결과 (추가 5편) ---")
for m in movies:
    params = {'key': api_key, 'movieNm': m}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json().get('movieListResult', {}).get('movieList', [])
            # 영화명 일치 여부 확인
            results = [ (i.get('movieNm'), i.get('movieCd'), i.get('openDt')) for i in items if m in i.get('movieNm') ]
            print(f"{m}: {results}")
        else:
            print(f"{m} 검색 실패: {response.status_code}")
    except Exception as e:
        print(f"{m} 예외 발생: {str(e)}")
