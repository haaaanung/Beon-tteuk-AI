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
    base_prompt = "입력 받은 자료에서 중요한 개념 및 키워드를 요약해줘. " \
    "시험에 나올 만한 핵심 내용은 **굵은 글씨**로 표시해서 정리해줘." \
    "이 내용을 토대로 나중에 사용자가 질문하면 답해줘." \
    "서로 다른 주제일 경우 분류해줘야해." \
    "내가 영어로 대답해달라고 요청하는 경우를 제외하고 절대 영어로 답변하지 말아줘"


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