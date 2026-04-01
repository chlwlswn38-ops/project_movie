import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
import time

# API 설정 (사용자 키 입력 필요)
API_KEY = "dummy_key_replace_it" 
BASE_URL = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

def collect_kobis_daily_data(movie_master_path):
    # 1. 마스터 데이터 로드
    df_master = pd.read_csv(movie_master_path)
    
    results = []
    
    for _, row in df_master.iterrows():
        movie_title = row['movie_title']
        movie_cd = str(row['movie_cd'])
        open_dt = str(row['open_dt']).replace('-', '') # YYYYMMDD
        
        print(f"[{movie_title}] 수집 시작...")
        
        start_date = datetime.strptime(open_dt, '%Y%m%d')
        
        for i in range(36): # 0~35일
            target_date = (start_date + timedelta(days=i)).strftime('%Y%m%d')
            
            # API 호출
            params = {
                'key': API_KEY,
                'targetDt': target_date
            }
            
            try:
                # raw 저장 경로 (초보자 권장)
                raw_dir = f"../data/raw/kobis_daily/{movie_cd}"
                os.makedirs(raw_dir, exist_ok=True)
                
                resp = requests.get(BASE_URL, params=params)
                data = resp.json()
                
                # Raw JSON 저장
                with open(f"{raw_dir}/{target_date}.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                # 데이터 파싱
                daily_list = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
                found = False
                for movie in daily_list:
                    if movie['movieCd'] == movie_cd:
                        results.append({
                            'movie_title': movie_title,
                            'movie_cd': movie_cd,
                            'target_date': target_date,
                            'days_since_open': i,
                            'rank': movie['rank'],
                            'audi_cnt': movie['audiCnt'],
                            'audi_acc': movie['audiAcc'],
                            'scrn_cnt': movie['scrnCnt'],
                            'sales_share': movie['salesShare']
                        })
                        found = True
                        break
                
                if not found:
                    print(f"  - {target_date}: 순위권(Top 10) 밖")
                    
                time.sleep(0.1) # 과부하 방지
                
            except Exception as e:
                print(f"  - {target_date} 오류: {e}")
                
    # 결과 저장
    df_res = pd.DataFrame(results)
    df_res.to_csv('../data/kobis_boxoffice_daily.csv', index=False, encoding='utf-8-sig')
    print(f"최종 처리 완료: ../data/kobis_boxoffice_daily.csv (총 {len(df_res)}행)")

if __name__ == "__main__":
    # 실행 전 movie_master.csv가 필요함
    # collect_kobis_daily_data('../data/movie_master.csv')
    pass
