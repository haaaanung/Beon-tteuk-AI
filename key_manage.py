import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# datetime, timedelta 설명

# datetime(년, 월, 일, 시간, 분, 초)
# datetime(2025,10,1,10,30) >> 2025년 10월 1일 10시 30분
# datetime.now() > 현재 시점

# timedelta(days=일수, hours=시간, minutes=분)
# timedelta(hours = 24) >> 24시간 간격
# timedelta(days = 7) >> 7일 간격

# API 요청 초기화 시간에 따른 조절 필요
# datetime.now() + timedelta(hours = 24) >> 현재 시간으로부터 24시간 후의 시점

load_dotenv()

# env 파일에 API Key들이 구분자 ','를 사용하여 나열되어 있어야 함
api_keys = [key.strip() for key in os.getenv("api_key", "").split(',') if key.strip()]

if not api_keys:
    # 이 오류는 geminiAPI.py가 아닌 key_manager.py 로드 시 발생해야 함
    raise ValueError("환경 변수 api_key에 API 키가 설정되어 있지 않습니다.")

# 키의 초기값, 잠겨있지 않음
key_status = {key: datetime(1970, 1, 1) for key in api_keys}

current_key_index = 0

# key별 대화 세션 저장을 위한 딕셔너리, geminiAPI.py와 공유
chat_session = {}



# 일일 요청 제한을 효율적으로 관리하기 위한 함수
def get_next_available_key(max_attemps: int) -> str | None:
    global current_key_index
    num_of_keys = len(api_keys)

    for _ in range(max_attemps):
        key = api_keys[current_key_index]
        unlock_time = key_status[key]

        if unlock_time <= datetime.now(): # 키 잠기지 않은 상태, 동일한 키 사용
            return key
        else: # 키 잠김 상태
            # 인덱스를 다음 키로 이동
            remaining_time = unlock_time - datetime.now()
            print(f"키 잠김: {key[:4]}****. {remaining_time.seconds // 3600}시간 남음. 다음 api 키로 전환.")
            
            # 다음 키로 인덱스 강제 이동
            current_key_index = (current_key_index + 1) % num_of_keys
    
    return None



# 아래 get_next_available_key 함수는 Round-Robin 적용, 요청마다 api 키를 바꿈
# 장점: 분당 요청 / 토큰 수 제한에 유리함
# 단점: 일일 요청 제한이 거의 동시에 걸리게 되어 요청량이 적을 것으로 예상되는 경우에만 효과적임
# 필요시 사용

# def get_next_available_key(max_attemps: int) -> str | None:
#     # 성공적으로 키를 찾으면 문자열(str, API 키)을 반환, 잠겨있으면 None 반환
#     global currnet_key_index # 함수 외부에서 선언한 변수를 끌어다 쓰기 위해
#     num_of_keys = len(api_keys) # 전체 api 키 개수

#     for _ in range(max_attemps):
#         key = api_keys[currnet_key_index] # 현재 사용해야 할 순서에 해당하는 API 키 선택
#         unlock_time = key_status[key] # 현재 선택된 key의 잠금 해제 시간

#         if unlock_time <= datetime.now(): # True, 초기상태 혹은 잠금이 풀린 상태, 사용 가능
#             currnet_key_index = (currnet_key_index + 1) % num_of_keys
#             return key
#         else:
#             remaining_time = unlock_time - datetime.now() # 잠금 해제까지 남은 시간
#             print(f"키 잠김: {key[:4]}****. {remaining_time.seconds // 3600}시간 남음. 다음 키 시도.")
#             currnet_key_index = (currnet_key_index + 1) % num_of_keys
    
#     return None



# 특정 키를 24시간동안 잠금 처리하는 함수
def lock_key(key: str):
    unlock_time = datetime.now() + timedelta(hours = 24)
    key_status[key] = unlock_time
    print(f"키 할당량 초과, {key[:4]}**** 키를 24시간 동안 잠금 처리합니다. 해제 시간: {unlock_time.strftime('%Y-%m-%d %H:%M:%S')}")



# 키가 모두 잠겼을 때 사용되는 함수
# 가장 빨리 풀리는 키를 출력하는 기능
def get_soonest_unlock_time() -> datetime | None:
    # 현재 시간보다 미래인 잠금 해제 시간만 필터링
    locked_times = [
        unlock_time for unlock_time in key_status.values() 
        if unlock_time > datetime.now()
    ]
    
    if locked_times:
        # 필터링된 시간 중 가장 빠른 시간 반환
        return min(locked_times)
    else:
        # 잠긴 키가 하나도 없으면 None 반환
        return None
    

# 개별 키 잠금 시간 초기화 함수
def reset_key(key: str):
    key_status[key] = datetime(1970, 1, 1)
    print(f"키 초기화: {key[:4]}**** 키의 잠금 상태를 해제했습니다.")


# 모든 키, 인덱스 초기 상태로 되돌리는 함수 (테스트 용도)
def reset_all_keys():
    global current_key_index
    for key in api_keys:
        key_status[key] = datetime(1970, 1, 1)
    
    current_key_index = 0 
    print("모든 API 키의 잠금 상태와 인덱스를 초기화했습니다.")