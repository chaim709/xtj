# -*- coding: utf-8 -*-
"""数据模型"""
from app import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


class Institution(db.Model):
    """机构配置（单例）"""
    __tablename__ = 'institution'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='培训机构')  # 机构名称
    slogan = db.Column(db.String(256))  # 机构标语
    logo_path = db.Column(db.String(256))  # Logo文件路径
    
    # 联系方式
    phone = db.Column(db.String(32))  # 联系电话
    wechat = db.Column(db.String(64))  # 微信号
    address = db.Column(db.String(256))  # 地址
    website = db.Column(db.String(128))  # 网站
    
    # 品牌颜色
    primary_color = db.Column(db.String(16), default='#1a73e8')  # 主色调
    secondary_color = db.Column(db.String(16), default='#34a853')  # 辅助色
    
    # 页眉页脚文字
    header_text = db.Column(db.String(256))  # 页眉文字
    footer_text = db.Column(db.String(256))  # 页脚文字
    
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @classmethod
    def get_instance(cls):
        """获取机构配置单例"""
        inst = cls.query.first()
        if not inst:
            inst = cls(name='新途径公考')
            db.session.add(inst)
            db.session.commit()
        return inst
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slogan': self.slogan,
            'logo_path': self.logo_path,
            'phone': self.phone,
            'wechat': self.wechat,
            'address': self.address,
            'website': self.website,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'header_text': self.header_text,
            'footer_text': self.footer_text
        }


class WorkbookTemplate(db.Model):
    """习题册模板配置"""
    __tablename__ = 'workbook_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 模板名称
    
    # 答案模式: hidden(隐藏), separated(分离), inline(直接显示)
    answer_mode = db.Column(db.String(16), default='hidden')
    
    # 排版配置
    questions_per_page = db.Column(db.Integer, default=5)
    show_difficulty = db.Column(db.Boolean, default=False)  # 显示难度
    show_category = db.Column(db.Boolean, default=True)  # 显示分类
    show_knowledge_point = db.Column(db.Boolean, default=False)  # 显示知识点
    
    # 品牌配置
    brand_enabled = db.Column(db.Boolean, default=True)  # 是否显示品牌
    show_cover = db.Column(db.Boolean, default=True)  # 是否生成封面
    show_qrcode = db.Column(db.Boolean, default=True)  # 是否显示二维码
    
    # 字体大小
    title_font_size = db.Column(db.Integer, default=16)
    stem_font_size = db.Column(db.Integer, default=12)
    option_font_size = db.Column(db.Integer, default=11)
    
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认模板
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @classmethod
    def get_default(cls):
        """获取默认模板"""
        template = cls.query.filter_by(is_default=True).first()
        if not template:
            template = cls.query.first()
        if not template:
            # 创建默认模板
            template = cls(
                name='默认模板',
                answer_mode='hidden',
                questions_per_page=5,
                brand_enabled=True,
                show_cover=True,
                show_qrcode=True,
                is_default=True
            )
            db.session.add(template)
            db.session.commit()
        return template
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'answer_mode': self.answer_mode,
            'questions_per_page': self.questions_per_page,
            'show_difficulty': self.show_difficulty,
            'show_category': self.show_category,
            'show_knowledge_point': self.show_knowledge_point,
            'brand_enabled': self.brand_enabled,
            'show_cover': self.show_cover,
            'show_qrcode': self.show_qrcode,
            'is_default': self.is_default
        }


class Admin(UserMixin, db.Model):
    """管理员"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Question(db.Model):
    """题目"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(32), unique=True, nullable=False)  # Q-001
    
    # 题目内容
    stem = db.Column(db.Text, nullable=False)  # 题干
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    answer = db.Column(db.String(4))  # A/B/C/D 或组合
    analysis = db.Column(db.Text)  # 解析
    
    # 分类
    category = db.Column(db.String(64))  # 一级分类：常识判断、言语理解等
    subcategory = db.Column(db.String(64))  # 二级分类
    knowledge_point = db.Column(db.String(128))  # 知识点
    
    # 来源
    source = db.Column(db.String(128))  # 来源资料名称
    difficulty = db.Column(db.String(16), default='中等')  # 难度
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    workbook_items = db.relationship('WorkbookItem', backref='question', lazy='dynamic')
    mistakes = db.relationship('Mistake', backref='question', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'stem': self.stem,
            'options': {
                'A': self.option_a,
                'B': self.option_b,
                'C': self.option_c,
                'D': self.option_d
            },
            'answer': self.answer,
            'analysis': self.analysis,
            'category': self.category,
            'subcategory': self.subcategory,
            'knowledge_point': self.knowledge_point
        }


