# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
import pymysql
from datetime import datetime
import logging
from public_private_partnership_crawler.items import FranchiseProjectItem, FranchiseAttachmentItem
from model import *
import datetime
import os
import pandas as pd


class PublicPrivatePartnershipCrawlerPipeline:
    """JSON文件存储管道"""

    def __init__(self):
        self.df = pd.DataFrame()
        self.src_path = r'./tmp/{}/json/{}.json'
        self.time = datetime.datetime.now().strftime('%Y-%m-%dT%H_%M_%S')

    def open_spider(self, spider):
        path = self.src_path.format(spider.name, self.time)
        if not os.path.exists('./tmp'):
            os.mkdir('./tmp')
        if not os.path.exists('./tmp/{}'.format(spider.name)):
            os.mkdir('./tmp/{}'.format(spider.name))
        if not os.path.exists('./tmp/{}/json'.format(spider.name)):
            os.mkdir('./tmp/{}/json'.format(spider.name))

    def process_item(self, item, spider):
        line = pd.DataFrame([item])
        self.df = pd.concat([self.df, line], ignore_index=True)
        return item

    def close_spider(self, spider):
        src_path = self.src_path.format(spider.name, self.time)
        self.df.to_json(src_path, orient='records', ensure_ascii=False, indent=2)


