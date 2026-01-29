"""
学习计划模型 - 个性化学习计划、目标和任务管理
"""
from datetime import datetime
import json
from app import db


class PlanTemplate(db.Model):
    """
    计划模板模型
    
    预设常用学习计划模板，支持批量创建学员计划
    """
    __tablename__ = 'plan_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='模板名称')
    phase = db.Column(db.String(20), default='foundation', comment='阶段: foundation/improvement/sprint')
    duration_days = db.Column(db.Integer, default=30, comment='持续天数')
    description = db.Column(db.Text, comment='模板描述')
    goals_template = db.Column(db.Text, comment='目标模板(JSON)')
    tasks_template = db.Column(db.Text, comment='任务模板(JSON)')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    creator = db.relationship('User', backref=db.backref('plan_templates', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PlanTemplate {self.name}>'
    
    @property
    def phase_display(self):
        """阶段显示名称"""
        phase_map = {
            'foundation': '基础阶段',
            'improvement': '提高阶段',
            'sprint': '冲刺阶段'
        }
        return phase_map.get(self.phase, self.phase)
    
    @property
    def goals_list(self):
        """解析目标模板JSON"""
        if self.goals_template:
            try:
                return json.loads(self.goals_template)
            except:
                return []
        return []
    
    @property
    def tasks_list(self):
        """解析任务模板JSON"""
        if self.tasks_template:
            try:
                return json.loads(self.tasks_template)
            except:
                return []
        return []
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'phase': self.phase,
            'phase_display': self.phase_display,
            'duration_days': self.duration_days,
            'description': self.description,
            'goals_template': self.goals_list,
            'tasks_template': self.tasks_list,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class StudyPlan(db.Model):
    """
    学习计划模型
    
    为学员创建个性化的学习计划
    """
    __tablename__ = 'study_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    name = db.Column(db.String(100), nullable=False, comment='计划名称')
    phase = db.Column(db.String(20), default='foundation', comment='阶段: foundation/improvement/sprint')
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, comment='结束日期')
    status = db.Column(db.String(20), default='active', comment='状态: active/completed/paused')
    ai_suggestion = db.Column(db.Text, comment='AI生成的建议(JSON)')
    notes = db.Column(db.Text, comment='督学备注')
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    student = db.relationship('Student', backref=db.backref('study_plans', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_plans', lazy='dynamic'))
    goals = db.relationship('PlanGoal', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('PlanTask', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    progress_records = db.relationship('PlanProgress', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudyPlan {self.name}>'
    
    @property
    def phase_display(self):
        """阶段显示名称"""
        phase_map = {
            'foundation': '基础阶段',
            'improvement': '提高阶段',
            'sprint': '冲刺阶段'
        }
        return phase_map.get(self.phase, self.phase)
    
    @property
    def status_display(self):
        """状态显示名称"""
        status_map = {
            'active': '进行中',
            'completed': '已完成',
            'paused': '已暂停'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def goal_progress(self):
        """目标完成进度"""
        total = self.goals.count()
        if total == 0:
            return 0
        achieved = self.goals.filter_by(status='achieved').count()
        return round(achieved / total * 100)
    
    @property
    def task_progress(self):
        """任务完成进度"""
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter_by(is_completed=True).count()
        return round(completed / total * 100)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'name': self.name,
            'phase': self.phase,
            'phase_display': self.phase_display,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'status_display': self.status_display,
            'goal_progress': self.goal_progress,
            'task_progress': self.task_progress,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PlanGoal(db.Model):
    """
    阶段目标模型
    
    记录计划中的阶段性目标
    """
    __tablename__ = 'plan_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False, comment='所属计划ID')
    goal_type = db.Column(db.String(20), nullable=False, comment='类型: accuracy/quantity/time')
    module = db.Column(db.String(50), comment='模块: 资料分析/言语理解等')
    description = db.Column(db.String(200), nullable=False, comment='目标描述')
    target_value = db.Column(db.Float, nullable=False, comment='目标值')
    current_value = db.Column(db.Float, default=0, comment='当前值')
    unit = db.Column(db.String(20), default='%', comment='单位: %/套/分钟')
    deadline = db.Column(db.Date, comment='截止日期')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/achieved/failed')
    achieved_at = db.Column(db.DateTime, comment='达成时间')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<PlanGoal {self.description}>'
    
    @property
    def goal_type_display(self):
        """目标类型显示"""
        type_map = {
            'accuracy': '正确率',
            'quantity': '数量',
            'time': '时间'
        }
        return type_map.get(self.goal_type, self.goal_type)
    
    @property
    def status_display(self):
        """状态显示"""
        status_map = {
            'pending': '进行中',
            'achieved': '已达成',
            'failed': '未达成'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def progress_percent(self):
        """进度百分比"""
        if self.target_value == 0:
            return 0
        return min(100, round(self.current_value / self.target_value * 100))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'goal_type': self.goal_type,
            'goal_type_display': self.goal_type_display,
            'module': self.module,
            'description': self.description,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'status_display': self.status_display,
            'progress_percent': self.progress_percent,
        }


class PlanTask(db.Model):
    """
    任务清单模型
    
    记录计划中的具体任务
    """
    __tablename__ = 'plan_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False, comment='所属计划ID')
    task_type = db.Column(db.String(20), default='daily', comment='类型: daily/weekly/milestone')
    title = db.Column(db.String(200), nullable=False, comment='任务标题')
    description = db.Column(db.Text, comment='任务描述')
    priority = db.Column(db.Integer, default=3, comment='优先级: 1-5')
    due_date = db.Column(db.Date, comment='截止日期')
    is_completed = db.Column(db.Boolean, default=False, comment='是否完成')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='完成确认人')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    completer = db.relationship('User', backref='completed_tasks')
    
    def __repr__(self):
        return f'<PlanTask {self.title}>'
    
    @property
    def task_type_display(self):
        """任务类型显示"""
        type_map = {
            'daily': '每日任务',
            'weekly': '每周任务',
            'milestone': '里程碑'
        }
        return type_map.get(self.task_type, self.task_type)
    
    @property
    def is_overdue(self):
        """是否逾期"""
        if self.is_completed or not self.due_date:
            return False
        from datetime import date
        return date.today() > self.due_date
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'task_type': self.task_type,
            'task_type_display': self.task_type_display,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue,
        }


class PlanProgress(db.Model):
    """
    进度记录模型
    
    记录计划执行过程中的评估和备注
    """
    __tablename__ = 'plan_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False, comment='所属计划ID')
    record_date = db.Column(db.Date, nullable=False, comment='记录日期')
    record_type = db.Column(db.String(20), default='evaluation', comment='类型: evaluation/note')
    content = db.Column(db.Text, nullable=False, comment='记录内容')
    overall_score = db.Column(db.Integer, comment='整体评分(1-5)')
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='记录人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    creator = db.relationship('User', backref='plan_progress_records')
    
    def __repr__(self):
        return f'<PlanProgress {self.record_date}>'
    
    @property
    def record_type_display(self):
        """记录类型显示"""
        type_map = {
            'evaluation': '阶段评估',
            'note': '备注'
        }
        return type_map.get(self.record_type, self.record_type)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'record_type': self.record_type,
            'record_type_display': self.record_type_display,
            'content': self.content,
            'overall_score': self.overall_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