class Workbook(db.Model):
    """题册"""
    __tablename__ = 'workbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # 题册名称
    description = db.Column(db.Text)  # 描述
    category = db.Column(db.String(64))  # 分类：专项练习/模拟套卷/真题
    
    questions_per_page = db.Column(db.Integer, default=5)  # 每页题目数
    total_questions = db.Column(db.Integer, default=0)  # 总题目数
    total_pages = db.Column(db.Integer, default=0)  # 总页数
    
    # 模板配置
    template_id = db.Column(db.Integer, db.ForeignKey('workbook_templates.id'))
    answer_mode = db.Column(db.String(16), default='hidden')  # hidden/separated/inline
    
    # 生成的文件
    pdf_path = db.Column(db.String(256))
    pdf_answers_path = db.Column(db.String(256))  # 答案PDF路径（分离模式）
    word_path = db.Column(db.String(256))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 模板关联
    template = db.relationship('WorkbookTemplate', backref='workbooks')
    
    # 关联
    items = db.relationship('WorkbookItem', backref='workbook', lazy='dynamic',
                           order_by='WorkbookItem.order')
    pages = db.relationship('WorkbookPage', backref='workbook', lazy='dynamic',
                           order_by='WorkbookPage.page_num')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'total_questions': self.total_questions,
            'total_pages': self.total_pages,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class WorkbookItem(db.Model):
    """题册题目关联"""
    __tablename__ = 'workbook_items'
    
    id = db.Column(db.Integer, primary_key=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)  # 题目序号 (1, 2, 3...)
    page_num = db.Column(db.Integer)  # 所在页码


class WorkbookPage(db.Model):
    """题册页面（用于二维码）"""
    __tablename__ = 'workbook_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    page_num = db.Column(db.Integer, nullable=False)  # 页码
    
    # 该页包含的题目范围
    start_order = db.Column(db.Integer)  # 起始题号
    end_order = db.Column(db.Integer)  # 结束题号
    
    # 二维码唯一标识
    qr_code = db.Column(db.String(32), unique=True)  # 用于扫码识别


class StudentClass(db.Model):
    """班级"""
    __tablename__ = 'student_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 班级名称
    description = db.Column(db.String(256))  # 描述
    teacher = db.Column(db.String(64))  # 班主任/老师
    
    # 时间
    start_date = db.Column(db.Date)  # 开班日期
    end_date = db.Column(db.Date)  # 结班日期
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    students = db.relationship('Student', backref='student_class', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'teacher': self.teacher,
            'student_count': self.students.count()
        }


class Student(db.Model):
    """学员（通过手机号识别）"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    
    # 班级关联
    class_id = db.Column(db.Integer, db.ForeignKey('student_classes.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_submit_at = db.Column(db.DateTime)
    
    # 关联
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')
    mistakes = db.relationship('Mistake', backref='student', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'class_id': self.class_id,
            'class_name': self.student_class.name if self.student_class else None,
            'total_mistakes': self.mistakes.count()
        }


class Submission(db.Model):
    """提交记录"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    page_num = db.Column(db.Integer)  # 提交的页码
    
    # 错题数量
    mistake_count = db.Column(db.Integer, default=0)
    
    # 新增：做题统计字段
    total_attempted = db.Column(db.Integer, default=0)  # 本次做了多少题
    correct_count = db.Column(db.Integer, default=0)    # 正确数（自动计算）
    accuracy_rate = db.Column(db.Float)                 # 正确率（自动计算，0-100）
    
    # 新增：关联的板块信息（从二维码解析）
    category = db.Column(db.String(64))      # 一级分类（如：言语理解）
    subcategory = db.Column(db.String(64))   # 二级分类/板块（如：片段阅读）
    
    # 题号范围（用于按范围提交）
    start_order = db.Column(db.Integer)  # 起始题号
    end_order = db.Column(db.Integer)    # 结束题号
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    workbook = db.relationship('Workbook')
    
    def calculate_accuracy(self):
        """计算正确率"""
        if self.total_attempted > 0:
            self.correct_count = self.total_attempted - self.mistake_count
            self.accuracy_rate = round(self.correct_count / self.total_attempted * 100, 1)
        else:
            self.correct_count = 0
            self.accuracy_rate = 0


