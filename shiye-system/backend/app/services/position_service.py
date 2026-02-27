"""
岗位服务 - 岗位查询和管理
"""
from typing import List, Dict, Tuple
from sqlalchemy import or_, and_, func
from app.models.position import Position
from app import db


class PositionService:
    """岗位服务类"""
    
    @staticmethod
    def search_positions(filters: dict, page: int = 1, per_page: int = 20) -> Tuple[List[Position], int]:
        """
        搜索岗位
        
        Args:
            filters: 筛选条件字典
            page: 页码
            per_page: 每页数量
        
        Returns:
            (岗位列表, 总数)
        """
        query = Position.query.filter(Position.year == filters.get('year', 2026))
        
        # 城市筛选
        if filters.get('city'):
            query = query.filter(Position.city == filters['city'])
        
        # 系统类型筛选
        if filters.get('system_type'):
            query = query.filter(Position.system_type == filters['system_type'])
        
        # 学历筛选
        if filters.get('education'):
            query = query.filter(Position.education.contains(filters['education']))
        
        # 考试类别筛选
        if filters.get('exam_category'):
            query = query.filter(Position.exam_category == filters['exam_category'])
        
        # 单位名称搜索
        if filters.get('department_name'):
            query = query.filter(Position.department_name.contains(filters['department_name']))
        
        # 岗位名称搜索
        if filters.get('position_name'):
            query = query.filter(Position.position_name.contains(filters['position_name']))
        
        # 专业搜索
        if filters.get('major'):
            query = query.filter(Position.major_requirement.contains(filters['major']))
        
        # 关键词搜索（搜索所有文本字段）
        if filters.get('keyword'):
            keyword = filters['keyword']
            query = query.filter(or_(
                Position.department_name.contains(keyword),
                Position.position_name.contains(keyword),
                Position.major_requirement.contains(keyword),
                Position.other_requirements.contains(keyword)
            ))
        
        # 竞争度筛选
        if filters.get('difficulty'):
            query = query.filter(Position.difficulty_level == filters['difficulty'])
        
        # 排序
        sort_by = filters.get('sort_by', 'recommendation_score')
        sort_order = filters.get('sort_order', 'desc')
        
        if sort_by == 'competition_ratio':
            order_col = Position.estimated_competition_ratio.asc() if sort_order == 'asc' else Position.estimated_competition_ratio.desc()
        elif sort_by == 'recruit_count':
            order_col = Position.recruit_count.desc() if sort_order == 'desc' else Position.recruit_count.asc()
        elif sort_by == 'salary':
            order_col = Position.estimated_salary.desc().nullslast() if sort_order == 'desc' else Position.estimated_salary.asc().nullslast()
        else:
            order_col = Position.recommendation_score.desc().nullslast()
        
        query = query.order_by(order_col)
        
        # 分页
        total = query.count()
        positions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return positions, total
    
    @staticmethod
    def get_position_detail(position_id: int) -> Position:
        """获取岗位详情"""
        return Position.query.get_or_404(position_id)
    
    @staticmethod
    def get_statistics() -> dict:
        """获取统计数据"""
        return {
            'total_positions': Position.query.count(),
            'total_recruit': db.session.query(func.sum(Position.recruit_count)).scalar() or 0,
            'cities_count': db.session.query(func.count(func.distinct(Position.city))).scalar() or 0,
            'departments_count': db.session.query(func.count(func.distinct(Position.department_name))).scalar() or 0
        }
    
    @staticmethod
    def get_city_statistics() -> List[dict]:
        """获取城市统计"""
        results = db.session.query(
            Position.city,
            func.count(Position.id).label('position_count'),
            func.sum(Position.recruit_count).label('recruit_count')
        ).filter(
            Position.city.isnot(None)
        ).group_by(
            Position.city
        ).order_by(
            func.sum(Position.recruit_count).desc()
        ).all()
        
        return [{
            'city': r.city,
            'position_count': r.position_count,
            'recruit_count': r.recruit_count or 0
        } for r in results]
    
    @staticmethod
    def get_education_statistics() -> List[dict]:
        """获取学历统计"""
        results = db.session.query(
            Position.education,
            func.count(Position.id).label('count')
        ).filter(
            Position.education.isnot(None)
        ).group_by(
            Position.education
        ).order_by(
            func.count(Position.id).desc()
        ).all()
        
        return [{
            'education': r.education,
            'count': r.count
        } for r in results]
    
    @staticmethod
    def get_exam_category_statistics() -> List[dict]:
        """获取考试类别统计"""
        results = db.session.query(
            Position.exam_category,
            func.count(Position.id).label('count')
        ).filter(
            Position.exam_category.isnot(None)
        ).group_by(
            Position.exam_category
        ).order_by(
            func.count(Position.id).desc()
        ).all()
        
        return [{
            'category': r.exam_category,
            'count': r.count
        } for r in results]
