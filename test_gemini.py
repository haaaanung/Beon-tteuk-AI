import os
from geminiAPI import input_process
from io import BytesIO

def create_dummy_file(filename, content=None, file_type='text'):
    """테스트를 위한 가상의 파일을 생성하는 헬퍼 함수입니다."""
    file = BytesIO()
    if file_type == 'text':
        file.write(content.encode('utf-8'))
    elif file_type == 'image':
        # 실제 이미지 데이터가 필요할 경우 여기에 추가
        pass
    file.seek(0)
    file.filename = filename
    return file

print("--- Gemini API 로컬 테스트 시작 ---")

# 1. 텍스트 입력 테스트
print("\n[1] 텍스트 입력 테스트 중...")
text_input = "오늘 날씨는 맑음."
test_data = [{'type': 'text', 'content': text_input}]
result = input_process(test_data)
print(f"결과: {result}")

# 2. 이미지 파일 테스트 (더미 파일)
print("\n[2] 이미지 파일 입력 테스트 중...")
# 실제 이미지 파일 경로로 변경하여 테스트하세요.
try:
    with open("example.png", "rb") as f:
        image_file = BytesIO(f.read())
        image_file.filename = "example.png"
    
    test_data = [{'type': 'file', 'file': image_file}]
    result = input_process(test_data)
    print(f"결과: {result}")
except FileNotFoundError:
    print("오류: example.png 파일을 찾을 수 없습니다. 테스트를 위해 실제 이미지 파일이 필요합니다.")
    print("테스트를 위해 example.png 파일을 생성하거나 경로를 수정해주세요.")

# 3. PDF 파일 테스트 (더미 파일)
print("\n[3] PDF 파일 입력 테스트 중...")
# 실제 PDF 파일 경로로 변경하여 테스트하세요.
try:
    with open("example.pdf", "rb") as f:
        pdf_file = BytesIO(f.read())
        pdf_file.filename = "example.pdf"
    
    test_data = [{'type': 'file', 'file': pdf_file}]
    result = input_process(test_data)
    print(f"결과: {result}")
except FileNotFoundError:
    print("오류: example.pdf 파일을 찾을 수 없습니다. 테스트를 위해 실제 PDF 파일이 필요합니다.")
    print("테스트를 위해 example.pdf 파일을 생성하거나 경로를 수정해주세요.")

print("\n--- 테스트 완료 ---")