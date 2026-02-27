"""
数据模型 - 事业单位选岗系统
"""
from app.models.position import Position
from app.models.user import User, UserProfile
from app.models.favorite import Favorite
from app.models.recommendation import Recommendation

__all__ = [
    'Position',
    'User',
    'UserProfile',
    'Favorite',
    'Recommendation'
]
