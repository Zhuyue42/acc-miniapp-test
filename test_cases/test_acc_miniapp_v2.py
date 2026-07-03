import pytest
import requests
from typing import Dict, Any
from common.Logger import logger

BASE_URL = "http://27.115.67.203:20004/"
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoxMjY2ODEwMzg1NjY0OTgzMDQwLCJ1c2VyX2tleSI6Ijg2ZTcwZmFlLTk4NTEtNDlkNC04MzlmLTg4NWE1ZTdmMjU4YSIsInVzZXJuYW1lIjoidyrmgKEifQ.ewIugNAVj3QNAIf3G4UpmemgSjtvwPJb6zE7iL0ZM7zdn9FnWe0lvUoONUUvwkmCV_eV59gqBMpEwpE48TzN1g"
CHANNEL_ID = "qos_test"

APIS_DIC = {
    'member_info': "api/app/user/v3/getMemberInfo",
    'check_qualification': "/api/app/activity/checkQualification",
    'claim_trial': "/api/app/activity/applyForPlay"
}

ACTIVITIES = {
    '云游戏': 'game',
    '云加速': 'speed'
}

# ==================== 工具函数 ====================
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

def extract_common_fields(responses: dict[str, Any]) -> Dict[str, str]:
    """从多个响应中提取公共关键字段"""
    return {
        'user_id': responses['member_info_json'].get('data', {}).get('userId'),
        'membership_level': responses['member_info_json'].get('data', {}).get('userLevel'),
        'membership_name': responses['member_info_json'].get('data', {}).get('userLevelName'),
        'has_eligibility': responses['equalification_json'].get('code') == 200
    }

# ==================== 测试类组织 ====================
class TestParallelENdPoints:

    @pytest.fixture(scope='function')
    def api_responses(self, session):
        try:
            member_info_resp = session.get(f"{BASE_URL}{APIS_DIC['member_info']}", timeout=5)
        except requests.exceptions.RequestException as e:
            logger.error(f"获取会员信息接口请求失败或超时：{e}")
            pytest.fail(f"获取会员信息接口请求失败或超时：{e}")

        try:
            check_qualification_resp = session.get(
            f"{BASE_URL}{APIS_DIC['check_qualification']}",
            params={'activityType': ACTIVITIES['speed']},
            timeout=5
        )
        except requests.exceptions.RequestException as e:
            logger.error(f"校验活动资格接口请求失败或超时：{e}")
            pytest.fail(f"校验活动资格接口请求失败或超时：{e}")
        
        responses_dic = {
            'member_info_json':member_info_resp.json(),
            'qualification_json':check_qualification_resp.json(),
            'member_info_raw':member_info_resp,
            'check_qualification_raw':check_qualification_resp
        }

        logger.info(f"已获取接口响应: {responses_dic}")
        return responses_dic
    
    # ========== 校验会员信息接口 ==========
    def test_endpoint_member_info_structure(self, api_responses):
        """测试会员信息接口的基本结构和必填字段"""
        member_info_data = api_responses['member_info_json']
        
        # HTTP 层校验
        logger.info(f"会员信息接口响应: {api_responses['member_info_raw']}")
        assert api_responses['member_info_raw'].status_code == 200, \
            f"会员信息接口状态码异常：{member_info_data.status_code}"
        
        
        # 业务层校验
        assert member_info_data.get('code') == 200, \
            f"会员信息接口业务异常: {member_info_data.get('msg')}"
        
        # 必填字段校验
        assert 'data' in member_info_data, "会员信息接口响应缺少 data 字段"
        required_fields = ['userId', 'userLevel', 'userLevelName']
        member_info_missing_field = [f for f in required_fields if f not in member_info_data['data']]
        assert not member_info_missing_field, f"会员信息data 中缺失必填字段: {member_info_missing_field}"
        
        # 类型校验
        assert isinstance(member_info_data['data']['userLevel'], int), \
            "userLevel 应为整数类型"
        # 允许的等级范围（根据你们的业务规则调整）
        VALID_LEVELS = {0, 1, 2, 3, 5, 6}  # 示例：0=游客, 1=月卡, 2=季卡, 等
        assert member_info_data['data']['userLevel'] in VALID_LEVELS, \
            f"无效的会员等级: {member_info_data['data']['userLevel']}. 请确认业务规则."
        assert isinstance(member_info_data['data']['userId'], (int, str)), \
            "userId 应为数字或字符串"
        
    # ========== 平行线的右侧：活动资格接口 ==========
    def test_endpoint_eligibility_per_activity(self, api_responses):
        """针对每种活动类型分别测试资格查询"""
        # HTTP 层校验
        assert api_responses['check_qualification_raw'].status_code == 200, \
            f"校验会员资格接口状态码异常：{api_responses['check_qualification_raw'].status_code}"
        
        qualification_data = api_responses['qualification_json']

        # 成功场景
        if qualification_data.get('code') == 200:
            assert 'data' in qualification_data
            activity_data = qualification_data['data']
            assert 'activityId' in activity_data, "业务状态码成功但未返回活动Id"
            print(f"可领取的活动ID: {activity_data['activityId']}")
        
        else:
            pytest.fail(
                f"业务状态码与业务消息 {qualification_data.get('code')}: {qualification_data.get('msg')}\n"
                f"完整响应: {qualification_data}"
            )


    # ========== 端到端场景 ==========
    def test_end_to_end_successful_claim(self, session):
        """
        E2E: 一个完整的成功领取流程
        只有在前置条件完美满足时才会全部通过
        """
        logger.info("\n🎬 已校验用户会员等级与活动资格，进行端到端测试...")
        
        # ① 快速探针：确认是否满足前提
        probe_member_info_resp = session.get(f"{BASE_URL}{APIS_DIC['member_info']}")
        if probe_member_info_resp.json()['data']['userLevel'] != 0:
            pytest.skip("当前测试账号已是会员，无体验资格")
        
        # ② 主干流程
        # -- 查询资格 --
        elig_resp = session.get(
            f"{BASE_URL}{APIS_DIC['check_qualification']}",
            params={'activityType': ACTIVITIES['云加速']}
        )
        elig_data = elig_resp.json()
        
        if elig_data.get('code') != 200:
            pytest.skip(f"无可参加的活动: {elig_data.get('msg')}")
        
        activity_id = elig_data['data']['activityId']
        logger.info(f"   获得资格: 活动#{activity_id}")
        
        # -- 执行领取 --
        claim_resp = session.post(
            f"{BASE_URL}{APIS_DIC['claim_trial']}",
            json={'activityId': activity_id},
            timeout=5
        )
        claim_data = claim_resp.json()
        
        logger.info(f"   领取结果: {claim_data.get('msg')}")
        assert claim_resp.status_code == 200
        assert claim_data.get('code') == 200
        
        # -- 回访验证 --
        verify_resp = session.get(f"{BASE_URL}{APIS_DIC['member_info']}")
        new_level = verify_resp.json()['data']['userLevel']
        assert new_level > 0, "领取后会员等级应上升"
        logger.info(f"领取会员成功: Lv{new_level}")
