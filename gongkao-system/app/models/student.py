"""
学员模型 - 存储学员基本信息和学情档案
"""
from datetime import datetime
from app import db


class Student(db.Model):
    """
    学员模型
    
    存储学员的基本信息、报考信息、学习画像等
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    phone = db.Column(db.String(20), comment='联系电话')
    wechat = db.Column(db.String(50), comment='微信号')
    
    # 班次和课程信息（兼容旧版本）
    class_name = db.Column(db.String(50), comment='班次名称(旧版本兼容)')
    exam_type = db.Column(db.String(100), comment='报考类型')
    target_position = db.Column(db.String(100), comment='目标岗位')
    exam_date = db.Column(db.Date, comment='考试日期')
    
    # 第二阶段新增：课程关联
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), comment='报名套餐ID')
    course_enrollment_date = db.Column(db.Date, comment='课程报名日期')
    valid_until = db.Column(db.Date, comment='有效期至')
    actual_price = db.Column(db.Numeric(10, 2), comment='实付金额')
    discount_info = db.Column(db.String(200), comment='优惠信息')
    
    # 学习画像
    has_basic = db.Column(db.Boolean, default=False, comment='是否有基础')
    is_agreement = db.Column(db.Boolean, default=False, comment='是否协议班')
    base_level = db.Column(db.String(20), comment='基础水平')
    learning_style = db.Column(db.String(20), comment='学习风格')
    study_plan = db.Column(db.Text, comment='个性化督学计划')
    
    # 个人信息
    education = db.Column(db.String(20), comment='学历')
    id_number = db.Column(db.String(30), comment='身份证号')
    address = db.Column(db.String(200), comment='家庭住址')
    
    # 智能选岗相关字段（第四阶段新增）
    major = db.Column(db.String(100), comment='专业')
    major_category_id = db.Column(db.Integer, db.ForeignKey('major_categories.id'), comment='专业大类ID')
    political_status = db.Column(db.String(20), comment='政治面貌')  # 党员/预备党员/团员/群众
    work_years = db.Column(db.Integer, default=0, comment='基层工作年限')
    hukou_province = db.Column(db.String(50), comment='户籍省份')
    hukou_city = db.Column(db.String(50), comment='户籍城市')
    gender = db.Column(db.String(10), comment='性别')  # 男/女
    birth_date = db.Column(db.Date, comment='出生日期')
    
    # 联系人信息
    parent_phone = db.Column(db.String(20), comment='家长联系电话')
    emergency_contact = db.Column(db.String(100), comment='紧急联系人')
    
    # 督学负责人
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='督学负责人ID')
    
    # 班级（错题系统）
    class_id = db.Column(db.Integer, db.ForeignKey('student_classes.id'), comment='班级ID')
    
    # 状态和时间
    enrollment_date = db.Column(db.Date, comment='入学日期')
    payment_status = db.Column(db.String(20), comment='缴费状态')
    status = db.Column(db.String(20), default='active', comment='状态')
    remarks = db.Column(db.Text, comment='备注')
    
    # 关注标记
    need_attention = db.Column(db.Boolean, default=False, comment='需重点关注')
    last_contact_date = db.Column(db.Date, comment='最后联系日期')
    
    # 微信小程序相关字段
    wx_openid = db.Column(db.String(64), unique=True, index=True, nullable=True, comment='微信OpenID')
    wx_unionid = db.Column(db.String(64), nullable=True, comment='微信UnionID')
    wx_avatar_url = db.Column(db.String(500), nullable=True, comment='微信头像URL')
    wx_nickname = db.Column(db.String(100), nullable=True, comment='微信昵称')
    
    # 打卡统计字段
    last_checkin_date = db.Column(db.Date, nullable=True, comment='最后打卡日期')
    total_checkin_days = db.Column(db.Integer, default=0, comment='累计打卡天数')
    consecutive_checkin_days = db.Column(db.Integer, default=0, comment='连续打卡天数')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    supervisor = db.relationship('User', backref=db.backref('students', lazy='dynamic'))
    weakness_tags = db.relationship('WeaknessTag', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    supervision_logs = db.relationship('SupervisionLog', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    homework_submissions = db.relationship('HomeworkSubmission', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    # 第二阶段新增关系
    package = db.relationship('Package', backref=db.backref('students', lazy='dynamic'))
    
    # 第四阶段新增关系（智能选岗）
    major_category = db.relationship('MajorCategory', backref=db.backref('students', lazy='dynamic'))
    
    # 题库与错题关系（从cuoti-system合并）
    submissions = db.relationship('Submission', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    mistakes = db.relationship('Mistake', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    student_stats = db.relationship('StudentStats', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'class_name': self.class_name,
            'exam_type': self.exam_type,
            'has_basic': self.has_basic,
            'is_agreement': self.is_agreement,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'status': self.status,
            'need_attention': self.need_attention,
            # 选岗相关字段
            'education': self.education,
            'major': self.major,
            'major_category_id': self.major_category_id,
            'major_category_name': self.major_category.name if self.major_category else None,
            'political_status': self.political_status,
            'work_years': self.work_years,
            'hukou_province': self.hukou_province,
            'hukou_city': self.hukou_city,
            'gender': self.gender,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            # 微信相关字段
            'wx_openid': self.wx_openid,
            'wx_unionid': self.wx_unionid,
            'wx_avatar_url': self.wx_avatar_url,
            'wx_nickname': self.wx_nickname,
            # 打卡统计字段
            'last_checkin_date': self.last_checkin_date.isoformat() if self.last_checkin_date else None,
            'total_checkin_days': self.total_checkin_days,
            'consecutive_checkin_days': self.consecutive_checkin_days,
        }
    
    @property
    def age(self):
        """计算年龄"""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    def is_position_eligible(self):
        """检查是否具备选岗必要条件"""
        return all([
            self.education,
            self.major or self.major_category_id,
            self.political_status,
            self.gender,
            self.birth_date
        ])