import os
import threading
import time
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

app = FastAPI()

# ── Keep-Alive: 10분마다 자기 자신에 핑 (Render 슬립 방지) ────
def keep_alive():
    # 서버 완전 기동 후 시작되도록 60초 대기
    time.sleep(60)
    url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not url:
        print("[keep-alive] RENDER_EXTERNAL_URL 환경변수 없음 — 슬립 방지 비활성")
        return
    ping_url = f"{url}/ping"
    while True:
        try:
            r = requests.get(ping_url, timeout=10)
            print(f"[keep-alive] ping → {r.status_code}")
        except Exception as e:
            print(f"[keep-alive] 오류: {e}")
        time.sleep(600)  # 10분

threading.Thread(target=keep_alive, daemon=True).start()

# ── 헬스체크 엔드포인트 (keep-alive 핑 대상) ────────────────────
@app.get("/ping")
def ping():
    return {"status": "ok"}

# ── 요청 데이터 구조 ────────────────────────────────────────────
class TripRequest(BaseModel):
    duration: str
    budget: str
    location: str
    member_summary: str

# ── 리포트 생성 엔드포인트 ──────────────────────────────────────
@app.post("/api/generate-trip")
def generate_trip(request: TripRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="서버에 API 키가 설정되지 않았습니다.")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
당신은 전세계 최고급 맞춤형 여행사 'Perfect Trip'의 AI 수석 설계사입니다.
아래 조건에 맞춰, 한글(HWP) 또는 MS 워드(Word)에 복사·붙여넣기하여 바로 출력할 수 있는
완성형 리포트를 작성해 주세요.

[여행 조건]
- 여행 구성원: {request.member_summary}
- 여행 기간   : {request.duration}
- 우선 배정 지역: {request.location}
- 전체 예산 한도: {request.budget}만원

[필수 서식 규칙]
1. 글꼴 기준: 맑은 고딕(Malgun Gothic) 13pt
2. 용지 기준: A4 세로(Portrait), 좌우 여백 포함 시 한 줄 약 32~36자 이내로 작성
3. 표(Table): 마크다운 표준(| — |) 사용, 각 셀은 짧고 간결하게 유지
4. 금액 단위: '만원' 또는 '원'으로 통일
5. 일정 요약 및 경비 배분은 반드시 표 형식으로 출력

[리포트 항목 — 순서 준수]

1. ■ Perfect Trip 팀 빌딩 분석
   - MBTI 궁합 분석 및 여행 테마 제안

2. ■ 핵심 일정 요약표 (표 형식 필수)
   컬럼: 일차 | 날짜(D+n) | 주요 도시 | 오전 일정 | 오후·야간 일정 | 이동수단

3. ■ 항목별 예산 배분표 (표 형식 필수)
   컬럼: 지출 항목 | 예산(만원) | 세부 기준

4. ■ 낙오 방지용 소통·갈등 제어 팁

5. ■ [참고] MBTI 유형별 여행 성향 표 (16유형 전부 포함, 표 형식 필수)
   컬럼: MBTI | 여행 스타일 | 선호 활동 | 동행 시 주의점
   포함 유형(빠짐없이): INTJ, INTP, ENTJ, ENTP,
                        INFJ, INFP, ENFJ, ENFP,
                        ISTJ, ISFJ, ESTJ, ESFJ,
                        ISTP, ISFP, ESTP, ESFP
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"result": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
