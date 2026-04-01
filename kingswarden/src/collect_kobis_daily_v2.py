import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
import numpy as np
import time

# [설정] KOBIS API 키
API_KEY = "c8063b308962f96f862aac7d24f888ff" 
BASE_URL = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

def collect_kobis_v2():
    # 1. movie_master 로드
    master_path = '../data/movie_master.csv'
    if not os.path.exists(master_path):
        print("movie_master.csv 파일이 없습니다. 가이드를 따라 먼저 생성하세요.")
        return
    
    df_master = pd.read_csv(master_path)
    
    # 2. 결과 저장용 리스트
    total_results = []
    
    # 데이터 저장 디렉토리 생성
    os.makedirs('../data/raw/kobis_daily', exist_ok=True)
    
    for _, row in df_master.iterrows():
        movie_title = row['movie_title']
        movie_cd = str(row['movie_cd'])
        release_date = str(row['release_date']) # YYYY-MM-DD
        
        print(f"\n>>> [{movie_title}] 수집 프로세스 시작")
        
        start_dt = datetime.strptime(release_date, '%Y-%m-%d')
        
        # 3. 날짜 범위 생성 (개봉일~+34일 = 총 35일)
        for i in range(35):
            target_date = (start_dt + timedelta(days=i)).strftime('%Y%m%d')
            raw_path = f"../data/raw/kobis_daily/{movie_cd}_{target_date}.json"
            
            # 4. 체크포인트 설계: 이미 수집된 파일이 있으면 건너뜀
            if os.path.exists(raw_path):
                # print(f"  - {target_date}: 이미 존재 (Skip API)")
                with open(raw_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # 5. API 호출 (재시도 로직 포함)
                data = None
                for attempt in range(3): # 최대 3회 시도
                    try:
                        resp = requests.get(BASE_URL, params={'key': API_KEY, 'targetDt': target_date}, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            # Raw JSON 저장
                            with open(raw_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=4)
                            print(f"  - {target_date}: API 호출 성공 및 저장")
                            break
                        else:
                            print(f"  - {target_date}: HTTP 오류 {resp.status_code} (시도 {attempt+1}/3)")
                    except Exception as e:
                        print(f"  - {target_date}: 연결 실패 {e} (시도 {attempt+1}/3)")
                    
                    time.sleep(1) # 재시도 전 대기
                
                time.sleep(0.2) # API 서버 부하 방지
            
            # 6. 데이터 정제 (JSON -> Flatten)
            if data:
                daily_list = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
                movie_data = next((m for m in daily_list if m['movieCd'] == movie_cd), None)
                
                if movie_data:
                    total_results.append({
                        'movie_title': movie_title,
                        'movie_cd': movie_cd,
                        'target_date': target_date,
                        'days_since_open': i,
                        'rank': int(movie_data['rank']),
                        'audi_cnt': int(movie_data['audiCnt']),
                        'audi_acc': int(movie_data['audiAcc']),
                        'scrn_cnt': int(movie_data['scrnCnt']),
                        'sales_share': float(movie_data['salesShare'])
                    })
                else:
                    # Top 10 밖으로 밀려난 경우 (누락 대응)
                    total_results.append({
                        'movie_title': movie_title,
                        'movie_cd': movie_cd,
                        'target_date': target_date,
                        'days_since_open': i,
                        'rank': 0, # 0은 순위권 밖을 의미
                        'audi_cnt': 0,
                        'audi_acc': np.nan, # 누적은 이전 값을 참조해야 하므로 결측치 처리
                        'scrn_cnt': 0,
                        'sales_share': 0.0
                    })

    # 7. 최종 결과 통합 저장
    if total_results:
        df_final = pd.DataFrame(total_results)
        # 누적 관객수 결측치 채우기 (Forward Fill)
        df_final['audi_acc'] = df_final.groupby('movie_title')['audi_acc'].ffill().fillna(0).astype(int)
        
        df_final.to_csv('../data/kobis_boxoffice_daily.csv', index=False, encoding='utf-8-sig')
        print(f"\n[완료] kobis_boxoffice_daily.csv 저장 완료 (총 {len(df_final)}행)")
    else:
        print("\n[알림] 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    import numpy as np
    # collect_kobis_v2() # 실행 시 주석 해제
    pass
