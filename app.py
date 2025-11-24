from flask import Flask, request, jsonify
from flask_cors import CORS
import geminiAPI  # 네가 작성한 파이썬 파일 이름 (확장자 제외)

app = Flask(__name__)
CORS(app)  # 리액트에서 요청 보낼 수 있게 허용

@app.route('/api/add-subject', methods=['POST'])
def add_subject():
    try:
        # 1. 리액트에서 보낸 데이터 받기
        name = request.form.get('name')
        importance = request.form.get('importance')
        exam_date = request.form.get('date')
        description = request.form.get('description')
        uploaded_file = request.files.get('file') # 파일 객체

        # 2. Gemini에게 넘길 Context 구성 (exam_init 모드)
        context_data = {
            'mode': 'exam_init',
            'exam_name': name,
            'importance': int(importance),
            'exam_date': exam_date,
            'description': description,
            'exam_id': 'TEMP_ID', # DB 저장 전이라 임시 ID 부여
        }

        # 3. Gemini에게 넘길 Input Data 구성
        input_data = []
        
        # 설명 텍스트 추가
        if description:
            input_data.append({'type': 'text', 'content': f"과목 설명: {description}"})
            
        # 파일이 있다면 추가 (네 코드에서 file객체를 바로 읽을 수 있게 처리됨)
        if uploaded_file:
            input_data.append({'type': 'file', 'file': uploaded_file})

        # 4. 네가 만든 AI 로직 호출
        # 주의: 네 코드의 input_process가 (input_data, context_data)를 받도록 되어 있어야 해.
        ai_response = geminiAPI.input_process(input_data, context_data)

        # 5. 결과 반환
        return jsonify({
            "status": "success",
            "data": ai_response
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)