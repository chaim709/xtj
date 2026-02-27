"""
收藏模型 - Favorite
"""
from datetime import datetime
from app import db


class Favorite(db.Model):
    """岗位收藏表"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, index=True)
    
    # 用户笔记
    note = db.Column(db.Text)
    
    # 标签
    tags = db.Column(db.String(200))  # JSON格式：["冲刺型", "待遇好"]
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'position_id', name='uix_user_position'),
    )
    
    def __repr__(self):
        return f'<Favorite user_id={self.user_id} position_id={self.position_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'position_id': self.position_id,
            'note': self.note,
            'tags': self.tags,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
