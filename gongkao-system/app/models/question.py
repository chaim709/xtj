# -*- coding: utf-8 -*-
"""
题库相关模型 - 从cuoti-system迁移
"""
from datetime import datetime
from app import db
import json


class Institution(db.Model):
    """机构配置（单例）"""
    __tablename__ = 'institution'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='培训机构')
    slogan = db.Column(db.String(256))
    logo_path = db.Column(db.String(256))
    
    phone = db.Column(db.String(32))
    wechat = db.Column(db.String(64))
    address = db.Column(db.String(256))
    website = db.Column(db.String(128))
    
    primary_color = db.Column(db.String(16), default='#1a73e8')
    secondary_color = db.Column(db.String(16), default='#34a853')
    
    header_text = db.Column(db.String(256))
    footer_text = db.Column(db.String(256))
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_instance(cls):
        inst = cls.query.first()
        if not inst:
            inst = cls(name='新途径公考')
            db.session.add(inst)
            db.session.commit()
        return inst


class WorkbookTemplate(db.Model):
    """习题册模板配置"""
    __tablename__ = 'workbook_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    
    answer_mode = db.Column(db.String(16), default='hidden')
    questions_per_page = db.Column(db.Integer, default=5)
    show_difficulty = db.Column(db.Boolean, default=False)
    show_category = db.Column(db.Boolean, default=True)
    show_knowledge_point = db.Column(db.Boolean, default=False)
    
    brand_enabled = db.Column(db.Boolean, default=True)
    show_cover = db.Column(db.Boolean, default=True)
    show_qrcode = db.Column(db.Boolean, default=True)
    
    title_font_size = db.Column(db.Integer, default=16)
    stem_font_size = db.Column(db.Integer, default=12)
    option_font_size = db.Column(db.Integer, default=11)
    
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_default(cls):
        template = cls.query.filter_by(is_default=True).first()
        if not template:
            template = cls.query.first()
        if not template:
            template = cls(name='默认模板', is_default=True)
            db.session.add(template)
            db.session.commit()
        return template


class Question(db.Model):
    """题目"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 题目内容
    stem = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    
    # 答案和解析
    answer = db.Column(db.String(8))
    analysis = db.Column(db.Text)
    
    # 分类
    category = db.Column(db.String(64))
    subcategory = db.Column(db.String(64))
    knowledge_point = db.Column(db.String(128))
    
    # 元数据
    difficulty = db.Column(db.Integer, default=3)
    source = db.Column(db.String(256))
    year = db.Column(db.Integer)
    
    # 图片题目支持
    is_image_question = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(512))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    workbook_items = db.relationship('WorkbookItem', backref='question', lazy='dynamic')
    mistakes = db.relationship('Mistake', backref='question', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
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
            'knowledge_point': self.knowledge_point,
            'difficulty': self.difficulty
        }


class Workbook(db.Model):
    """题册"""
    __tablename__ = 'workbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    category = db.Column(db.String(64))
    total_questions = db.Column(db.Integer, default=0)
    total_pages = db.Column(db.Integer, default=0)
    answer_mode = db.Column(db.String(32), default='hidden')
    
    template_id = db.Column(db.Integer, db.ForeignKey('workbook_templates.id'))
    template = db.relationship('WorkbookTemplate')
    
    pdf_path = db.Column(db.String(512))
    answer_pdf_path = db.Column(db.String(512))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    items = db.relationship('WorkbookItem', backref='workbook', lazy='dynamic',
                           cascade='all, delete-orphan', order_by='WorkbookItem.order')
    pages = db.relationship('WorkbookPage', backref='workbook', lazy='dynamic',
                           cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='workbook', lazy='dynamic')
    mistakes = db.relationship('Mistake', backref='workbook', lazy='dynamic')
    
    def update_question_count(self):
        self.total_questions = self.items.count()


class WorkbookItem(db.Model):
    """题册题目关联"""
    __tablename__ = 'workbook_items'
    
    id = db.Column(db.Integer, primary_key=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkbookPage(db.Model):
    """题册页面（二维码关联）"""
    __tablename__ = 'workbook_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    
    page_num = db.Column(db.Integer, nullable=False)
    start_order = db.Column(db.Integer)
    end_order = db.Column(db.Integer)
    
    qr_code = db.Column(db.String(128), unique=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Submission(db.Model):
    """学员提交记录"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'))
    page_num = db.Column(db.Integer)
    
    # 统计字段
    total_attempted = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    mistake_count = db.Column(db.Integer, default=0)
    accuracy_rate = db.Column(db.Float)
    
    # 分类信息
    category = db.Column(db.String(64))
    subcategory = db.Column(db.String(64))
    start_order = db.Column(db.Integer)
    end_order = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_accuracy(self):
        if self.total_attempted and self.total_attempted > 0:
            self.correct_count = self.total_attempted - self.mistake_count
            self.accuracy_rate = round(self.correct_count / self.total_attempted * 100, 1)


