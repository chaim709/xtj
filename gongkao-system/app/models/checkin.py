# -*- coding: utf-8 -*-
"""
打卡记录模型
"""
from datetime import datetime
from app import db


class CheckinRecord(db.Model):
    """
    打卡记录模型
    
    记录学员的每日打卡历史
    """
    __tablename__ = 'checkin_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    checkin_date = db.Column(db.Date, nullable=False, comment='打卡日期')
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow, comment='打卡时间')
    study_minutes = db.Column(db.Integer, default=0, comment='学习时长(分钟)')
    note = db.Column(db.Text, comment='打卡备注')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('student_id', 'checkin_date', name='uq_student_checkin_date'),
    )
    
    # 关系
    student = db.relationship('Student', backref=db.backref('checkin_records', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CheckinRecord {self.student_id} {self.checkin_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'checkinDate': self.checkin_date.isoformat() if self.checkin_date else None,
            'checkinTime': self.checkin_time.isoformat() if self.checkin_time else None,
            'studyMinutes': self.study_minutes,
            'note': self.note
        }
