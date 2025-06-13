from sqlalchemy import create_engine, Column, String, Integer, DECIMAL, TEXT, DATETIME, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import logging

Base = declarative_base()


class FranchiseProject(Base):
    __tablename__ = 'franchise_projects'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    project_id = Column(String(100), unique=True, nullable=False, comment='项目ID（唯一标识）', index=True)
    project_code = Column(String(100), comment='项目代码', index=True)
    project_name = Column(String(500), nullable=False, comment='项目名称', index=True)

    # 地区信息 - 支持多级地区筛选
    province_code = Column(String(10), comment='省份代码', index=True)
    province_name = Column(String(50), comment='省份名称', index=True)
    city_code = Column(String(10), comment='城市代码', index=True)
    city_name = Column(String(50), comment='城市名称', index=True)
    county_code = Column(String(10), comment='区县代码', index=True)
    county_name = Column(String(50), comment='区县名称', index=True)
    area_code = Column(String(50), comment='所属地区代码（审批机关）', index=True)
    area_name = Column(String(200), comment='所属地区名称（审批机关）', index=True)
    construction_location = Column(TEXT, comment='建设地点')

    # 项目分类信息 - 优化为可筛选字段
    project_level = Column(String(10), comment='项目层级代码', index=True)
    project_level_name = Column(String(50), comment='项目层级名称', index=True)
    industry_code = Column(String(20), comment='所属行业代码', index=True)
    industry_name = Column(String(200), comment='所属行业名称', index=True)
    project_type = Column(String(10), comment='项目类型代码', index=True)
    project_type_name = Column(String(200), comment='项目类型名称', index=True)

    # 实施模式
    exec_mode = Column(String(10), comment='实施模式代码', index=True)
    exec_mode_name = Column(String(50), comment='实施模式名称', index=True)

    # 投资信息 - 修改为数值类型
    total_investment = Column(DECIMAL(15, 4), comment='总投资（万元）', index=True)
    expected_private_capital = Column(DECIMAL(15, 4), comment='预计民间投资（万元）')
    expected_project_capital = Column(DECIMAL(15, 4), comment='预计项目资本金（万元）')
    scale_content = Column(TEXT, comment='建设规模及内容')

    # 特许经营信息
    franchise_period = Column(Integer, comment='特许经营期限（年）', index=True)
    pre_start_date = Column(Date, comment='预计开始日期')
    pre_end_date = Column(Date, comment='预计结束日期')

    # 政府补贴信息 - 优化为布尔类型和数值类型
    has_gov_subsidy = Column(Boolean, default=False, comment='有无政府补贴', index=True)
    gov_invest_type = Column(String(200), comment='投资支持形式')
    gov_invest_ratio = Column(DECIMAL(5, 2), comment='政府投资支持预计比例（%）')
    gov_representative = Column(String(200), comment='政府出资人代表')
    gov_share_ratio = Column(DECIMAL(5, 2), comment='政府出资人代表预计持股比例（%）')
    gov_invest_capital = Column(DECIMAL(15, 4), comment='预计政府投资资本金（万元）')

    # 运营补贴信息
    has_operation_subsidy = Column(Boolean, default=False, comment='有无运营补贴', index=True)
    subsidy_source = Column(String(500), comment='运营补贴资金来源')
    subsidy_limit = Column(DECIMAL(15, 4), comment='运营补贴上限（万元）')
    subsidy_mode = Column(String(200), comment='运营补贴方式')

    # 招投标信息
    bidding_method = Column(String(100), comment='招标方式', index=True)
    bidding_time = Column(Date, comment='招标时间（公开竞争文件发布时间）', index=True)

    # 中标信息
    winner_nature = Column(TEXT, comment='中标单位性质', index=True)
    winner_names = Column(TEXT, comment='中标单位名称（多个用逗号分隔）')
    private_share_ratio = Column(DECIMAL(5, 2), comment='民营企业特许经营者预计持股比例（%）', index=True)

    # 项目进展
    project_stage = Column(String(10), comment='进行阶段代码', index=True)
    project_stage_name = Column(String(100), comment='进行阶段名称', index=True)

    # 审批信息
    approval_org_name = Column(String(200), comment='审批机关名称')
    approval_date = Column(Date, comment='审批时间')

    # 实施机构信息
    implement_org_name = Column(String(200), comment='实施机构名称')
    implement_contact = Column(String(100), comment='实施机构联系人')
    implement_phone = Column(String(50), comment='实施机构联系电话')

    # 咨询机构信息
    consult_org_name = Column(String(200), comment='咨询机构名称')
    consult_contact = Column(String(100), comment='咨询机构联系人')
    consult_phone = Column(String(50), comment='咨询机构联系电话')

    # 法律机构信息
    law_firm_name = Column(String(200), comment='法律机构名称')
    law_firm_contact = Column(String(100), comment='法律机构联系人')
    law_firm_phone = Column(String(50), comment='法律机构联系电话')

    # 授权政府
    mandate_gov = Column(String(200), comment='授权政府')

    # 民营企业参与情况
    private_enterprise_plan = Column(TEXT, comment='民营企业参与方案')

    # 状态字段
    is_published = Column(Boolean, default=True, comment='是否公开')
    verification_code = Column(String(20), comment='验证码')

    # 时间戳
    create_time = Column(DATETIME, comment='创建时间')
    update_time = Column(DATETIME, comment='更新时间', index=True)
    crawl_time = Column(DATETIME, comment='爬取时间', index=True)

    # 关联附件
    attachments = relationship('FranchiseAttachment', back_populates='project', cascade='all, delete-orphan')


class FranchiseAttachment(Base):
    __tablename__ = 'franchise_attachments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    attachment_id = Column(String(100), unique=True, nullable=False, comment='附件ID', index=True)
    project_id = Column(String(100), ForeignKey('franchise_projects.project_id'), nullable=False, comment='关联项目ID',
                        index=True)

    # 文件信息
    file_type = Column(String(50), comment='文件类型', index=True)
    file_name = Column(String(500), comment='文件名称')
    original_filename = Column(String(500), comment='原始文件名')
    content_type = Column(String(200), comment='文件MIME类型')
    file_size = Column(Integer, comment='文件大小（字节）')

    # 文件下载链接（不存储内容，只存储下载链接）
    download_url = Column(String(1000), comment='文件下载链接')
    file_content = Column(TEXT, comment='文件内容（可选存储）')

    # 文件分类
    attachment_category = Column(String(50), comment='附件分类', index=True)  # 政府授权、特许经营方案、招标文件、中标文件等

    # 状态
    is_downloaded = Column(Boolean, default=False, comment='是否已下载')
    download_time = Column(DATETIME, comment='下载时间')

    project = relationship('FranchiseProject', back_populates='attachments')