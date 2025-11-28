from flask import Flask, request, jsonify
from flask_cors import CORS
import geminiAPI  # 작성한 AI 로직 파일 (geminiAPI.py)

app = Flask(__name__)
CORS(app)  # 리액트 등 외부 요청 허용

# ---------------------------------------------------------
# 1. 과목 추가 (초기 분석)
# ---------------------------------------------------------
@app.route('/api/ai/add-subject', methods=['POST'])
def add_subject():
    try:
        # 1. 리액트(FormData)에서 데이터 받기
        name = request.form.get('name')
        importance = request.form.get('importance')
        exam_date = request.form.get('date')
        description = request.form.get('description')
        uploaded_file = request.files.get('file') # 파일 객체

        # 2. Gemini Context (exam_init 모드)
        context_data = {
            'mode': 'exam_init',
            'exam_name': name,
            'importance': int(importance) if importance else 3,
            'exam_date': exam_date,
            'description': description,
            'exam_id': 'TEMP_ID', 
            # 만약 기존에 분석된 태그가 있다면 프론트에서 넘겨받아 여기에 넣어야 함
            'tag_name': request.form.get('tag_name', '') 
        }

        # 3. Input Data 구성
        input_data = []
        
        if description:
            input_data.append({'type': 'text', 'content': f"사용자 메모: {description}"})
            
        if uploaded_file:
            # 파일 포인터를 처음으로 되돌림 (혹시 모를 오류 방지)
            uploaded_file.seek(0)
            input_data.append({'type': 'file', 'file': uploaded_file})

        # 4. AI 호출
        ai_response = geminiAPI.input_process(input_data, context_data)

        return jsonify({
            "status": "success",
            "data": ai_response
        })

    except Exception as e:
        print(f"Error in add_subject: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------
# 2. 문제 생성 요청 (NEW)
# ---------------------------------------------------------
@app.route('/api/ai/generate-questions', methods=['POST'])
def generate_questions():
    try:
        # 1. 리액트(JSON)에서 데이터 받기
        # 파일 업로드가 없으므로 JSON으로 받음
        data = request.get_json()
        
        tag_name = data.get('tag_name')       # 필수: 공통 태그명 (예: OS_SCHEDULING)
        user_id = data.get('user_id', 'Guest')

        if not tag_name:
            return jsonify({"status": "error", "message": "tag_name is required"}), 400

        # 2. Gemini Context (Study 모드)
        # 중요: mode를 'study'로 해야 get_base_prompt의 [상황 3]이 발동됨
        context_data = {
            'mode': 'study',
            'user_id': user_id,
            'related_tagname': tag_name, # 프롬프트의 {related_tagname}에 매핑됨
            'task_id': 'GEN_Q_TASK'
        }   

        # 3. AI에게 보낼 '트리거 메시지' 구성
        # 프롬프트의 [상황 3] 판단 기준을 만족시키는 문구를 시스템이 대신 입력해줌
        system_trigger_msg = f"""
        [시스템 명령]
        - 타겟 태그: {tag_name}
        
        위 내용을 바탕으로 문제 10개를 생성하라.
        반드시 [상황 3] 규칙을 따르고, JSON 포맷을 엄격히 준수하여 출력하라.
        """

        input_data = [
            {'type': 'text', 'content': system_trigger_msg}
        ]

        # 4. AI 호출
        ai_response = geminiAPI.input_process(input_data, context_data)

        # 5. [핵심] JSON 블록만 깔끔하게 잘라내기 (Cleaning)
        clean_response = ai_response # 기본값은 전체
        start_marker = "[START_QUESTIONS_JSON]"
        end_marker = "[END_QUESTIONS_JSON]"
        
        s_idx = ai_response.find(start_marker)
        e_idx = ai_response.find(end_marker)
        
        if s_idx != -1 and e_idx != -1:
            # 마커를 포함한 구간만 정확히 추출 (끝 마커 길이까지 포함)
            clean_response = ai_response[s_idx : e_idx + len(end_marker)]
            print(f"[DEBUG] Cleaned JSON Block extracted successfully.")
        else:
            print(f"[WARN] JSON markers not found. Returning full text.")
        print(clean_response)
        # 5. 결과 반환
        return jsonify({
            "status": "success",
            "data": clean_response
        })

    except Exception as e:
        print(f"Error in generate_questions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)

