import google.generativeai as genai
from dotenv import load_dotenv
import fitz
import os

load_dotenv()
try:
    api_key = os.getenv("api_key")
    if not api_key:
        raise ValueError("API 키 누락!!")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"오류:{e}")
    exit()

# 이전까지의 대화 저장
chat_session = genai.GenerativeModel("gemini-2.5-flash").start_chat(history=[])


def input_process(input_data):
    """
    text, image, pdf 등 다양한 유형의 입력을 받아 Gemini API에 전달하여 처리하는 함수.

    Args: input_data

    Returns: Gemini API의 응답 텍스트(혹은 오류)
    """
    contents = []
    base_prompt = """
                    주어진 입력 자료를 분석하여 '벼락치기 학습 자료' 형태로 정리해줘.

1.  **대주제 추출 및 제목화:** 입력 내용의 대주제를 분석하여 가장 먼저 **굵은 글씨**로 제목화하고, 맨 앞에 '###'을 붙여 표시해.
2.  **예상 공부 시간 산출:** 자료의 길이와 복잡성을 고려하여 'XX분' 형식의 **예상 공부 시간**을 산출하고, 대주제 바로 밑에 별도로 표시해.
3.  **내용 분류 및 요약:**
    * 서로 다른 주제일 경우 내용을 명확히 분류하여 소주제를 설정해.
    * 각 소주제별로 **핵심 개념 및 키워드**를 간결하게 정리해.
4.  **시험 핵심 내용 강조:** 요약된 내용 중 **시험에 나올 만한 핵심 내용**은 반드시 **굵은 글씨**로 표시해서 정리해. (이는 나중에 사용자 질문에 답할 때 가장 중요한 근거 자료가 됨)
5.  **[조건부 지시: 문제 생성 시]** 만약 사용자의 요청에 문제 생성이 포함되었다면, 아래 7번 항목에 따라 문제를 생성해야 해.
6.  **최종 출력 형식:** 출력을 다음의 세 가지 주요 섹션으로 구분해서 제공해.
    * **섹션 1: 시험 대비 핵심 요약본:** 대주제, 예상 공부 시간, 분류된 소주제별 핵심 요약(굵은 글씨 강조 포함)이 포함되어야 해.
    * **섹션 2: 입력 자료 전체 텍스트 (원문):** 사용자가 입력한 원문 텍스트를 그대로 여기에 복사해서 넣어.
    * **섹션 3: Gemini의 학습 준비:** '정리된 내용을 토대로 나중에 사용자가 질문하면 정확히 답변할 준비가 완료되었음'을 명시하는 문구를 포함해.
7.  ** 데이터베이스 관리용 문제 목록 (조건부 출력):** 만약 문제 생성이 요청되었다면, 최종 응답의 맨 마지막에 **다른 텍스트 없이** 반드시 `[START_QUESTIONS_JSON]` 마커와 `[END_QUESTIONS_JSON]` 마커 사이에 **JSON 배열 형식**으로만 문제 목록을 출력해야 해. 이 JSON은 데이터베이스 저장을 위한 것이며 사용자에게는 보여주지 않는 것을 원칙으로 해.

    * **JSON 구조:**
      ```json
      [
        {
          "question_id": "Q1",
          "related_topic": "[관련 소주제 제목]",
          "type": "[문제 유형: 예: 주관식, 객관식]",
          "content": "[문제 내용 전체]",
          "answer": "[정답]",
          "explanation": "[해설]"
        },
        // ... 다음 문제 ...
      ]
      ```
8.  **언어 규칙:** 모든 답변은 **한글**로 작성해야 해.
                """

    contents.append(base_prompt)

    try:
        for item in input_data:
            if item["type"] == "text":
                contents.append(item["content"])
            elif item["type"] == "file":
                file = item["file"]
                # 파일 확장자를 기반으로 처리 진행
                file_name = file.filename.lower()

                if file_name.endswith(".pdf"):
                    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
                    # Gemini API는 pdf를 입력으로 받지 않고 이미지를 사용하므로 모든 페이지를 image로 전환
                    for page in pdf_document:
                        pix = page.get_pixmap()
                        contents.append(
                            {"mime_type": "image/png", "data": pix.tobytes("png")}
                        )
                elif file_name.endswith((".jpg", ".jpeg", ".png")):
                    contents.append(
                        {
                            "mime_type": f'image/{file_name.split(".")[-1]}',
                            "data": file.read(),
                        }
                    )
                elif file_name.endswith(".txt"):
                    text_content = file.read().decode("utf-8")
                    contents.append(text_content)
                else:
                    return "지원하지 않는 형식의 파일입니다"
        response = chat_session.send_message(contents, stream=True)
        response.resolve()

        return response.text
    except Exception as e:
        return f"처리 중 오류: {e}"
