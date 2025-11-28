# 1. Python 3.11 슬림 버전 사용 (가볍고 안정적)
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치
# (캐싱 효율을 위해 소스 코드보다 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 현재 폴더의 모든 소스 코드를 컨테이너 내부 /app으로 복사
# (app.py, geminiAPI.py, key_manage.py 등이 복사됨)
COPY . .

# 5. Flask 포트 5000번 개방 알림
EXPOSE 5000

# 6. 컨테이너 실행 시 작동할 명령어 (app.py 실행)
CMD ["python", "app.py"]