"""
督学记录模型 - 记录督学人员与学员的沟通内容
"""
from datetime import datetime
from app import db


class SupervisionLog(db.Model):
    """
    督学记录模型
    
    快速记录每次与学员沟通的内容，形成完整的督学轨迹
    """
    __tablename__ = 'supervision_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='督学人员ID')
    
    # 沟通信息
    contact_type = db.Column(db.String(20), comment='沟通方式(电话/微信/面谈)')
    contact_duration = db.Column(db.Integer, comment='沟通时长(分钟)')
    content = db.Column(db.Text, comment='沟通内容')
    
    # 学生状态评估
    student_mood = db.Column(db.String(20), comment='学生心态(积极/平稳/焦虑/低落)')
    study_status = db.Column(db.String(20), comment='学习状态(优秀/良好/一般/较差)')
    self_discipline = db.Column(db.String(20), comment='自律性(强/中/弱)')
    
    # 行动记录
    actions = db.Column(db.Text, comment='今日行动记录')
    next_follow_up_date = db.Column(db.Date, comment='下次跟进时间')
    
    # 快速标签（JSON格式存储）
    tags = db.Column(db.Text, comment='快速标签')
    
    # 记录日期
    log_date = db.Column(db.Date, nullable=False, default=datetime.utcnow, comment='记录日期')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    supervisor = db.relationship('User', backref=db.backref('supervision_logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SupervisionLog {self.student_id} - {self.log_date}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'supervisor_id': self.supervisor_id,
            'contact_type': self.contact_type,
            'contact_duration': self.contact_duration,
            'content': self.content,
            'student_mood': self.student_mood,
            'study_status': self.study_status,
            'next_follow_up_date': self.next_follow_up_date.isoformat() if self.next_follow_up_date else None,
            'log_date': self.log_date.isoformat() if self.log_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
