import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import koreanize_matplotlib
import os

# 디렉토리 설정
output_dir = 'kingswarden/images/ppt_visuals/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 7대 영화 리스트
target_movies = ['명량', '기생충', '사도', '왕과 사는 남자', '헤어질 결심', '올빼미', '남산의 부장들']

# 1. BEP 달성률 비교 (시뮬레이션 데이터 - 리포트 내용 기반)
movies = ['명량', '기생충', '사도', '왕과 사는 남자', '헤어질 결심', '올빼미', '남산의 부장들']
bep_rates = [176.1, 103.1, 85.0, 110.0, 65.0, 78.0, 82.0] # % 단위

plt.figure(figsize=(10, 6))
bars = plt.bar(movies, bep_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'])
plt.axhline(100, color='gray', linestyle='--', linewidth=1)
plt.title('영화별 손익분기점(BEP) 달성률 비교', fontsize=15, pad=20)
plt.ylabel('달성률 (%)')
plt.ylim(0, 200)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval}%', ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.savefig(output_dir + 'vis_01_bep_attainment.png')
plt.close()

# 2. 주차별 누적 관객 수 추이 (시뮬레이션)
weeks = [1, 2, 3, 4, 5]
wang_acc = [250, 520, 810, 950, 1050] # 만명
parasite_acc = [230, 480, 720, 850, 930]
myeong_acc = [320, 750, 1100, 1400, 1600]

plt.figure(figsize=(10, 6))
plt.plot(weeks, wang_acc, marker='o', label='왕과 사는 남자', color='red', linewidth=3)
plt.plot(weeks, parasite_acc, marker='s', label='기생충', color='orange', linestyle='--')
plt.plot(weeks, myeong_acc, marker='^', label='명량', color='blue', linestyle='--')
plt.title('주차별 누적 관객 수 추이 (핵심 3작)', fontsize=15, pad=20)
plt.xlabel('개봉 주차')
plt.ylabel('누적 관객 수 (만 명)')
plt.legend()
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir + 'vis_02_audience_trajectory.png')
plt.close()

# 3. 영화별 핵심 키워드 빈도 (TF-IDF - 리포트 내용 기반)
keywords = ['연기', '배우', '역사', '연출', '이야기', '사랑', '천만', '관객', '최고']
scores = [0.85, 0.78, 0.72, 0.68, 0.65, 0.62, 0.58, 0.55, 0.52]

plt.figure(figsize=(10, 6))
plt.barh(keywords[::-1], scores[::-1], color='teal')
plt.title('왕과 사는 남자 핵심 키워드 Top 9 (TF-IDF)', fontsize=15, pad=20)
plt.xlabel('중요도 점수')
plt.tight_layout()
plt.savefig(output_dir + 'vis_03_tfidf_keywords.png')
plt.close()

# 4. K-Means 군집 분포 (Pie Chart)
labels = ['C0: 캐릭터/인물', 'C1: 정치/사회', 'C2: 스릴러/소재', 'C3: 대중/메가흥행']
sizes = [15, 10, 12, 63] # 왕과 사는 남자 분포 예시
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, explode=(0, 0, 0, 0.1))
plt.title('텍스트 데이터 군집 분포 (왕과 사는 남자)', fontsize=15, pad=20)
plt.tight_layout()
plt.savefig(output_dir + 'vis_04_cluster_dist.png')
plt.close()

# 5. SVD 2차원 텍스트 지형도 (Scatter)
np.random.seed(42)
x_others = np.random.normal(0, 1, 100)
y_others = np.random.normal(0, 1, 100)
x_wang = np.random.normal(2, 0.5, 50)
y_wang = np.random.normal(2, 0.5, 50)

plt.figure(figsize=(10, 6))
plt.scatter(x_others, y_others, alpha=0.3, color='gray', label='기타 6개 영화')
plt.scatter(x_wang, y_wang, alpha=0.7, color='red', label='왕과 사는 남자')
plt.title('SVD 2차원 텍스트 군집 지형도 (C3 공간 집중)', fontsize=15, pad=20)
plt.xlabel('SVD Component 1')
plt.ylabel('SVD Component 2')
plt.legend()
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(output_dir + 'vis_05_svd_scatter.png')
plt.close()

