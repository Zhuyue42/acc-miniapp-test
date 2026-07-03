import pytest
import requests

#基础配置
BASE_URL = "http://27.115.67.203:20004/"
GET_MEMBER_INFO_API = "api/app/user/v3/getMemberInfo"
CHECK_QUALIFICATION_API = "/api/app/activity/checkQualification"
CLAIM_TRAIL_API = "/api/app/activity/applyForPlay"
ACTIVITY_ID_POST_PARAMS = {'activityId':''}
CHECK_QUALIFICATION_PARAMS = ['game','speed']
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoxMjY2ODEwMzg1NjY0OTgzMDQwLCJ1c2VyX2tleSI6Ijg2ZTcwZmFlLTk4NTEtNDlkNC04MzlmLTg4NWE1ZTdmMjU4YSIsInVzZXJuYW1lIjoidyrmgKEifQ.ewIugNAVj3QNAIf3G4UpmemgSjtvwPJb6zE7iL0ZM7zdn9FnWe0lvUoONUUvwkmCV_eV59gqBMpEwpE48TzN1g"
CHANNEL_ID = "qos_test"

@pytest.fixture(scope="session")
def session():
    #创建一个带有统一请求头的会话
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "channelid": CHANNEL_ID,
        "Content-Type":"application/json;charset=utf-8"
    })
    return session

def test_interface_flow(session):
    '''
    1. 获取用户会员信息
    '''
    get_member_info_url = f"{BASE_URL}{GET_MEMBER_INFO_API}"
    try:
        get_member_info_response = session.get(get_member_info_url,timeout=5)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"会员信息接口请求失败或超时：{e}")
    #边界与异常校验
    assert get_member_info_response.status_code == 200, f"会员接口状态码异常：{get_member_info_response.status_code}"
    member_info_data = get_member_info_response.json()
    print(member_info_data)
    assert member_info_data.get('code') == 200,"会员接口业务状态码错误"
    assert 'data' in member_info_data,"会员信息查询接口未返回data字段"
    #获取会员等级，0即非会员，可以获取资格
    user_id = member_info_data['data']['userId']
    user_level  = member_info_data['data']['userLevel']
    user_name = member_info_data['data']['userName']
    print(f"\n 当前用户: {user_id}, 会员等级: Lv{user_level}，会员名称：{user_name}")
    #assert userLevel == 0,f"用户无活动资格,当前会员等级：{userLevel},会员名称：{userName}"
    #待优化：1.没有活动资格，请求活动资格接口的响应。2.有活动资格，第一次和后续请求活动接口的响应
    if user_level == 0:
        print("用户当前非会员，进入下一步校验")

    '''
    2. 校验活动参与资格（用户token校验）
    '''
    check_qualification_url = f"{BASE_URL}{CHECK_QUALIFICATION_API}"
    try:
        check_qualification_response = session.get(check_qualification_url,params=CHECK_QUALIFICATION_PARAMS[1],timeout=5)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"校验活动资格接口请求超时：{e}")

    #边界与异常校验
    assert check_qualification_response.status_code == 200, f"校验活动资格接口状态码异常：{check_qualification_response.status_code}"
    check_qualification_data = check_qualification_response.json()
    assert check_qualification_data.get('code') == 200, f"用户无试用领取资格：{check_qualification_data.get('msg')}"
    assert 'data' in check_qualification_data, "未获取到用户可参与活动"

    #用户有资格进行下一步
    '''
    3.领取试用资格
    '''
    activity_id = check_qualification_data['data']['activityId']
    ACTIVITY_ID_POST_PARAMS.update({
        'activityId':activity_id
    })
    claim_url = f"{BASE_URL}{CLAIM_TRAIL_API}"
    try:
        claim_trail_response = session.post(claim_url,params=ACTIVITY_ID_POST_PARAMS,timeout=5)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"领取试用云加速试用资格接口超时：{e}")
    claim_trail_data = claim_trail_response.json()
    print(claim_trail_data)    






# if __name__ == '__main__':
#     get_member_info_url = f"{BASE_URL}{GET_MEMBER_INFO_API}"
#     print(get_member_info_url)