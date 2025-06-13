import scrapy


class FranchiseProjectItem(scrapy.Item):
    """特许经营项目数据模型 - 优化版"""

    # 基础信息
    project_id = scrapy.Field()  # 项目ID（唯一标识）
    project_code = scrapy.Field()  # 项目代码
    project_name = scrapy.Field()  # 项目名称

    # 地区信息 - 支持多级地区筛选
    province_code = scrapy.Field()  # 省份代码
    province_name = scrapy.Field()  # 省份名称
    city_code = scrapy.Field()  # 城市代码
    city_name = scrapy.Field()  # 城市名称
    county_code = scrapy.Field()  # 区县代码
    county_name = scrapy.Field()  # 区县名称
    area_code = scrapy.Field()  # 所属地区代码
    area_name = scrapy.Field()  # 所属行政区划
    construction_location = scrapy.Field()  # 建设地点

    # 项目分类信息
    project_level = scrapy.Field()  # 项目层级代码
    project_level_name = scrapy.Field()  # 项目层级名称
    industry_code = scrapy.Field()  # 所属行业代码
    industry_name = scrapy.Field()  # 所属行业
    project_type = scrapy.Field()  # 项目类型代码
    project_type_name = scrapy.Field()  # 项目类型名称

    # 实施模式
    exec_mode = scrapy.Field()  # 实施模式代码
    exec_mode_name = scrapy.Field()  # 实施模式名称

    # 投资信息
    total_investment = scrapy.Field()  # 预计项目总投资
    expected_private_capital = scrapy.Field()  # 预计民间投资（万元）
    expected_project_capital = scrapy.Field()  # 预计项目资本金（万元）
    scale_content = scrapy.Field()  # 建设内容和规模

    # 特许经营信息
    franchise_period = scrapy.Field()  # 特许经营期限（年）
    pre_start_date = scrapy.Field()  # 预计开始日期
    pre_end_date = scrapy.Field()  # 预计结束日期

    # 政府补贴信息
    has_gov_subsidy = scrapy.Field()  # 有无政府补贴（bool）
    gov_invest_type = scrapy.Field()  # 投资支持形式
    gov_invest_ratio = scrapy.Field()  # 政府投资支持预计比例（%）
    gov_representative = scrapy.Field()  # 政府出资人代表
    gov_share_ratio = scrapy.Field()  # 政府出资人代表预计持股比例（%）
    gov_invest_capital = scrapy.Field()  # 预计政府投资资本金（万元）

    # 运营补贴信息
    has_operation_subsidy = scrapy.Field()  # 有无运营补贴（bool）
    subsidy_source = scrapy.Field()  # 运营补贴资金来源
    subsidy_limit = scrapy.Field()  # 运营补贴上限（万元）
    subsidy_mode = scrapy.Field()  # 运营补贴方式

    # 招投标信息
    bidding_method = scrapy.Field()  # 招标方式
    bidding_time = scrapy.Field()  # 招标时间（公开竞争文件发布时间）

    # 中标信息
    winner_nature = scrapy.Field()  # 中标单位性质
    winner_names = scrapy.Field()  # 中标单位名称（多个用逗号分隔）
    private_share_ratio = scrapy.Field()  # 民营企业特许经营者预计持股比例（%）

    # 项目进展
    project_stage = scrapy.Field()  # 进行阶段代码
    project_stage_name = scrapy.Field()  # 进行阶段名称

    # 审批信息
    approval_org_name = scrapy.Field()  # 审批机关名称
    approval_date = scrapy.Field()  # 审批时间

    # 实施机构信息
    implement_org_name = scrapy.Field()  # 实施机构名称
    implement_contact = scrapy.Field()  # 实施机构联系人
    implement_phone = scrapy.Field()  # 实施机构联系电话

    # 咨询机构信息
    consult_org_name = scrapy.Field()  # 实施机构聘请的咨询机构名称
    consult_contact = scrapy.Field()  # 咨询机构联系人
    consult_phone = scrapy.Field()  # 咨询机构联系电话

    # 法律机构信息
    law_firm_name = scrapy.Field()  # 实施机构聘请的律师事务所名称
    law_firm_contact = scrapy.Field()  # 法律机构联系人
    law_firm_phone = scrapy.Field()  # 法律机构联系电话

    # 授权政府
    mandate_gov = scrapy.Field()  # 授权政府名称

    # 民营企业参与情况
    private_enterprise_plan = scrapy.Field()  # 民营企业参与方案

    # 状态字段
    is_published = scrapy.Field()  # 是否公开
    verification_code = scrapy.Field()  # 验证码

    # 时间戳
    create_time = scrapy.Field()  # 创建时间
    update_time = scrapy.Field()  # 更新时间
    crawl_time = scrapy.Field()  # 爬取时间


class FranchiseAttachmentItem(scrapy.Item):
    """特许经营项目附件数据模型 - 优化版"""

    # 附件基本信息
    attachment_id = scrapy.Field()  # 附件ID（系统中的文件ID）
    project_id = scrapy.Field()  # 关联的项目ID（外键）

    # 文件信息
    file_type = scrapy.Field()  # 文件类型（gov_auth/franchise_plan/bidding_file等）
    file_name = scrapy.Field()  # 文件名称（描述性名称）
    original_filename = scrapy.Field()  # 原始文件名
    content_type = scrapy.Field()  # 文件MIME类型
    file_size = scrapy.Field()  # 文件大小（字节）

    # 文件下载链接
    download_url = scrapy.Field()  # 文件下载链接
    file_content = scrapy.Field()  # 文件二进制内容（可选）

    # 文件分类
    attachment_category = scrapy.Field()  # 附件分类

    # 状态
    is_downloaded = scrapy.Field()  # 是否已下载
    download_time = scrapy.Field()  # 下载时间