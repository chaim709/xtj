"""
老师模型 - 管理外聘老师信息
"""
from datetime import datetime
from app import db


class Teacher(db.Model):
    """
    老师模型
    
    管理外聘老师信息，包括排课和薪资
    """
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    phone = db.Column(db.String(20), nullable=False, comment='手机')
    subject_ids = db.Column(db.String(100), nullable=False, comment='擅长科目ID(逗号分隔)')
    daily_rate = db.Column(db.Numeric(10, 2), comment='日薪')
    hourly_rate = db.Column(db.Numeric(10, 2), comment='课时费')
    id_card = db.Column(db.String(20), comment='身份证号')
    bank_account = db.Column(db.String(50), comment='银行账号')
    bank_name = db.Column(db.String(50), comment='开户行')
    remark = db.Column(db.Text, comment='备注')
    status = db.Column(db.String(10), default='active', comment='状态(active/inactive)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<Teacher {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'subject_ids': self.subject_ids,
            'daily_rate': float(self.daily_rate) if self.daily_rate else None,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'status': self.status,
        }
    
    def get_subject_ids(self):
        """获取擅长科目ID列表"""
        if self.subject_ids:
            return [int(x) for x in self.subject_ids.split(',') if x.strip()]
        return []
    
    def set_subject_ids(self, subject_ids):
        """设置擅长科目ID"""
        self.subject_ids = ','.join(str(x) for x in subject_ids)
    
    def get_subjects(self):
        """获取擅长科目列表"""
        from app.models.course import Subject
        ids = self.get_subject_ids()
        if ids:
            return Subject.query.filter(Subject.id.in_(ids)).all()
        return []
    
    @property
    def subjects_display(self):
        """擅长科目显示"""
        subjects = self.get_subjects()
        if subjects:
            return '、'.join(s.short_name or s.name for s in subjects)
        return ''
    
    def has_schedule_on_date(self, check_date):
        """
        检查老师在指定日期是否有排课
        
        Args:
            check_date: 日期
        
        Returns:
            bool: 是否有排课
        """
        from app.models.course import Schedule
        count = Schedule.query.filter(
            Schedule.schedule_date == check_date,
            db.or_(
                Schedule.morning_teacher_id == self.id,
                Schedule.afternoon_teacher_id == self.id,
                Schedule.evening_teacher_id == self.id
            )
        ).count()
        return count > 0
    
    def get_schedules_on_date(self, check_date):
        """
        获取老师在指定日期的排课
        
        Args:
            check_date: 日期
        
        Returns:
            List[Schedule]: 排课列表
        """
        from app.models.course import Schedule
        return Schedule.query.filter(
            Schedule.schedule_date == check_date,
            db.or_(
                Schedule.morning_teacher_id == self.id,
                Schedule.afternoon_teacher_id == self.id,
                Schedule.evening_teacher_id == self.id
            )
        ).all()
    
    def get_all_schedules(self, start_date=None, end_date=None):
        """
        获取老师的所有排课
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        
        Returns:
            List[Schedule]: 排课列表
        """
        from app.models.course import Schedule
        query = Schedule.query.filter(
            db.or_(
                Schedule.morning_teacher_id == self.id,
                Schedule.afternoon_teacher_id == self.id,
                Schedule.evening_teacher_id == self.id
            )
        )
        
        if start_date:
            query = query.filter(Schedule.schedule_date >= start_date)
        if end_date:
            query = query.filter(Schedule.schedule_date <= end_date)
        
        return query.order_by(Schedule.schedule_date).all()
    
    def calculate_workload(self, start_date, end_date):
        """
        计算老师工作量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {
                'total_days': int,
                'morning_count': int,
                'afternoon_count': int,
                'evening_count': int,
                'total_amount': Decimal
            }
        """
        from app.models.course import Schedule
        from decimal import Decimal
        
        schedules = self.get_all_schedules(start_date, end_date)
        
        # 统计各时段
        morning_count = sum(1 for s in schedules if s.morning_teacher_id == self.id)
        afternoon_count = sum(1 for s in schedules if s.afternoon_teacher_id == self.id)
        evening_count = sum(1 for s in schedules if s.evening_teacher_id == self.id)
        
        # 计算总天数（去重日期）
        dates = set(s.schedule_date for s in schedules)
        total_days = len(dates)
        
        # 计算薪资（按日薪计算）
        total_amount = Decimal('0')
        if self.daily_rate:
            total_amount = self.daily_rate * total_days
        
        return {
            'total_days': total_days,
            'morning_count': morning_count,
            'afternoon_count': afternoon_count,
            'evening_count': evening_count,
            'total_amount': total_amount
        }