class Mistake(db.Model):
    """错题记录"""
    __tablename__ = 'mistakes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'))
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    
    question_order = db.Column(db.Integer)
    wrong_answer = db.Column(db.String(8))
    
    review_count = db.Column(db.Integer, default=0)
    last_review_at = db.Column(db.DateTime)
    mastered = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MistakeReview(db.Model):
    """错题复习记录（艾宾浩斯）"""
    __tablename__ = 'mistake_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    review_count = db.Column(db.Integer, default=0)
    last_review_at = db.Column(db.DateTime)
    next_review_at = db.Column(db.DateTime)
    current_interval = db.Column(db.Integer, default=1)
    mastered = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='reviews')
    question = db.relationship('Question')
    
    @classmethod
    def get_or_create(cls, student_id, question_id):
        from datetime import timedelta
        review = cls.query.filter_by(
            student_id=student_id,
            question_id=question_id
        ).first()
        if not review:
            review = cls(
                student_id=student_id,
                question_id=question_id,
                next_review_at=datetime.utcnow() + timedelta(days=1)
            )
            db.session.add(review)
        return review
    
    def record_review(self, is_correct):
        from datetime import timedelta
        self.review_count += 1
        self.last_review_at = datetime.utcnow()
        
        intervals = [1, 2, 4, 7, 15, 30]
        
        if is_correct:
            idx = intervals.index(self.current_interval) if self.current_interval in intervals else 0
            if idx < len(intervals) - 1:
                self.current_interval = intervals[idx + 1]
            else:
                self.mastered = True
            self.next_review_at = datetime.utcnow() + timedelta(days=self.current_interval)
        else:
            self.current_interval = 1
            self.next_review_at = datetime.utcnow() + timedelta(days=1)
            self.mastered = False


class StudentStats(db.Model):
    """学员统计缓存"""
    __tablename__ = 'student_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    dimension = db.Column(db.String(32), nullable=False)
    dimension_value = db.Column(db.String(128))
    period = db.Column(db.String(16), default='all')
    
    total_attempted = db.Column(db.Integer, default=0)
    total_correct = db.Column(db.Integer, default=0)
    total_mistakes = db.Column(db.Integer, default=0)
    accuracy_rate = db.Column(db.Float, default=0)
    submission_count = db.Column(db.Integer, default=0)
    study_days = db.Column(db.Integer, default=0)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_accuracy(self):
        if self.total_attempted > 0:
            self.accuracy_rate = round(self.total_correct / self.total_attempted * 100, 1)
    
    @classmethod
    def get_or_create(cls, student_id, dimension, dimension_value, period='all'):
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


class StudentClass(db.Model):
    """学员班级"""
    __tablename__ = 'student_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    teacher = db.Column(db.String(64))
    
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    students = db.relationship('Student', backref='student_class', lazy='dynamic')