class Mistake(db.Model):
    """错题记录"""
    __tablename__ = 'mistakes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'))
    question_order = db.Column(db.Integer)  # 在题册中的题号
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    workbook = db.relationship('Workbook')
    submission = db.relationship('Submission', backref='mistakes')


class MistakeReview(db.Model):
    """错题复习记录"""
    __tablename__ = 'mistake_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # 复习状态
    review_count = db.Column(db.Integer, default=0)  # 复习次数
    last_review_at = db.Column(db.DateTime)  # 上次复习时间
    next_review_at = db.Column(db.DateTime)  # 下次复习时间
    
    # 艾宾浩斯间隔（天）: 1, 2, 4, 7, 15, 30
    current_interval = db.Column(db.Integer, default=1)
    
    # 是否已掌握
    mastered = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    student = db.relationship('Student', backref='reviews')
    question = db.relationship('Question')
    
    @classmethod
    def get_or_create(cls, student_id, question_id):
        """获取或创建复习记录"""
        review = cls.query.filter_by(
            student_id=student_id,
            question_id=question_id
        ).first()
        
        if not review:
            # 计算下次复习时间（1天后）
            from datetime import timedelta
            review = cls(
                student_id=student_id,
                question_id=question_id,
                next_review_at=datetime.now() + timedelta(days=1)
            )
            db.session.add(review)
        
        return review
    
    def record_review(self, is_correct):
        """记录一次复习"""
        from datetime import timedelta
        
        self.review_count += 1
        self.last_review_at = datetime.now()
        
        # 艾宾浩斯间隔
        intervals = [1, 2, 4, 7, 15, 30]
        
        if is_correct:
            # 答对了，增加间隔
            idx = intervals.index(self.current_interval) if self.current_interval in intervals else 0
            if idx < len(intervals) - 1:
                self.current_interval = intervals[idx + 1]
            else:
                self.mastered = True  # 已掌握
            self.next_review_at = datetime.now() + timedelta(days=self.current_interval)
        else:
            # 答错了，重置间隔
            self.current_interval = 1
            self.next_review_at = datetime.now() + timedelta(days=1)
            self.mastered = False


class StudentStats(db.Model):
    """学员统计汇总（缓存表，提升查询性能）"""
    __tablename__ = 'student_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # 统计维度
    dimension = db.Column(db.String(32), nullable=False)  # 'total'/'workbook'/'category'/'subcategory'/'knowledge_point'
    dimension_value = db.Column(db.String(128))  # 具体值，如"言语理解"/"片段阅读"，total时为空
    
    # 统计数据
    total_attempted = db.Column(db.Integer, default=0)  # 总做题数
    total_correct = db.Column(db.Integer, default=0)    # 总正确数
    total_mistakes = db.Column(db.Integer, default=0)   # 总错题数
    accuracy_rate = db.Column(db.Float)                 # 正确率（0-100）
    
    # 时间范围
    period = db.Column(db.String(16), default='all')  # 'all'/'7d'/'30d'
    
    # 额外统计
    submission_count = db.Column(db.Integer, default=0)  # 提交次数
    study_days = db.Column(db.Integer, default=0)        # 学习天数
    
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    student = db.relationship('Student', backref='stats')
    
    # 索引
    __table_args__ = (
        db.Index('idx_student_dimension_period', 'student_id', 'dimension', 'period'),
    )
    
    def calculate_accuracy(self):
        """计算正确率"""
        if self.total_attempted > 0:
            self.accuracy_rate = round(self.total_correct / self.total_attempted * 100, 1)
        else:
            self.accuracy_rate = 0
    
    @classmethod
    def get_or_create(cls, student_id, dimension, dimension_value=None, period='all'):
        """获取或创建统计记录"""
        stat = cls.query.filter_by(
            student_id=student_id,
            dimension=dimension,
            dimension_value=dimension_value,
            period=period
        ).first()
        
        if not stat:
            stat = cls(
                student_id=student_id,
                dimension=dimension,
                dimension_value=dimension_value,
                period=period
            )
            db.session.add(stat)
        
        return stat
    
    def to_dict(self):
        return {
            'dimension': self.dimension,
            'dimension_value': self.dimension_value,
            'total_attempted': self.total_attempted,
            'total_correct': self.total_correct,
            'total_mistakes': self.total_mistakes,
            'accuracy_rate': self.accuracy_rate,
            'period': self.period
        }
