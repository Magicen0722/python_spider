import scrapy
import traceback
import json
import re
from datetime import datetime
from scrapy import Request
from ..items import FranchiseProjectItem, FranchiseAttachmentItem


class FranchiseSpider(scrapy.Spider):
    name = 'franchise_spider'
    allowed_domains = ['tzxm.gov.cn']

    # API接口
    base_url = 'https://www.tzxm.gov.cn:8081/aweb-ui/#/ppp/project-publicity/project-publicity-list'
    list_api = 'https://www.tzxm.gov.cn:8081/aweb/api/v1/pi/getPublicInfoList1'
    detail_api = 'https://www.tzxm.gov.cn:8081/aweb/api/v1/common/getPublicProjectDetailById/{}'
    download_api = 'https://www.tzxm.gov.cn:8081/aweb/api/v1/file/downloadById'

    # 请求头
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.tzxm.gov.cn:8081',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'X-Auth-Token': 'null'
    }

    def __init__(self, *args, **kwargs):
        super(FranchiseSpider, self).__init__(*args, **kwargs)
        # 初始化参数
        self.incremental = kwargs.get('incremental', True)
        self.last_update_time = kwargs.get('last_update_time', None)
        self.download_attachments = kwargs.get('download_attachments', False)
        self.cookies = {}

    def start_requests(self):
        # 首先访问主页获取cookies
        yield scrapy.Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.get_cookies,
            meta={'use_flaresolverr': True}
        )

    def get_cookies(self, response):
        """获取cookies后开始正式抓取"""
        # 从response中提取cookies
        if hasattr(response, 'cookies'):
            self.cookies = response.cookies
            self.logger.info(f"获取到cookies: {self.cookies}")

        # 构建请求体
        body = {
            "pageSize": 100,  # 每页100条，减少请求次数
            "pageNum": 1,
            "projectCode": "",
            "projectName": "",
            "apprOrgno": "",
            "execMode": "",
            "theIndustry": "",
            "planTotalMoneyStart": "",
            "planTotalMoneyEnd": ""
        }

        # 更新headers，添加cookies
        headers = self.headers.copy()
        if self.cookies:
            cookie_str = '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
            headers['Cookie'] = cookie_str

        yield scrapy.Request(
            url=self.list_api,
            method='POST',
            headers=headers,
            body=json.dumps(body),
            callback=self.parse_list,
            meta={'page_num': 1}
        )

    def parse_list(self, response):
        """解析列表页"""
        try:
            data = json.loads(response.text)
            if data['code'] == 'SYS.200':
                result = data['data']
                projects = result.get('list', [])

                # 处理每个项目
                for project in projects:
                    # 增量抓取逻辑：检查更新时间
                    if self.incremental and self.last_update_time:
                        operate_time = project.get('operateTime', '')
                        if operate_time and operate_time <= self.last_update_time:
                            continue

                    # 请求详情页
                    project_id = project['id']
                    detail_url = self.detail_api.format(project_id)
                    headers = self.headers.copy()
                    if self.cookies:
                        cookie_str = '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
                        headers['Cookie'] = cookie_str

                    yield scrapy.Request(
                        url=detail_url,
                        headers=headers,
                        callback=self.parse_detail,
                        meta={'list_data': project}
                    )

                # 翻页逻辑
                current_page = result.get('pageNum', 1)
                total_pages = result.get('pages', 1)

                if current_page < total_pages:
                    next_page = current_page + 1
                    body = {
                        "pageSize": 100,
                        "pageNum": next_page,
                        "projectCode": "",
                        "projectName": "",
                        "apprOrgno": "",
                        "execMode": "",
                        "theIndustry": "",
                        "planTotalMoneyStart": "",
                        "planTotalMoneyEnd": ""
                    }
                    headers = self.headers.copy()
                    if self.cookies:
                        cookie_str = '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
                        headers['Cookie'] = cookie_str

                    yield scrapy.Request(
                        url=self.list_api,
                        method='POST',
                        headers=headers,
                        body=json.dumps(body),
                        callback=self.parse_list,
                        meta={'page_num': next_page}
                    )
        except Exception as e:
            self.logger.error(f"解析列表页出错: {e}")

    def parse_detail(self, response):
        """解析详情页"""
        try:
            data = json.loads(response.text)
            if data['code'] == 'SYS.200':
                detail_data = data['data']
                list_data = response.meta['list_data']

                # 创建Item对象
                item = FranchiseProjectItem()

                # 基本信息（来自列表页）
                item['project_id'] = list_data.get('id', '')
                item['project_code'] = list_data.get('projectCode', '')
                item['project_name'] = list_data.get('projectName', '')

                # 地区信息解析 - 支持多级地区
                area_info = self.parse_area_info(list_data)
                item.update(area_info)

                # 项目分类信息
                item['project_level'] = list_data.get('projectLevel', '')
                item['project_level_name'] = self.get_code_name('PROJECT_LEVEL', list_data.get('projectLevel', ''))
                item['industry_code'] = list_data.get('theIndustry', '')
                item['industry_name'] = list_data.get('theIndustryName', '')
                item['project_type'] = list_data.get('projectType', '')
                item['project_type_name'] = list_data.get('projectTypeName', '')

                # 实施模式
                item['exec_mode'] = list_data.get('execMode', '')
                item['exec_mode_name'] = list_data.get('execModeName', '')

                # 投资信息 - 转换为数值类型
                item['total_investment'] = self.safe_decimal(list_data.get('planTotalMoney', 0))
                item['construction_location'] = self.format_address_list(list_data.get('projectAddressList', []))
                item['scale_content'] = list_data.get('scaleContent', '')

                # 处理详情页数据
                ppp_project_vo = detail_data.get('PaEbPppProjectVo', {})
                if ppp_project_vo:
                    item['expected_private_capital'] = self.safe_decimal(ppp_project_vo.get('expPriCap', 0))
                    item['expected_project_capital'] = self.safe_decimal(
                        ppp_project_vo.get('expectedProjectCapital', 0))

                # 特许经营参数信息
                argument_info = detail_data.get('PaEbArgumentInfoVo', {})
                if argument_info:
                    item['franchise_period'] = self.safe_int(argument_info.get('franDeadline', 0))
                    item['pre_start_date'] = self.parse_date(argument_info.get('preStartDate', ''))
                    item['pre_end_date'] = self.parse_date(argument_info.get('preComplDate', ''))

                    # 政府补贴信息 - 转换为布尔值和数值
                    item['has_gov_subsidy'] = argument_info.get('isGovInvSupport', '0') == '1'
                    item['gov_invest_type'] = self.get_code_name('GOV_INV_TYPE',
                                                                 argument_info.get('invSupportType', ''))
                    item['gov_invest_ratio'] = self.safe_decimal(argument_info.get('preGovInvRatio', 0))
                    item['gov_representative'] = argument_info.get('govInvReferee', '')
                    item['gov_share_ratio'] = self.safe_decimal(argument_info.get('govInvRefereeBonus', 0))
                    item['gov_invest_capital'] = self.safe_decimal(argument_info.get('preGovInvCap', 0))

                    # 运营补贴信息
                    item['has_operation_subsidy'] = argument_info.get('isOperSubsidy', '0') == '1'
                    item['subsidy_source'] = argument_info.get('operSubsidySource', '')
                    item['subsidy_limit'] = self.safe_decimal(argument_info.get('operSubsidyLimit', 0))
                    item['subsidy_mode'] = argument_info.get('operSubsidyMode', '')

                    # 民营企业参与
                    item['private_enterprise_plan'] = argument_info.get('privateEntPlan', '')
                    item['private_share_ratio'] = self.extract_private_ratio(argument_info.get('privateEntPlan', ''))

                # 招投标信息
                invbids = detail_data.get('InvbidsVo', [])
                if invbids:
                    first_bid = invbids[0]
                    item['bidding_method'] = self.get_code_name('BID_TYPE', first_bid.get('bidType', ''))
                    item['bidding_time'] = self.parse_date(first_bid.get('pubBidDate', ''))

                # 中标信息
                winbids = detail_data.get('WinbidsVo', [])
                if winbids:
                    winner_names = []
                    winner_types = []
                    for win in winbids:
                        winner_names.append(win.get('winbidEntname', ''))
                        winner_types.append(self.get_code_name('ENTTYPE', win.get('enttype', '')))
                    item['winner_nature'] = ','.join(winner_types)
                    item['winner_names'] = ','.join(winner_names)

                # 项目阶段
                item['project_stage'] = list_data.get('stageType', '')
                item['project_stage_name'] = self.get_stage_name(list_data.get('stageType', ''))

                # 审批信息
                plan_appr_info = detail_data.get('PaDfPlanapprInfoVo', {})
                if plan_appr_info:
                    item['approval_org_name'] = plan_appr_info.get('apprOrgName', '')
                    item['approval_date'] = self.parse_date(plan_appr_info.get('apprDate', ''))

                # 实施机构信息
                item['implement_org_name'] = list_data.get('enforBodyName', '')
                item['implement_contact'] = list_data.get('enforBodyLinp', '')
                item['implement_phone'] = list_data.get('enBodyTel', '')

                # 咨询机构信息
                item['consult_org_name'] = list_data.get('consOrgName', '')
                item['consult_contact'] = list_data.get('consOrgPri', '')
                item['consult_phone'] = list_data.get('consOrgPriTel', '')

                # 法律机构信息
                item['law_firm_name'] = list_data.get('lawFirmName', '')
                item['law_firm_contact'] = list_data.get('lawFirmPri', '')
                item['law_firm_phone'] = list_data.get('lawFirmPriTel', '')

                # 授权政府
                item['mandate_gov'] = list_data.get('mandateGov', '')

                # 状态信息
                item['is_published'] = list_data.get('isEnable', '1') == '1'
                item['verification_code'] = list_data.get('verificationCode', '')

                # 时间戳
                item['create_time'] = self.parse_datetime(list_data.get('createTime', ''))
                item['update_time'] = self.parse_datetime(list_data.get('operateTime', ''))
                item['crawl_time'] = datetime.now()

                # 先yield项目数据
                yield item

                # 处理附件下载
                if self.download_attachments:
                    yield from self.handle_attachments(list_data, detail_data, item['project_id'])

        except Exception as e:
            error_message = f"解析详情页出错: {e}\n{traceback.format_exc()}"
            self.logger.error(error_message)

    def handle_attachments(self, list_data, detail_data, project_id):
        """处理附件信息"""
        attachments = []

        # 从列表数据收集附件
        if list_data.get('govAuthEbFile'):
            attachments.append({
                'file_id': list_data['govAuthEbFile'],
                'file_type': 'gov_auth',
                'file_name': '政府授权文件',
                'attachment_category': '政府授权',
                'project_id': project_id
            })

        if list_data.get('franPlanFile'):
            attachments.append({
                'file_id': list_data['franPlanFile'],
                'file_type': 'franchise_plan',
                'file_name': '特许经营方案',
                'attachment_category': '特许经营方案',
                'project_id': project_id
            })

        if list_data.get('franPlanFileWord'):
            attachments.append({
                'file_id': list_data['franPlanFileWord'],
                'file_type': 'franchise_plan_word',
                'file_name': '特许经营方案Word版',
                'attachment_category': '特许经营方案',
                'project_id': project_id
            })

        if list_data.get('franPlanFileZip'):
            attachments.append({
                'file_id': list_data['franPlanFileZip'],
                'file_type': 'franchise_plan_zip',
                'file_name': '特许经营方案压缩包',
                'attachment_category': '特许经营方案',
                'project_id': project_id
            })

        # 从详情数据收集附件
        plan_appr_info = detail_data.get('PaDfPlanapprInfoVo', {})
        if plan_appr_info and plan_appr_info.get('apprFile'):
            attachments.append({
                'file_id': plan_appr_info['apprFile'],
                'file_type': 'approval_file',
                'file_name': '审批文件',
                'attachment_category': '审批文件',
                'project_id': project_id
            })

        # 招标文件
        invbids = detail_data.get('InvbidsVo', [])
        for inv in invbids:
            if inv.get('invbidProcFile'):
                attachments.append({
                    'file_id': inv['invbidProcFile'],
                    'file_type': 'bidding_file',
                    'file_name': '招标文件',
                    'attachment_category': '招标文件',
                    'project_id': project_id
                })

        # 中标文件
        winbids = detail_data.get('WinbidsVo', [])
        for win in winbids:
            if win.get('winbidAdviceFile'):
                attachments.append({
                    'file_id': win['winbidAdviceFile'],
                    'file_type': 'winning_file',
                    'file_name': f'中标通知书-{win.get("winbidEntname", "")}',
                    'attachment_category': '中标文件',
                    'project_id': project_id
                })

        # 为每个附件创建附件项
        for attachment in attachments:
            attachment_item = FranchiseAttachmentItem()
            attachment_item['attachment_id'] = attachment['file_id']
            attachment_item['project_id'] = attachment['project_id']
            attachment_item['file_type'] = attachment['file_type']
            attachment_item['file_name'] = attachment['file_name']
            attachment_item['attachment_category'] = attachment['attachment_category']
            attachment_item['download_url'] = f"{self.download_api}?id={attachment['file_id']}&pppId={project_id}"
            attachment_item['is_downloaded'] = False
            attachment_item['download_time'] = datetime.now()
            yield attachment_item

    def parse_area_info(self, list_data):
        """解析地区信息，支持多级地区"""
        area_info = {}

        # 从projectAddressList解析地区代码
        address_list = list_data.get('projectAddressList', [])
        if address_list:
            # 假设地区代码是6位数字，前2位省份，前4位城市，6位区县
            first_area = address_list[0]
            if len(first_area) >= 2:
                province_code = first_area[:2] + '0000'
                area_info['province_code'] = province_code
                area_info['province_name'] = list_data.get('sname1', '')

            if len(first_area) >= 4:
                city_code = first_area[:4] + '00'
                area_info['city_code'] = city_code
                area_info['city_name'] = list_data.get('sname2', '')

            if len(first_area) == 6:
                area_info['county_code'] = first_area
                area_info['county_name'] = list_data.get('sname', '')

        # 审批机关信息
        area_info['area_code'] = list_data.get('apprOrgno', '')
        area_info['area_name'] = list_data.get('projectAddressName', '')

        return area_info

    def format_address_list(self, address_list):
        """格式化地址列表"""
        if not address_list:
            return ''
        # 这里可以根据地区代码转换为地区名称
        return ','.join(address_list)

    def safe_decimal(self, value):
        """安全转换为decimal类型"""
        try:
            if value is None or value == '':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def safe_int(self, value):
        """安全转换为int类型"""
        try:
            if value is None or value == '':
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d', '%Y-%m', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def parse_datetime(self, datetime_str):
        """解析日期时间字符串"""
        if not datetime_str:
            return None
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None

    def extract_private_ratio(self, text):
        """从文本中提取民企持股比例"""
        if not text:
            return 0.0

        # 尝试匹配百分比
        pattern = r'(\d+(?:\.\d+)?)[%％]'
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        return 0.0

    def get_code_name(self, code_type, code_value):
        """根据code_type和code_value获取对应的名称"""
        if not code_value:
            return ''

        code_mapping = {
            "PROJECT_LEVEL": {
                "A00001": "国家级",
                "A00002": "省级",
                "A00003": "市级",
                "A00004": "县级",
                "A00099": "其他"
            },
            "GOV_INV_TYPE": {
                "A00001": "无",
                "A00002": "直接投资",
                "A00003": "资本金注入",
                "A00004": "投资补助",
                "A00005": "贷款贴息"
            },
            "PROJECT_TYPE": {
                "A00001": "新建项目",
                "A00002": "改扩建项目",
                "A00003": "不涉及新建、改扩建的存量项目"
            },
            "ENTTYPE": {
                "A00001": "民营企业",
                "A00002": "外商投资企业",
                "A00003": "中央企业",
                "A00004": "项目所在地省级国有企业",
                "A00005": "项目所在地市级国有企业",
                "A00006": "项目所在地县级国有企业",
                "A00007": "非项目所在地其他国有企业",
                "A00099": "其他"
            },
            "EXEC_MODE": {
                "A00001": "BOT",
                "A00002": "TOT",
                "A00003": "ROT",
                "A00004": "BOOT",
                "A00005": "DBFOT",
                "A00006": "BOO",
                "A00099": "其他"
            },
            "BID_TYPE": {
                "A00001": "公开招标",
                "A00099": "其他公开竞争方式"
            }
        }

        mapping = code_mapping.get(code_type, {})
        return mapping.get(code_value, code_value)

    def get_stage_name(self, stage_code):
        """获取项目阶段名称"""
        stage_map = {
            '01': '特许经营方案编制阶段',
            '02': '特许经营方案论证阶段',
            '03': '特许经营者选择阶段',
            '04': '特许经营协议签订阶段',
            '05': '特许经营项目建设或运营阶段',
            '06': '特许经营项目移交阶段'
        }
        return stage_map.get(stage_code, stage_code)