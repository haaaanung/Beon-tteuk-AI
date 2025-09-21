import google.generativeai as genai
from dotenv import load_dotenv
import fitz
import os

load_dotenv()
try:
    api_key = os.getenv('api_key')
    if not api_key:
        raise ValueError("API 키 누락!!")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"오류:{e}")
    exit()

def input_process(input_data):
    """
    text, image, pdf 등 다양한 유형의 입력을 받아 Gemini API에 전달하여 처리하는 함수.
    
    Args: input_data

    Returns: Gemini API의 응답 텍스트(혹은 오류)
    """
    contents = []
    base_prompt = "입력 받은 자료에서 중요한 개념 및 키워드를 요약해줘. " \
    "시험에 나올 만한 핵심 내용은 **굵은 글씨**로 표시해서 정리해줘." \
    "이 내용을 토대로 나중에 사용자가 질문하면 답해줘."


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
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(contents, stream=True)
        response.resolve()

        return response.text
    except Exception as e:
        return f"처리 중 오류: {e}"