class DataValidationPipeline:
    """数据验证管道"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, FranchiseProjectItem):
            # 验证必需字段
            if not adapter.get('project_id'):
                raise ValueError("project_id is required")
            if not adapter.get('project_name'):
                raise ValueError("project_name is required")

            # 数据类型转换和验证
            self._validate_and_convert_project_item(adapter, spider)

        elif isinstance(item, FranchiseAttachmentItem):
            # 验证附件必需字段
            if not adapter.get('attachment_id'):
                raise ValueError("attachment_id is required")
            if not adapter.get('project_id'):
                raise ValueError("project_id is required")

        return item

    def _validate_and_convert_project_item(self, adapter, spider):
        """验证和转换项目数据"""
        try:
            # 转换数值字段
            numeric_fields = [
                'total_investment', 'expected_private_capital', 'expected_project_capital',
                'gov_invest_ratio', 'gov_share_ratio', 'gov_invest_capital',
                'subsidy_limit', 'private_share_ratio'
            ]

            for field in numeric_fields:
                value = adapter.get(field)
                if value is not None and value != '':
                    try:
                        adapter[field] = float(value)
                    except (ValueError, TypeError):
                        adapter[field] = 0.0
                        spider.logger.warning(f"无法转换字段 {field} 的值: {value}")
                else:
                    adapter[field] = 0.0

            # 转换整数字段
            integer_fields = ['franchise_period']
            for field in integer_fields:
                value = adapter.get(field)
                if value is not None and value != '':
                    try:
                        adapter[field] = int(float(value))
                    except (ValueError, TypeError):
                        adapter[field] = 0
                        spider.logger.warning(f"无法转换字段 {field} 的值: {value}")
                else:
                    adapter[field] = 0

            # 转换布尔字段
            boolean_fields = ['has_gov_subsidy', 'has_operation_subsidy',]
            for field in boolean_fields:
                value = adapter.get(field)
                if isinstance(value, str):
                    adapter[field] = value.lower() in ('1', 'true', 'yes', '是')
                elif value is None:
                    adapter[field] = False
                else:
                    adapter[field] = bool(value)

            # 确保字符串字段长度限制
            string_fields = {
                'project_code': 100,
                'project_name': 500,
                'area_code': 50,
                'province_code': 10,
                'city_code': 10,
                'county_code': 10,
                'project_level': 10,
                'industry_code': 20,
                'project_type': 10,
                'exec_mode': 10,
                'verification_code': 20
            }

            for field, max_length in string_fields.items():
                value = adapter.get(field, '')
                if isinstance(value, str) and len(value) > max_length:
                    adapter[field] = value[:max_length]
                    spider.logger.warning(f"字段 {field} 长度超限，已截断")

        except Exception as e:
            spider.logger.error(f"数据验证出错: {e}")
            raise


class MySQLPipeline:
    """MySQL数据存储管道 - 优化版"""

    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.engine = create_engine(
            f"mysql+pymysql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['database']}?charset=utf8mb4",
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)

    @classmethod
    def from_crawler(cls, crawler):
        """从crawler获取数据库配置"""
        db_settings = crawler.settings.getdict("DATABASE")
        return cls(db_settings)

    def open_spider(self, spider):
        """爬虫开始时连接数据库"""
        try:
            Base.metadata.create_all(self.engine)
            spider.logger.info("Connected to MySQL database successfully")
        except Exception as e:
            spider.logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def close_spider(self, spider):
        """爬虫结束时关闭数据库连接"""
        self.engine.dispose()
        spider.logger.info("Disconnected from MySQL database")

    def process_item(self, item, spider):
        """处理每个项目数据"""
        session = self.Session()

        try:
            if isinstance(item, FranchiseProjectItem):
                self._process_project_item(item, session, spider)
            elif isinstance(item, FranchiseAttachmentItem):
                self._process_attachment_item(item, session, spider)

            session.commit()

        except Exception as e:
            session.rollback()
            spider.logger.error(f"Failed to process item: {e}")
            raise

        finally:
            session.close()

        return item

    def _process_project_item(self, item, session, spider):
        """处理项目数据"""
        existing_project = session.query(FranchiseProject).filter_by(project_id=item['project_id']).first()

        if existing_project:
            # 更新现有项目
            for key, value in item.items():
                if hasattr(existing_project, key):
                    setattr(existing_project, key, value)
            spider.logger.info(f"Updated project: {item['project_name']}")
        else:
            # 插入新项目
            # 移除不存在的字段
            project_data = {}
            for key, value in item.items():
                if hasattr(FranchiseProject, key):
                    project_data[key] = value
                else:
                    spider.logger.debug(f"Skipping field {key} - not in model")

            new_project = FranchiseProject(**project_data)
            session.add(new_project)
            spider.logger.info(f"Inserted new project: {item['project_name']}")

    def _process_attachment_item(self, item, session, spider):
        """处理附件数据"""
        existing_attachment = session.query(FranchiseAttachment).filter_by(
            attachment_id=item['attachment_id']).first()

        if existing_attachment:
            # 更新现有附件
            for key, value in item.items():
                if hasattr(existing_attachment, key):
                    setattr(existing_attachment, key, value)
            spider.logger.info(f"Updated attachment: {item['file_name']}")
        else:
            # 插入新附件
            attachment_data = {}
            for key, value in item.items():
                if hasattr(FranchiseAttachment, key):
                    attachment_data[key] = value
                else:
                    spider.logger.debug(f"Skipping field {key} - not in model")

            new_attachment = FranchiseAttachment(**attachment_data)
            session.add(new_attachment)
            spider.logger.info(f"Inserted new attachment: {item['file_name']}")


class DuplicatesPipeline:
    """去重管道"""

    def __init__(self):
        self.seen_projects = set()
        self.seen_attachments = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, FranchiseProjectItem):
            project_id = adapter['project_id']
            if project_id in self.seen_projects:
                spider.logger.debug(f"Duplicate project found: {project_id}")
                raise DropItem(f"Duplicate project: {project_id}")
            else:
                self.seen_projects.add(project_id)

        elif isinstance(item, FranchiseAttachmentItem):
            attachment_id = adapter['attachment_id']
            if attachment_id in self.seen_attachments:
                spider.logger.debug(f"Duplicate attachment found: {attachment_id}")
                raise DropItem(f"Duplicate attachment: {attachment_id}")
            else:
                self.seen_attachments.add(attachment_id)

        return item


class StatisticsPipeline:
    """统计管道"""

    def __init__(self):
        self.projects_count = 0
        self.attachments_count = 0
        self.project_stages = {}
        self.exec_modes = {}

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, FranchiseProjectItem):
            self.projects_count += 1

            # 统计项目阶段
            stage = adapter.get('project_stage_name', 'Unknown')
            self.project_stages[stage] = self.project_stages.get(stage, 0) + 1

            # 统计实施模式
            exec_mode = adapter.get('exec_mode_name', 'Unknown')
            self.exec_modes[exec_mode] = self.exec_modes.get(exec_mode, 0) + 1

        elif isinstance(item, FranchiseAttachmentItem):
            self.attachments_count += 1

        return item

    def close_spider(self, spider):
        """爬虫结束时输出统计信息"""
        spider.logger.info(f"爬取统计:")
        spider.logger.info(f"- 项目总数: {self.projects_count}")
        spider.logger.info(f"- 附件总数: {self.attachments_count}")
        spider.logger.info(f"- 项目阶段分布: {self.project_stages}")
        spider.logger.info(f"- 实施模式分布: {self.exec_modes}")