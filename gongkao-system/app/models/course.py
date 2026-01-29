"""
课程管理模型 - 科目、招生项目、报名套餐、班型、班次、课表
"""
from datetime import datetime, date
from app import db
import json


class Subject(db.Model):
    """
    科目模型
    
    管理考试科目，支持预设科目和自定义科目
    """
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='科目名称')
    short_name = db.Column(db.String(20), comment='简称')
    exam_type = db.Column(db.String(20), default='common', comment='考试类型(civil/career/common)')
    is_preset = db.Column(db.Boolean, default=False, comment='是否预设科目')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    status = db.Column(db.String(10), default='active', comment='状态(active/inactive)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    schedules = db.relationship('Schedule', backref='subject', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'exam_type': self.exam_type,
            'is_preset': self.is_preset,
            'sort_order': self.sort_order,
            'status': self.status,
        }


class Project(db.Model):
    """
    招生项目模型
    
    管理培训机构的招生项目，如"2026国省考系统班"
    """
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='项目名称')
    exam_type = db.Column(db.String(20), nullable=False, comment='考试类型(civil/career)')
    year = db.Column(db.Integer, nullable=False, comment='招生年份')
    start_date = db.Column(db.Date, comment='项目开始日期')
    end_date = db.Column(db.Date, comment='项目结束日期')
    description = db.Column(db.Text, comment='项目描述')
    status = db.Column(db.String(20), default='preparing', comment='状态(preparing/recruiting/ended)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    packages = db.relationship('Package', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    class_types = db.relationship('ClassType', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'exam_type': self.exam_type,
            'year': self.year,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
        }
    
    @property
    def status_display(self):
        """状态显示名称"""
        status_map = {
            'preparing': '筹备中',
            'recruiting': '招生中',
            'ended': '已结束'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def exam_type_display(self):
        """考试类型显示名称"""
        type_map = {
            'civil': '国省考',
            'career': '事业编'
        }
        return type_map.get(self.exam_type, self.exam_type)


class Package(db.Model):
    """
    报名套餐模型
    
    管理报名套餐，如"全程班"、"暑假班"等
    """
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='所属项目')
    name = db.Column(db.String(50), nullable=False, comment='套餐名称')
    package_type = db.Column(db.String(20), nullable=False, comment='类型(full/period/single_type/single_subject)')
    price = db.Column(db.Numeric(10, 2), nullable=False, comment='原价')
    valid_days = db.Column(db.Integer, comment='有效天数(全程班)')
    valid_start = db.Column(db.Date, comment='有效期开始(期限班)')
    valid_end = db.Column(db.Date, comment='有效期结束(期限班)')
    include_all_types = db.Column(db.Boolean, default=True, comment='是否包含所有班型')
    included_type_ids = db.Column(db.String(200), comment='包含的班型ID(逗号分隔)')
    discount_rules = db.Column(db.Text, comment='优惠规则(JSON)')
    description = db.Column(db.Text, comment='套餐说明')
    status = db.Column(db.String(10), default='active', comment='状态(active/inactive)')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<Package {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'package_type': self.package_type,
            'price': float(self.price) if self.price else 0,
            'valid_days': self.valid_days,
            'status': self.status,
        }
    
    @property
    def package_type_display(self):
        """套餐类型显示名称"""
        type_map = {
            'full': '全程班',
            'period': '期限班',
            'single_type': '单班型',
            'single_subject': '单科目'
        }
        return type_map.get(self.package_type, self.package_type)
    
    def get_discount_rules(self):
        """获取优惠规则"""
        if self.discount_rules:
            try:
                return json.loads(self.discount_rules)
            except:
                return {}
        return {}
    
    def set_discount_rules(self, rules):
        """设置优惠规则"""
        self.discount_rules = json.dumps(rules, ensure_ascii=False)
    
    def get_included_type_ids(self):
        """获取包含的班型ID列表"""
        if self.included_type_ids:
            return [int(x) for x in self.included_type_ids.split(',') if x.strip()]
        return []
    
    def set_included_type_ids(self, type_ids):
        """设置包含的班型ID"""
        self.included_type_ids = ','.join(str(x) for x in type_ids)


class ClassType(db.Model):
    """
    班型模型
    
    管理班型，如"基础班"、"提高班"、"刷题班"、"冲刺班"
    """
    __tablename__ = 'class_types'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='所属项目')
    name = db.Column(db.String(50), nullable=False, comment='班型名称')
    planned_days = db.Column(db.Integer, comment='计划天数')
    single_price = db.Column(db.Numeric(10, 2), comment='单独售价')
    sort_order = db.Column(db.Integer, default=0, comment='顺序')
    description = db.Column(db.Text, comment='班型说明')
    status = db.Column(db.String(10), default='active', comment='状态(active/inactive)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    batches = db.relationship('ClassBatch', backref='class_type', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ClassType {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'planned_days': self.planned_days,
            'single_price': float(self.single_price) if self.single_price else None,
            'sort_order': self.sort_order,
            'status': self.status,
        }


