"""
推荐记录模型 - Recommendation
"""
from datetime import datetime
from app import db


class Recommendation(db.Model):
    """推荐记录表"""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, index=True)
    
    # 评分信息
    total_score = db.Column(db.Float)  # 综合评分 (0-100)
    landing_probability = db.Column(db.Float)  # 上岸概率 (0-100)
    
    # 分项评分
    probability_score = db.Column(db.Float)  # 上岸概率分
    salary_score = db.Column(db.Float)  # 待遇水平分
    development_score = db.Column(db.Float)  # 发展空间分
    life_quality_score = db.Column(db.Float)  # 生活质量分
    overall_rating_score = db.Column(db.Float)  # 综合评价分
    
    # 推荐类型
    recommendation_type = db.Column(db.String(20))  # 冲刺型/稳妥型/保底型
    
    # 匹配度分析
    education_match = db.Column(db.String(20))  # 学历匹配度
    major_match = db.Column(db.String(20))  # 专业匹配度
    location_match = db.Column(db.String(20))  # 地域匹配度
    
    # 推荐原因
    reasons = db.Column(db.Text)  # JSON格式的推荐理由
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Recommendation user_id={self.user_id} position_id={self.position_id} type={self.recommendation_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'position_id': self.position_id,
            'total_score': round(self.total_score, 2) if self.total_score else 0,
            'landing_probability': round(self.landing_probability, 2) if self.landing_probability else 0,
            'recommendation_type': self.recommendation_type,
            'education_match': self.education_match,
            'major_match': self.major_match,
            'location_match': self.location_match,
            'reasons': self.reasons,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
