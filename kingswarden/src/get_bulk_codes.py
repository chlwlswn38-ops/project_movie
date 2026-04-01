import os
import requests
from dotenv import load_dotenv

load_dotenv('../.env')
api_key = os.getenv('KOBIS_API_KEY')
url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json'

# Group B: 5M-9M (20 movies)
group_b = [
    '한산: 용의 출현', '공조2: 인터내셔날', '베테랑2', '밀수', '하얼빈', 
    '노량: 죽음의 바다', '엑시트', '백두산', '안시성', '내부자들', 
    '인천상륙작전', '마스터', '청년경찰', '1987', '완벽한 타인', 
    '독전', '강철비', '남한산성', '꾼', '히말라야'
]

# Group A: 100만-500만 (20 movies)
group_a = [
    '모가디슈', '싱크홀', '헌트', '올빼미', '영웅', 
    '콘크리트 유토피아', '파일럿', '탈주', '교섭', '핸섬가이즈', 
    '인질', '보이스', '시민덕희', '외계+인 2부', '슬립', 
    '드림', '마녀', '곤지암', '박열', '나쁜 녀석들: 더 무비'
]

all_movies = group_b + group_a

print("--- KOBIS 영화 코드 대량 검색 ---")
results = []
for m in all_movies:
    params = {'key': api_key, 'movieNm': m}
    res = requests.get(url, params=params).json()
    items = res.get('movieListResult', {}).get('movieList', [])
    if items:
        # 가장 검색어에 근접한 첫 번째 항목 (또는 개봉일 있는 항목)
        best = items[0]
        for item in items:
            if item['movieNm'] == m and item['openDt']:
                best = item
                break
        results.append({
            "title": m,
            "movie_code": best['movieCd'],
            "opening_date": best['openDt']
        })
        print(f"성공: {m} -> {best['movieCd']} ({best['openDt']})")
    else:
        print(f"실패: {m} 검색 결과 없음")

import json
with open("comparison_list.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nJSON 저장 완료!")
