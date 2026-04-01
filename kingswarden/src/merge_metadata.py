import json
import os

# 기존 메타데이터 로드
with open("../docs/pilot_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# 자동 조회된 비교군 리스트 로드
with open("comparison_list.json", "r", encoding="utf-8") as f:
    comp_list = json.load(f)

# 수동 보정 데이터 (KOBIS 재검색 결과 반영)
fixed_data = {
    "독전": ("20176140", "20180522"),
    "영웅": ("20196478", "20221221"),
    "슬립": ("20211942", "20230906"),
    "보이스": ("20190207", "20210915"),
    "마녀": ("20170513", "20180627"),
    "마스터": ("20150970", "20161221"),
    "꾼": ("20165748", "20171122"),
    "드림": ("20191221", "20230426"),
    "하얼빈": ("20228796", "20241224"), # 확인
    "베테랑2": ("20239670", "20240913")
}

# 이미 존재하는 영화 제목 리스트
existing_titles = [m['title'] for m in metadata['pilot_movies']]

for item in comp_list:
    title = item['title']
    if title in existing_titles: continue
    
    # 보정 데이터 적용
    if title in fixed_data:
        code, date = fixed_data[title]
    else:
        code, date = item['movie_code'], item['opening_date']
    
    # 데이터가 유효한 경우만 추가
    if code and date:
        metadata['pilot_movies'].append({
            "title": title,
            "english_title": "", # 필요 시 추가 가능
            "movie_code": code,
            "opening_date": date,
            "youtube_video_ids": []
        })

# 최종 메타데이터 저장
with open("../docs/pilot_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"메타데이터 업데이트 완료! 총 영화 수: {len(metadata['pilot_movies'])}편")
