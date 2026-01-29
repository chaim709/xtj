"""
作业模型 - 作业任务和提交记录
"""
from datetime import datetime
from app import db


class HomeworkTask(db.Model):
    """
    作业任务模型
    
    督学人员发布的作业任务
    """
    __tablename__ = 'homework_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False, comment='作业名称')
    task_type = db.Column(db.String(20), comment='作业类型(专项练习/套卷/错题)')
    
    # 学习模块
    module = db.Column(db.String(50), comment='学习模块')
    sub_module = db.Column(db.String(100), comment='子模块')
    
    # 作业要求
    question_count = db.Column(db.Integer, comment='题量')
    suggested_time = db.Column(db.Integer, comment='建议用时(分钟)')
    deadline = db.Column(db.DateTime, comment='截止时间')
    
    # 目标对象
    target_class = db.Column(db.String(50), comment='目标班次')
    target_students = db.Column(db.Text, comment='目标学员ID(JSON数组)')
    
    # 作业说明
    description = db.Column(db.Text, comment='作业说明')
    
    # 创建人
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    
    # 发布信息
    publish_time = db.Column(db.DateTime, comment='发布时间')
    status = db.Column(db.String(20), default='published', comment='状态(draft/published/closed)')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    creator = db.relationship('User', backref=db.backref('created_tasks', lazy='dynamic'))
    submissions = db.relationship('HomeworkSubmission', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HomeworkTask {self.task_name}>'
    
    def get_statistics(self):
        """获取作业统计信息"""
        submissions = self.submissions.all()
        total_target = len(self.target_students.split(',')) if self.target_students else 0
        completed = len(submissions)
        
        if completed > 0:
            avg_rate = sum(s.accuracy_rate or 0 for s in submissions) / completed
            avg_time = sum(s.time_spent or 0 for s in submissions) / completed
        else:
            avg_rate = 0
            avg_time = 0
        
        return {
            'total_target': total_target,
            'completed': completed,
            'completion_rate': (completed / total_target * 100) if total_target > 0 else 0,
            'avg_accuracy_rate': avg_rate,
            'avg_time_spent': avg_time,
        }
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_type': self.task_type,
            'module': self.module,
            'question_count': self.question_count,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HomeworkSubmission(db.Model):
    """
    作业提交记录模型
    
    由督学人员录入学员的作业完成情况
    """
    __tablename__ = 'homework_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('homework_tasks.id'), nullable=False, comment='作业任务ID')
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    
    # 完成情况
    completed_count = db.Column(db.Integer, comment='完成题量')
    correct_count = db.Column(db.Integer, comment='正确数量')
    accuracy_rate = db.Column(db.Float, comment='正确率(%)')
    time_spent = db.Column(db.Integer, comment='实际用时(分钟)')
    
    # 错题记录
    wrong_questions = db.Column(db.Text, comment='错题编号(JSON数组)')
    
    # 反馈
    feedback = db.Column(db.Text, comment='学员反馈/备注')
    
    # 提交信息
    submit_time = db.Column(db.DateTime, default=datetime.utcnow, comment='提交时间')
    is_late = db.Column(db.Boolean, default=False, comment='是否逾期')
    
    # 录入人
    recorder_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='录入人ID')
    
    # 状态
    status = db.Column(db.String(20), default='submitted', comment='状态(submitted/reviewed)')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    recorder = db.relationship('User', backref=db.backref('recorded_submissions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<HomeworkSubmission task={self.task_id} student={self.student_id}>'
    
    def calculate_accuracy(self):
        """计算正确率"""
        if self.completed_count and self.completed_count > 0:
            self.accuracy_rate = (self.correct_count / self.completed_count) * 100
        else:
            self.accuracy_rate = 0
        return self.accuracy_rate
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'student_id': self.student_id,
            'completed_count': self.completed_count,
            'correct_count': self.correct_count,
            'accuracy_rate': self.accuracy_rate,
            'time_spent': self.time_spent,
            'submit_time': self.submit_time.isoformat() if self.submit_time else None,
            'is_late': self.is_late,
        }