class ClassBatch(db.Model):
    """
    班次模型
    
    管理具体的班次（期数），如"基础班一期"、"基础班二期"
    """
    __tablename__ = 'class_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    class_type_id = db.Column(db.Integer, db.ForeignKey('class_types.id'), nullable=False, comment='所属班型')
    name = db.Column(db.String(50), nullable=False, comment='班次名称')
    batch_number = db.Column(db.Integer, nullable=False, comment='期数')
    start_date = db.Column(db.Date, nullable=False, comment='开课日期')
    end_date = db.Column(db.Date, nullable=False, comment='结课日期')
    actual_days = db.Column(db.Integer, comment='实际天数')
    max_students = db.Column(db.Integer, comment='招生上限')
    enrolled_count = db.Column(db.Integer, default=0, comment='已报人数')
    classroom = db.Column(db.String(50), comment='教室')
    status = db.Column(db.String(20), default='recruiting', comment='状态(recruiting/ongoing/ended)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    schedules = db.relationship('Schedule', backref='batch', lazy='dynamic', cascade='all, delete-orphan')
    student_batches = db.relationship('StudentBatch', backref='batch', lazy='dynamic', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='batch', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ClassBatch {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'class_type_id': self.class_type_id,
            'name': self.name,
            'batch_number': self.batch_number,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'actual_days': self.actual_days,
            'max_students': self.max_students,
            'enrolled_count': self.enrolled_count,
            'status': self.status,
        }
    
    @property
    def status_display(self):
        """状态显示名称"""
        status_map = {
            'recruiting': '招生中',
            'ongoing': '进行中',
            'ended': '已结课'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def is_full(self):
        """是否已满"""
        if self.max_students:
            return self.enrolled_count >= self.max_students
        return False
    
    def update_enrolled_count(self):
        """更新已报人数"""
        self.enrolled_count = self.student_batches.filter_by(status='active').count()
        return self.enrolled_count


class Schedule(db.Model):
    """
    课表模型
    
    管理班次的具体课表，精确到每天的科目和老师安排
    """
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('class_batches.id'), nullable=False, comment='所属班次')
    schedule_date = db.Column(db.Date, nullable=False, comment='上课日期')
    day_number = db.Column(db.Integer, nullable=False, comment='第几天')
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, comment='科目')
    morning_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), comment='上午老师')
    afternoon_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), comment='下午老师')
    evening_type = db.Column(db.String(20), default='self_study', comment='晚间类型(self_study/exercise/class)')
    evening_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), comment='晚间老师')
    remark = db.Column(db.String(200), comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    morning_teacher = db.relationship('Teacher', foreign_keys=[morning_teacher_id], backref='morning_schedules')
    afternoon_teacher = db.relationship('Teacher', foreign_keys=[afternoon_teacher_id], backref='afternoon_schedules')
    evening_teacher = db.relationship('Teacher', foreign_keys=[evening_teacher_id], backref='evening_schedules')
    change_logs = db.relationship('ScheduleChangeLog', backref='schedule', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Schedule {self.schedule_date} Day{self.day_number}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'schedule_date': self.schedule_date.isoformat() if self.schedule_date else None,
            'day_number': self.day_number,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'morning_teacher_id': self.morning_teacher_id,
            'morning_teacher_name': self.morning_teacher.name if self.morning_teacher else None,
            'afternoon_teacher_id': self.afternoon_teacher_id,
            'afternoon_teacher_name': self.afternoon_teacher.name if self.afternoon_teacher else None,
            'evening_type': self.evening_type,
            'remark': self.remark,
        }
    
    @property
    def evening_type_display(self):
        """晚间类型显示名称"""
        type_map = {
            'self_study': '自习',
            'exercise': '习题',
            'class': '上课'
        }
        return type_map.get(self.evening_type, self.evening_type)


class ScheduleChangeLog(db.Model):
    """
    课表变更记录模型
    
    记录课表变更历史，包括换老师、调课等
    """
    __tablename__ = 'schedule_change_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False, comment='关联课表')
    change_type = db.Column(db.String(20), nullable=False, comment='变更类型(teacher_change/reschedule/cancel)')
    original_value = db.Column(db.Text, nullable=False, comment='原值(JSON)')
    new_value = db.Column(db.Text, nullable=False, comment='新值(JSON)')
    reason = db.Column(db.String(200), comment='变更原因')
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='操作人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='变更时间')
    
    # 关系
    operator = db.relationship('User', backref='schedule_changes')
    
    def __repr__(self):
        return f'<ScheduleChangeLog {self.change_type} at {self.created_at}>'
    
    def get_original_value(self):
        """获取原值"""
        if self.original_value:
            try:
                return json.loads(self.original_value)
            except:
                return {}
        return {}
    
    def get_new_value(self):
        """获取新值"""
        if self.new_value:
            try:
                return json.loads(self.new_value)
            except:
                return {}
        return {}
    
    @property
    def change_type_display(self):
        """变更类型显示名称"""
        type_map = {
            'teacher_change': '换老师',
            'reschedule': '调课',
            'cancel': '取消'
        }
        return type_map.get(self.change_type, self.change_type)


class StudentBatch(db.Model):
    """
    学员班次关联模型
    
    学员与班次的多对多关联表
    """
    __tablename__ = 'student_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员')
    batch_id = db.Column(db.Integer, db.ForeignKey('class_batches.id'), nullable=False, comment='班次')
    enroll_time = db.Column(db.DateTime, default=datetime.utcnow, comment='加入时间')
    status = db.Column(db.String(20), default='active', comment='状态(active/completed/dropped)')
    progress_day = db.Column(db.Integer, default=0, comment='当前进度(第几天)')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('student_id', 'batch_id', name='uq_student_batch'),
    )
    
    # 关系
    student = db.relationship('Student', backref=db.backref('student_batches', lazy='dynamic'))
    
    def __repr__(self):
        return f'<StudentBatch student={self.student_id} batch={self.batch_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'batch_id': self.batch_id,
            'enroll_time': self.enroll_time.isoformat() if self.enroll_time else None,
            'status': self.status,
            'progress_day': self.progress_day,
        }
    
    @property
    def status_display(self):
        """状态显示名称"""
        status_map = {
            'active': '在学',
            'completed': '已完成',
            'dropped': '退出'
        }
        return status_map.get(self.status, self.status)


