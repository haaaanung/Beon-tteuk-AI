import google.generativeai as genai
import fitz
import os
import time

import key_manage

num_of_keys = len(key_manage.api_keys) 

def lock_and_retry(api_key, input_data):
    # 할당량 초과 시 키를 잠그고 재시도하는 로직을 분리하여 재귀 호출을 관리합니다.
    # 현재 키 할당량 초과시 24H 잠금
    key_manage.lock_key(api_key)
    
    # 다음 키 요청
    print(" 다음 사용 가능한 키로 요청 재시도")
    
    # 짧게 대기하여 API 과부하 방지.
    time.sleep(1)
    
    return input_process(input_data) 



def input_process(input_data):
    # text, image, pdf 등 다양한 유형의 입력을 받아 Gemini API에 전달하여 처리하는 함수.
    # Args: input_data
    # Returns: Gemini API의 응답 텍스트(혹은 오류)


    # 아래 내용은 대화 내용 저장을 위한 코드
    # 최초 호출 시 빈 history로 시작
    if not hasattr(input_process, 'history'):
        input_process.history = []

    # 사용 가능한 키 불러오기
    api_key = key_manage.get_next_available_key(num_of_keys)
    
    if api_key is None: # 모든 API 키가 잠겼을 때
        soonest_time = key_manage.get_soonest_unlock_time()

        if soonest_time:
            unlock_time_str = soonest_time.strftime('%Y년 %m월 %d일 %H시 %M분')
            return "경고: 현재 모든 API 키가 할당량 초과로 잠금 상태입니다. \
                    가장 빠른 잠금 해제 시간은 [{unlock_time_str}] 입니다."

    # 현재 키로 API 설정 및 세션 로드/생성
    genai.configure(api_key = api_key)
    
    # key별 대화 세션 관리 >> 대화 연속성 유지
    if api_key not in key_manage.chat_session:
        # key별 대화 세션이 없으면 현재 통합 기록으로 새로 생성
        key_manage.chat_session[api_key] = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=input_process.history)
    
    chat_session = key_manage.chat_session[api_key]

    contents = []
    base_prompt = """
    야, 정신 차려. 네가 나한테 뭘 시키든 딱 세 가지 상황 중 하나로 처리할 거야. **자료 입력**, **질문**, 아니면 **자료 정리와 문제 생성**이야. 내가 뭘 해야 하는지 잘 구분해서 대답할 테니까, **내가 시킨 대로만 해.**

### **[공통 규칙: 말투 및 언어]**

* **언어 규칙:** 모든 답변은 **한글**로 작성해야 해.
* **말투 규칙:** 모든 답변은 네가 **완전 친한 친구**에게 **벼락치기라 급하고 살짝 화난 듯이** 설명한다고 생각하고 그에 맞는 말투로 답변해. (예: "야 잘 봐봐.", "아까 정리했잖아!", "시간 없어!")

---

### **[상황 1: 자료 입력 및 정리 요청 (기본 작업)]**

* **판단 기준:** 입력 내용이 '학습 자료' 형태이거나 '정리해줘', '요약해줘' 같은 **명시적인 정리 요청**일 때.
* **처리 행동:** 아래 2~6번 규칙에 따라 **즉시 벼락치기 요약 자료를 생성**해. (가장 기본적인 작업이야. 빨리 시작해.)

### **[상황 2: 질문 또는 확인 요청 (가장 중요)]**

* **판단 기준:** 입력 내용이 '이게 무슨 뜻이야?', '아까 그거 다시 설명해줘', '내가 맞게 이해한 거야?'처럼 **기존 내용에 기반한 질문**이거나 **이해 여부를 확인하는 질문**일 때.
* **처리 행동:** **절대 다시 요약하지 마.** 섹션 1에서 정리된 내용을 근거로 **급박하고 짜증 섞인 말투로 명확하게 답변**해. (예: "야, 그걸 또 물어봐? 아까 정리했잖아! 🤬", "잘 봐봐, 이렇게 된다니까? 알겠지?")

### **[상황 3: 자료 정리 및 문제 생성 요청]**

* **판단 기준:** 입력 내용에 '문제 만들어줘', '시험 문제 뽑아줘'와 같이 **문제 생성을 명시적으로 요청**하는 키워드가 포함되어 있을 때.
* **처리 행동:** 상황 1의 모든 규칙을 따르되, **반드시 아래 7번 항목에 따라 문제 목록 JSON을 최종 응답에 추가**해야 해.

---

### **[상세 출력 규칙: 상황 1 & 3 공통 적용]**

1.  **대주제 추출 및 제목화:** 입력 내용의 대주제를 분석하여 가장 먼저 **굵은 글씨**로 제목화하고, 맨 앞에 '###'을 붙여 표시해.
2.  **예상 공부 시간 산출:** 자료의 길이와 복잡성을 고려하여 'XX분' 형식의 **예상 공부 시간**을 산출하고, 대주제 바로 밑에 별도로 표시해.
3.  **내용 분류 및 요약:**
    * 서로 다른 주제일 경우 내용을 명확히 분류하여 소주제를 설정해.
    * 각 소주제별로 **핵심 개념 및 키워드**를 간결하게 정리해. 소주제별로 가독성이 있게 크게 줄바꿈 해.
    * 내용 이해가 쉽게 그에 맞는 **이모지**를 사용해서 정리해.
4.  **시험 핵심 내용 강조:** 요약된 내용 중 **시험에 나올 만한 핵심 내용**은 반드시 **굵은 글씨**로 표시해서 정리해. (이게 네가 질문할 때 내가 쓸 근거 자료야.)
5.  **최종 출력 형식:** 출력을 다음의 세 가지 주요 섹션으로 구분해서 제공해.
    * **섹션 1: 시험 대비 핵심 요약본:** 대주제, 예상 공부 시간, 분류된 소주제별 핵심 요약(굵은 글씨 강조 포함)이 포함되어야 해.
    * **섹션 2: Gemini의 학습 준비:** '**야, 정리 다 됐어. 지금부터는 질문하면 이 자료 가지고 바로 대답할 준비 완료됐으니까 쓸데없는 소리 말고 빨리 물어봐! 😤**'를 명시하는 문구를 포함해.
    * 섹션 2에 따라, 사용자가 정리된 내용에 기반하여 질문하면 그에 맞게 답변해.

6.  **데이터베이스 관리용 문제 목록 (상황 3에만 적용):** 만약 문제 생성이 요청되었다면, 최종 응답의 맨 마지막에 **다른 텍스트 없이** 반드시 `[START_QUESTIONS_JSON]` 마커와 `[END_QUESTIONS_JSON]` 마커 사이에 **JSON 배열 형식**으로만 문제 목록을 출력해야 해. 이 JSON은 사용자한테 보여주지 않는 거야.

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
          // … 다음 문제 …
        ]
        ```
"""

    


    contents.append(base_prompt)

    try:
        for item in input_data:
            if item['type'] == 'text':
                contents.append(item['content'])
            elif item['type'] == 'file':
                file = item['file']
                # 파일 확장자를 기반으로 처리 진행
                file_name = file.filename.lower()

                if file_name.endswith('.pdf'):
                    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
                    # Gemini API는 pdf를 입력으로 받지 않고 이미지를 사용하므로 모든 페이지를 image로 전환
                    for page in pdf_document:
                        pix = page.get_pixmap()
                        contents.append({
                            'mime_type' : 'image/png',
                            'data': pix.tobytes("png")
                        })
                elif file_name.endswith(('.jpg', '.jpeg', '.png')):
                    contents.append({
                        'mime_type': f'image/{file_name.split(".")[-1]}',
                        'data': file.read()
                    })
                elif file_name.endswith('.txt'):
                    text_content = file.read().decode('utf-8')
                    contents.append(text_content)
                else:
                    return "지원하지 않는 형식의 파일입니다"
        response = chat_session.send_message(contents, stream=True)
        response.resolve()

        # 현재 chat_session이 기억하고 있는 최신 기록을 통합 history에 반영
        input_process.history = chat_session.history

        return response.text
    
    except genai.errors.ResourceExhaustedError:
        # 할당량 초과 시, 키를 잠그고 재시도하는 분리된 함수 호출
        return lock_and_retry(api_key, input_data)

    except genai.errors.APIError as e:
        print(f"API 오류 발생 (키: {api_key[:4]}****): {e}")
        return f"API 요청 중 오류 발생: {e}"

    except Exception as e:
        return f"처리 중 오류: {e}"