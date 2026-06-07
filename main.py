import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

app = FastAPI()

# 텍스트 데이터 구조 정의
class TripRequest(BaseModel):
    duration: str
    budget: str
    location: str
    member_summary: str

@app.post("/api/generate-trip")
def generate_trip(request: TripRequest):
    # 서버의 환경변수에서 API 키를 가져옵니다. (코드에 직접 노출 X)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="서버에 API 키가 설정되지 않았습니다.")

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
당신은 전세계 최고급 맞춤형 여행사 'Perfect Trip'의 AI 수석 설계사입니다.
아래 조건에 맞춰 여행 리포트를 작성해 주세요.

[여행 조건]
- 여행 구성원: {request.member_summary}
- 여행 기간   : {request.duration}
- 우선 배정 지역: {request.location}
- 전체 예산 한도: {request.budget}만원

(이하 기존 파이썬 코드의 필수 서식 규칙 및 리포트 항목 프롬프트를 그대로 기입)
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"result": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