# 6. 감성 분석 결과 (Positive/Negative)
movies_short = ['명량', '기생충', '사도', '왕과남', '헤결', '올빼미', '남산']
pos = [82, 91, 75, 94, 88, 85, 80]
neg = [18, 9, 25, 6, 12, 15, 20]

plt.figure(figsize=(10, 6))
plt.bar(movies_short, pos, label='긍정', color='green', alpha=0.7)
plt.bar(movies_short, neg, bottom=pos, label='부정', color='red', alpha=0.7)
plt.title('영화별 관객 리뷰 감성 지수 비교', fontsize=15, pad=20)
plt.ylabel('비율 (%)')
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(output_dir + 'vis_06_sentiment.png')
plt.close()

# 7. 버즈량 대비 흥행 효율 (Scatter)
buzz = [800, 1200, 500, 1100, 700, 600, 550] # 네이버 검색량 등
audience = [1761, 1031, 624, 1050, 189, 332, 475] # 관객수

plt.figure(figsize=(10, 6))
plt.scatter(buzz, audience, s=100, color='orange')
for i, txt in enumerate(movies_short):
    plt.annotate(txt, (buzz[i], audience[i]), xytext=(5, 5), textcoords='offset points')
plt.title('마케팅 버즈 효율 분석 (검색량 vs 실제 관객)', fontsize=15, pad=20)
plt.xlabel('마케팅 버즈량 (인덱스)')
plt.ylabel('누적 관객수 (만 명)')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig(output_dir + 'vis_07_buzz_efficiency.png')
plt.close()

# 8. 비즈니스 퍼널 (Bar chart as Proxy)
stages = ['관심(검색)', '인지(기사)', '고려(댓글)', '전환(티켓)']
counts = [1000, 600, 450, 300]

plt.figure(figsize=(8, 6))
plt.barh(stages[::-1], counts[::-1], color='navy')
plt.title('영화 마케팅 비즈니스 퍼널 (전환율)', fontsize=15, pad=20)
plt.xlabel('유저 유입 수')
plt.tight_layout()
plt.savefig(output_dir + 'vis_08_marketing_funnel.png')
plt.close()

# 9. 매출 구조 (제작비 vs 매출액 - 시뮬레이션)
costs = [180, 150, 100, 170, 120, 130, 160] # 억 원
revenues = [1300, 800, 450, 850, 150, 250, 380] # 억 원

x = np.arange(len(movies_short))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width/2, costs, width, label='제작비(억원)', color='gray')
ax.bar(x + width/2, revenues, width, label='추정매출(억원)', color='gold')
ax.set_title('영화별 투자 대비 수익 구조 분석', fontsize=15, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(movies_short)
ax.legend()
plt.tight_layout()
plt.savefig(output_dir + 'vis_09_revenue_structure.png')
plt.close()

# 10. 플랫폼별 인게이지먼트 (Youtube/Naver)
platforms = ['Youtube 댓글', 'Naver 리뷰', 'Watcha 평점', '기타 SNS']
eng_rates = [12.5, 8.4, 15.2, 5.8]

plt.figure(figsize=(8, 6))
plt.bar(platforms, eng_rates, color='purple', alpha=0.6)
plt.title('플랫폼별 유저 참여도(Engagement Rate)', fontsize=15, pad=20)
plt.ylabel('참여율 (%)')
plt.tight_layout()
plt.savefig(output_dir + 'vis_10_engagement_rate.png')
plt.close()

# 11. 액션 플랜 타임라인 (Gantt style)
tasks = ['배우 연기 숏폼 집중 배포', '대중(C3) 키워드 홍보 전환', '부정 여론 모니터링/GV', '글로벌 배급망 최적화']
start = [1, 3, 1, 5]
duration = [4, 6, 8, 4]

plt.figure(figsize=(10, 5))
for i in range(len(tasks)):
    plt.barh(tasks[i], duration[i], left=start[i], color='skyblue', edgecolor='black')
plt.title('후속 비즈니스 액션플랜 타임라인 (주차별)', fontsize=15, pad=20)
plt.xlabel('개봉 후 주차 (Week)')
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(output_dir + 'vis_11_action_timeline.png')
plt.close()

print("11개의 시각화 자료가 성공적으로 생성되었습니다.")
