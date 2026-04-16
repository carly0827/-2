# Lecture Sync WebApp (Quick Version)

아이패드 Safari에서 쓰기 쉬운 빠른 웹앱 버전입니다.

## 기능
- 강의록 PDF 업로드
- 전사본 업로드 (json / srt / txt)
- 자동 필기 PDF 생성
- 결과 PDF / 매칭 JSON 다운로드
- 연습문제/기출문제만 있고 설명이 거의 없는 페이지 자동 건너뛰기

## 실행
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000` 접속

## Render 배포
Start Command:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## 포함 파일
- `app.py`: FastAPI 웹앱
- `templates/`: 업로드/결과 화면
- `static/`: CSS
- `lecture_sync_annotator/`: 기존 PDF 생성 엔진