class Attendance(db.Model):
    """
    考勤模型
    
    记录学员签到和缺课情况
    """
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员')
    batch_id = db.Column(db.Integer, db.ForeignKey('class_batches.id'), nullable=False, comment='班次')
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False, comment='课表')
    attendance_date = db.Column(db.Date, nullable=False, comment='日期')
    status = db.Column(db.String(20), nullable=False, comment='状态(present/absent/late/leave)')
    check_in_time = db.Column(db.Time, comment='签到时间')
    remark = db.Column(db.String(200), comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    student = db.relationship('Student', backref=db.backref('attendances', lazy='dynamic'))
    schedule = db.relationship('Schedule', backref='attendances')
    
    def __repr__(self):
        return f'<Attendance {self.attendance_date} {self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'batch_id': self.batch_id,
            'schedule_id': self.schedule_id,
            'attendance_date': self.attendance_date.isoformat() if self.attendance_date else None,
            'status': self.status,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
        }
    
    @property
    def status_display(self):
        """状态显示名称"""
        status_map = {
            'present': '出勤',
            'absent': '缺勤',
            'late': '迟到',
            'leave': '请假'
        }
        return status_map.get(self.status, self.status)


class CourseRecording(db.Model):
    """
    课程录播模型
    
    记录腾讯会议等平台的课程录播链接
    """
    __tablename__ = 'course_recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('class_batches.id'), nullable=False, comment='所属班次')
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), comment='关联课表(可选)')
    recording_date = db.Column(db.Date, nullable=False, comment='录播日期')
    period = db.Column(db.String(20), nullable=False, default='morning', comment='时段(morning/afternoon/evening)')
    title = db.Column(db.String(200), nullable=False, comment='录播标题')
    recording_url = db.Column(db.String(500), nullable=False, comment='录播链接')
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), comment='科目')
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), comment='授课老师')
    duration_minutes = db.Column(db.Integer, comment='时长(分钟)')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    batch = db.relationship('ClassBatch', backref=db.backref('recordings', lazy='dynamic'))
    schedule = db.relationship('Schedule', backref=db.backref('recordings', lazy='dynamic'))
    subject = db.relationship('Subject', backref='recordings')
    teacher = db.relationship('Teacher', backref='recordings')
    creator = db.relationship('User', backref='created_recordings')
    
    def __repr__(self):
        return f'<CourseRecording {self.title} {self.recording_date}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'batch_name': self.batch.name if self.batch else None,
            'schedule_id': self.schedule_id,
            'recording_date': self.recording_date.isoformat() if self.recording_date else None,
            'period': self.period,
            'period_display': self.period_display,
            'title': self.title,
            'recording_url': self.recording_url,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'duration_minutes': self.duration_minutes,
            'duration_display': self.duration_display,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def period_display(self):
        """时段显示名称"""
        period_map = {
            'morning': '上午',
            'afternoon': '下午',
            'evening': '晚间'
        }
        return period_map.get(self.period, self.period)
    
    @property
    def duration_display(self):
        """时长显示"""
        if not self.duration_minutes:
            return '-'
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f'{hours}小时{minutes}分钟' if minutes > 0 else f'{hours}小时'
        return f'{minutes}分钟'
