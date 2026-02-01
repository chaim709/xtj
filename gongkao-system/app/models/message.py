# -*- coding: utf-8 -*-
"""
学员消息模型
"""
from datetime import datetime
from app import db


class StudentMessage(db.Model):
    """
    学员消息模型
    
    存储推送给学员的各类消息
    """
    __tablename__ = 'student_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    message_type = db.Column(db.String(50), nullable=False, comment='消息类型(supervision/homework/system)')
    title = db.Column(db.String(200), nullable=False, comment='消息标题')
    content = db.Column(db.Text, comment='消息内容')
    source_type = db.Column(db.String(50), comment='来源类型')
    source_id = db.Column(db.Integer, comment='来源ID')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    read_at = db.Column(db.DateTime, comment='阅读时间')
    
    # 关系
    student = db.relationship('Student', backref=db.backref('messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<StudentMessage {self.id} {self.message_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'type': self.message_type,
            'title': self.title,
            'content': self.content,
            'isRead': self.is_read,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_as_read(self):
        """标记为已读"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()


class WxSubscribeTemplate(db.Model):
    """
    微信订阅消息模板
    """
    __tablename__ = 'wx_subscribe_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.String(100), nullable=False, comment='微信模板ID')
    template_type = db.Column(db.String(50), nullable=False, comment='模板类型(class_reminder/homework_reminder)')
    title = db.Column(db.String(100), comment='模板标题')
    description = db.Column(db.Text, comment='模板描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<WxSubscribeTemplate {self.template_type}>'
