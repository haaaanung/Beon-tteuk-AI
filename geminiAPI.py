from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="입력 받은 자료에서 가장 중요한 개념 및 키워드를 요약해줘. 시험에 나올 만한 핵심 내용은 굵은 글씨로 표시해서 정리해줘. 이 내용을 토대로 나중에 사용자가 질문하면 답해줘."
)
print(response.text)