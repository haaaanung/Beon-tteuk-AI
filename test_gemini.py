import os
import sys
from geminiAPI import input_process
from io import BytesIO

# --- 헬퍼 함수 ---
def create_file_from_path(file_path):
    """실제 파일 경로를 기반으로 파일 객체를 생성합니다."""
    if not os.path.exists(file_path):
        return None
  
    with open(file_path, 'rb') as f:
        file_content = BytesIO(f.read())
        file_content.filename = os.path.basename(file_path)
        return file_content

def main():
    print("--- Gemini API CLI 테스트 ---")
    print("1. 텍스트 입력")
    print("2. 파일 입력 (경로 입력)")
    print("3. 종료")

    while True:
        choice = input("입력 방식을 선택하세요 (1, 2, 3): ")

        if choice == '1':
            text_input = input("텍스트를 입력하세요: ")
            input_data = [{'type': 'text', 'content': text_input}]
            result = input_process(input_data)
            print("--- 결과 ---")
            print(result)
            print("------------\n")

        elif choice == '2':
            file_path = input("파일 경로를 입력하세요 (예: my_image.jpg): ")
            file_object = create_file_from_path(file_path)
            
            if file_object:
                input_data = [{'type': 'file', 'file': file_object}]
                result = input_process(input_data)
                print("--- 결과 ---")
                print(result)
                print("------------\n")
            else:
                print("오류: 파일을 찾을 수 없거나 올바른 파일 경로가 아닙니다.\n")
        
        elif choice == '3':
            print("테스트를 종료합니다.")
            sys.exit()

        else:
            print("잘못된 입력입니다. 1, 2, 3 중 하나를 입력하세요.\n")

if __name__ == "__main__":
    main()
'''
eof

### 사용 방법

1.  **`gemini_api.py`와 `test_gemini.py`가 같은 폴더에 있는지 확인**합니다.
2.  **터미널에서 `test_gemini.py`를 실행**합니다.
    ```bash
    python test_gemini.py
'''