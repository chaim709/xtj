"""
岗位仪表盘数据服务 - 统计分析和可视化数据聚合
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import func, case, and_, or_, desc
from app import db
from app.models.position import Position


class PositionDashboardService:
    """岗位仪表盘数据服务类"""
    
    @staticmethod
    def get_overview(year: int = 2026, exam_type: str = '省考', 
                     city: str = None) -> Dict[str, Any]:
        """
        获取总体概览数据
        
        Args:
            year: 年份
            exam_type: 考试类型
            city: 城市筛选（可选）
            
        Returns:
            概览统计数据
        """
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        
        if city:
            query = query.filter(Position.city == city)
        
        # 基础统计
        total_positions = query.count()
        
        # 招录总人数
        total_recruit = db.session.query(
            func.sum(Position.recruit_count)
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        if city:
            total_recruit = total_recruit.filter(Position.city == city)
        total_recruit = total_recruit.scalar() or 0
        
        # 平均竞争比（排除空值）
        avg_competition = db.session.query(
            func.avg(Position.competition_ratio)
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.competition_ratio.isnot(None)
        )
        if city:
            avg_competition = avg_competition.filter(Position.city == city)
        avg_competition = avg_competition.scalar() or 0
        
        # 平均进面分（排除空值）
        avg_entry_score = db.session.query(
            func.avg(Position.min_entry_score)
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.min_entry_score.isnot(None)
        )
        if city:
            avg_entry_score = avg_entry_score.filter(Position.city == city)
        avg_entry_score = avg_entry_score.scalar() or 0
        
        # 低竞争岗位数量（竞争比 < 20）
        low_competition_count = query.filter(
            Position.competition_ratio.isnot(None),
            Position.competition_ratio < 20
        ).count()
        
        return {
            'total_positions': total_positions,
            'total_recruit': int(total_recruit),
            'avg_competition': round(avg_competition, 1) if avg_competition else 0,
            'avg_entry_score': round(avg_entry_score, 1) if avg_entry_score else 0,
            'low_competition_count': low_competition_count,
        }
    
    @staticmethod
    def get_city_stats(year: int = 2026, exam_type: str = '省考') -> List[Dict]:
        """
        获取城市分布统计
        
        Returns:
            城市统计列表，按招录人数降序
        """
        results = db.session.query(
            Position.city,
            func.count(Position.id).label('position_count'),
            func.sum(Position.recruit_count).label('recruit_count'),
            func.avg(Position.competition_ratio).label('avg_competition'),
            func.avg(Position.min_entry_score).label('avg_entry_score'),
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.city.isnot(None)
        ).group_by(Position.city).order_by(
            desc('recruit_count')
        ).all()
        
        return [{
            'city': r.city,
            'position_count': r.position_count,
            'recruit_count': int(r.recruit_count or 0),
            'avg_competition': round(r.avg_competition, 1) if r.avg_competition else None,
            'avg_entry_score': round(r.avg_entry_score, 1) if r.avg_entry_score else None,
        } for r in results]
    
    @staticmethod
    def get_system_stats(year: int = 2026, exam_type: str = '省考',
                         city: str = None) -> List[Dict]:
        """
        获取系统类型分布统计
        
        Returns:
            系统类型统计列表
        """
        query = db.session.query(
            Position.system_type,
            func.count(Position.id).label('position_count'),
            func.sum(Position.recruit_count).label('recruit_count'),
            func.avg(Position.competition_ratio).label('avg_competition'),
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.system_type.isnot(None)
        )
        
        if city:
            query = query.filter(Position.city == city)
        
        results = query.group_by(Position.system_type).order_by(
            desc('recruit_count')
        ).all()
        
        return [{
            'system_type': r.system_type,
            'position_count': r.position_count,
            'recruit_count': int(r.recruit_count or 0),
            'avg_competition': round(r.avg_competition, 1) if r.avg_competition else None,
        } for r in results]
    
    @staticmethod
    def get_education_stats(year: int = 2026, exam_type: str = '省考',
                            city: str = None) -> List[Dict]:
        """
        获取学历分布统计
        
        Returns:
            学历统计列表
        """
        query = db.session.query(
            Position.education,
            func.count(Position.id).label('position_count'),
            func.sum(Position.recruit_count).label('recruit_count'),
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.education.isnot(None)
        )
        
        if city:
            query = query.filter(Position.city == city)
        
        results = query.group_by(Position.education).order_by(
            desc('position_count')
        ).all()
        
        return [{
            'education': r.education,
            'position_count': r.position_count,
            'recruit_count': int(r.recruit_count or 0),
        } for r in results]
    
    @staticmethod
    def get_competition_distribution(year: int = 2026, exam_type: str = '省考',
                                     city: str = None) -> Dict[str, Any]:
        """
        获取竞争比分布统计
        
        Returns:
            竞争比区间分布
        """
        base_filter = [
            Position.year == year,
            Position.exam_type == exam_type,
            Position.competition_ratio.isnot(None)
        ]
        
        if city:
            base_filter.append(Position.city == city)
        
        # 竞争比区间分布
        ranges = [
            ('< 20', 0, 20),
            ('20-50', 20, 50),
            ('50-100', 50, 100),
            ('> 100', 100, 99999),
        ]
        
        distribution = []
        for label, min_val, max_val in ranges:
            count = Position.query.filter(
                *base_filter,
                Position.competition_ratio >= min_val,
                Position.competition_ratio < max_val
            ).count()
            distribution.append({
                'range': label,
                'count': count,
                'min': min_val,
                'max': max_val
            })
        
        # 高竞争预警（竞争比 > 100 的岗位）
        high_competition = Position.query.filter(
            *base_filter,
            Position.competition_ratio > 100
        ).order_by(Position.competition_ratio.desc()).limit(10).all()
        
        return {
            'distribution': distribution,
            'high_competition_positions': [{
                'id': p.id,
                'department_name': p.department_name,
                'position_name': p.position_name,
                'city': p.city,
                'competition_ratio': p.competition_ratio,
                'recruit_count': p.recruit_count,
            } for p in high_competition]
        }
    
    @staticmethod
    def get_score_distribution(year: int = 2026, exam_type: str = '省考',
                               city: str = None) -> Dict[str, Any]:
        """
        获取进面分分布统计
        
        Returns:
            分数分布数据（用于箱线图和直方图）
        """
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.min_entry_score.isnot(None)
        )
        
        if city:
            query = query.filter(Position.city == city)
        
        positions = query.all()
        scores = [p.min_entry_score for p in positions if p.min_entry_score]
        
        if not scores:
            return {
                'histogram': [],
                'stats': {},
                'by_system': []
            }
        
        # 直方图数据（按分数段）
        ranges = [
            ('< 120', 0, 120),
            ('120-130', 120, 130),
            ('130-140', 130, 140),
            ('140-150', 140, 150),
            ('150-160', 150, 160),
            ('> 160', 160, 999),
        ]
        
        histogram = []
        for label, min_val, max_val in ranges:
            count = len([s for s in scores if min_val <= s < max_val])
            histogram.append({
                'range': label,
                'count': count
            })
        
        # 基础统计
        import statistics
        stats = {
            'min': min(scores),
            'max': max(scores),
            'mean': round(statistics.mean(scores), 1),
            'median': round(statistics.median(scores), 1),
            'count': len(scores)
        }
        
        # 按系统类型的分数分布（用于箱线图）
        base_filter = [
            Position.year == year,
            Position.exam_type == exam_type,
            Position.min_entry_score.isnot(None),
            Position.system_type.isnot(None)
        ]
        if city:
            base_filter.append(Position.city == city)
        
        by_system_query = db.session.query(
            Position.system_type,
            func.min(Position.min_entry_score).label('min_score'),
            func.max(Position.min_entry_score).label('max_score'),
            func.avg(Position.min_entry_score).label('avg_score'),
        ).filter(*base_filter).group_by(Position.system_type).all()
        
        by_system = [{
            'system_type': r.system_type,
            'min_score': round(r.min_score, 1) if r.min_score else None,
            'max_score': round(r.max_score, 1) if r.max_score else None,
            'avg_score': round(r.avg_score, 1) if r.avg_score else None,
        } for r in by_system_query]
        
        return {
            'histogram': histogram,
            'stats': stats,
            'by_system': by_system
        }
    
    @staticmethod
    def get_year_comparison(exam_type: str = '省考', 
                            city: str = None) -> List[Dict]:
        """
        获取年度对比数据
        
        Returns:
            多年份对比数据
        """
        years = [2024, 2025, 2026]
        comparison = []
        
        for year in years:
            query = Position.query.filter(
                Position.year == year,
                Position.exam_type == exam_type
            )
            if city:
                query = query.filter(Position.city == city)
            
            total_positions = query.count()
            
            # 招录人数
            recruit_count = db.session.query(
                func.sum(Position.recruit_count)
            ).filter(
                Position.year == year,
                Position.exam_type == exam_type
            )
            if city:
                recruit_count = recruit_count.filter(Position.city == city)
            recruit_count = recruit_count.scalar() or 0
            
            # 平均竞争比
            avg_competition = db.session.query(
                func.avg(Position.competition_ratio)
            ).filter(
                Position.year == year,
                Position.exam_type == exam_type,
                Position.competition_ratio.isnot(None)
            )
            if city:
                avg_competition = avg_competition.filter(Position.city == city)
            avg_competition = avg_competition.scalar()
            
            # 平均进面分
            avg_score = db.session.query(
                func.avg(Position.min_entry_score)
            ).filter(
                Position.year == year,
                Position.exam_type == exam_type,
                Position.min_entry_score.isnot(None)
            )
            if city:
                avg_score = avg_score.filter(Position.city == city)
            avg_score = avg_score.scalar()
            
            comparison.append({
                'year': year,
                'position_count': total_positions,
                'recruit_count': int(recruit_count),
                'avg_competition': round(avg_competition, 1) if avg_competition else None,
                'avg_entry_score': round(avg_score, 1) if avg_score else None,
            })
        
        return comparison
    
    @staticmethod
    def get_major_ranking(year: int = 2026, exam_type: str = '省考',
                          limit: int = 20) -> List[Dict]:
        """
        获取热门专业排行
        
        通过分析专业要求字段，统计出现频率最高的专业关键词
        
        Returns:
            专业热度排行
        """
        # 获取所有专业要求
        positions = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.major_requirement.isnot(None),
            Position.major_requirement != '不限'
        ).all()
        
        # 统计专业关键词
        major_counts = {}
        for p in positions:
            if not p.major_requirement:
                continue
            # 分割专业要求
            majors = p.major_requirement.replace('，', ',').replace('、', ',').split(',')
            for major in majors:
                major = major.strip()
                if major and len(major) >= 2 and major != '不限':
                    # 提取主要专业名（去除"类"等后缀之前的部分）
                    if '类' in major:
                        key = major.split('类')[0] + '类'
                    else:
                        key = major[:10]  # 截取前10个字符
                    
                    major_counts[key] = major_counts.get(key, 0) + 1
        
        # 排序
        sorted_majors = sorted(major_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{
            'major': major,
            'count': count
        } for major, count in sorted_majors]
    
    @staticmethod
    def get_low_competition_positions(year: int = 2026, exam_type: str = '省考',
                                      education: str = None, major: str = None,
                                      city: str = None, limit: int = 20) -> List[Dict]:
        """
        获取低竞争优质岗位推荐
        
        条件：竞争比 < 30，进面分有数据
        
        Returns:
            推荐岗位列表
        """
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.competition_ratio.isnot(None),
            Position.competition_ratio < 30,
            Position.min_entry_score.isnot(None)
        )
        
        if city:
            query = query.filter(Position.city == city)
        
        if education:
            query = query.filter(Position.education.contains(education))
        
        if major:
            query = query.filter(or_(
                Position.major_requirement.contains(major),
                Position.major_requirement.contains('不限')
            ))
        
        positions = query.order_by(
            Position.competition_ratio.asc(),
            Position.min_entry_score.asc()
        ).limit(limit).all()
        
        return [{
            'id': p.id,
            'city': p.city,
            'system_type': p.system_type,
            'department_name': p.department_name,
            'position_name': p.position_name,
            'education': p.education,
            'recruit_count': p.recruit_count,
            'competition_ratio': p.competition_ratio,
            'min_entry_score': p.min_entry_score,
            'major_requirement': p.major_requirement[:50] if p.major_requirement else None,
        } for p in positions]
    
    # ==================== 宿迁专项 ====================
    
    @staticmethod
    def get_suqian_overview(year: int = 2026, exam_type: str = '省考') -> Dict[str, Any]:
        """获取宿迁市整体概览"""
        return PositionDashboardService.get_overview(year, exam_type, city='宿迁市')
    
    @staticmethod
    def get_suqian_district_stats(year: int = 2026, exam_type: str = '省考') -> List[Dict]:
        """
        获取宿迁市各区县统计
        
        宿迁下辖：宿城区、宿豫区、沭阳县、泗阳县、泗洪县
        """
        # 获取宿迁相关岗位
        positions = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            or_(
                Position.city == '宿迁市',
                Position.region_name.contains('宿迁'),
                Position.region_name.contains('宿城'),
                Position.region_name.contains('宿豫'),
                Position.region_name.contains('沭阳'),
                Position.region_name.contains('泗阳'),
                Position.region_name.contains('泗洪'),
            )
        ).all()
        
        # 按区县统计
        district_map = {
            '宿城区': ['宿城', '宿城区'],
            '宿豫区': ['宿豫', '宿豫区'],
            '沭阳县': ['沭阳', '沭阳县'],
            '泗阳县': ['泗阳', '泗阳县'],
            '泗洪县': ['泗洪', '泗洪县'],
            '市直': ['宿迁市', '市直', '市级']
        }
        
        stats = {district: {
            'position_count': 0,
            'recruit_count': 0,
            'competition_ratios': [],
            'entry_scores': []
        } for district in district_map.keys()}
        
        for p in positions:
            matched_district = None
            search_text = (p.region_name or '') + (p.department_name or '')
            
            for district, keywords in district_map.items():
                if any(kw in search_text for kw in keywords):
                    matched_district = district
                    break
            
            if matched_district:
                stats[matched_district]['position_count'] += 1
                stats[matched_district]['recruit_count'] += (p.recruit_count or 1)
                if p.competition_ratio:
                    stats[matched_district]['competition_ratios'].append(p.competition_ratio)
                if p.min_entry_score:
                    stats[matched_district]['entry_scores'].append(p.min_entry_score)
        
        # 转换为列表格式
        result = []
        for district, data in stats.items():
            if data['position_count'] > 0:
                avg_comp = sum(data['competition_ratios']) / len(data['competition_ratios']) if data['competition_ratios'] else None
                avg_score = sum(data['entry_scores']) / len(data['entry_scores']) if data['entry_scores'] else None
                
                result.append({
                    'district': district,
                    'position_count': data['position_count'],
                    'recruit_count': data['recruit_count'],
                    'avg_competition': round(avg_comp, 1) if avg_comp else None,
                    'avg_entry_score': round(avg_score, 1) if avg_score else None,
                    'difficulty_level': 'high' if avg_comp and avg_comp > 40 else ('medium' if avg_comp and avg_comp > 25 else 'low')
                })
        
        # 按招录人数排序
        result.sort(key=lambda x: x['recruit_count'], reverse=True)
        
        return result
    
    @staticmethod
    def get_suqian_suggestions(year: int = 2026, exam_type: str = '省考') -> List[str]:
        """生成宿迁选岗建议"""
        district_stats = PositionDashboardService.get_suqian_district_stats(year, exam_type)
        
        suggestions = []
        
        # 找出竞争最小的区县
        if district_stats:
            low_comp = [d for d in district_stats if d.get('avg_competition')]
            if low_comp:
                low_comp.sort(key=lambda x: x['avg_competition'])
                best_district = low_comp[0]
                suggestions.append(f"{best_district['district']}竞争相对较小（平均{best_district['avg_competition']}:1），本地户籍有优势")
        
        # 找出岗位最多的区县
        if district_stats:
            most_positions = max(district_stats, key=lambda x: x['position_count'])
            if most_positions['position_count'] > 20:
                suggestions.append(f"{most_positions['district']}岗位最多（{most_positions['position_count']}个），选择面更广")
        
        # 检查是否有低竞争岗位
        low_competition = PositionDashboardService.get_low_competition_positions(
            year, exam_type, city='宿迁市', limit=5
        )
        if low_competition:
            suggestions.append(f"宿迁有{len(low_competition)}个低竞争优质岗位（竞争比<30）值得关注")
        
        return suggestions
    
    # ==================== 泗洪专项 ====================
    
    @staticmethod
    def get_sihong_overview(year: int = 2026, exam_type: str = '省考') -> Dict[str, Any]:
        """获取泗洪县整体概览"""
        positions = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            or_(
                Position.region_name.contains('泗洪'),
                Position.department_name.contains('泗洪'),
            )
        ).all()
        
        if not positions:
            return {
                'total_positions': 0,
                'total_recruit': 0,
                'avg_competition': 0,
                'avg_entry_score': 0
            }
        
        total_positions = len(positions)
        total_recruit = sum(p.recruit_count or 1 for p in positions)
        
        competitions = [p.competition_ratio for p in positions if p.competition_ratio]
        avg_competition = sum(competitions) / len(competitions) if competitions else 0
        
        scores = [p.min_entry_score for p in positions if p.min_entry_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_positions': total_positions,
            'total_recruit': total_recruit,
            'avg_competition': round(avg_competition, 1),
            'avg_entry_score': round(avg_score, 1)
        }
    
    @staticmethod
    def get_sihong_town_stats(year: int = 2026, exam_type: str = '省考') -> List[Dict]:
        """
        获取泗洪县乡镇/单位统计
        """
        positions = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type,
            or_(
                Position.region_name.contains('泗洪'),
                Position.department_name.contains('泗洪'),
            )
        ).order_by(Position.competition_ratio.asc().nullslast()).all()
        
        # 按单位分组
        dept_stats = {}
        for p in positions:
            dept = p.department_name or '其他'
            if dept not in dept_stats:
                dept_stats[dept] = {
                    'positions': [],
                    'recruit_count': 0,
                    'competition_ratios': [],
                    'entry_scores': []
                }
            
            dept_stats[dept]['positions'].append(p)
            dept_stats[dept]['recruit_count'] += (p.recruit_count or 1)
            if p.competition_ratio:
                dept_stats[dept]['competition_ratios'].append(p.competition_ratio)
            if p.min_entry_score:
                dept_stats[dept]['entry_scores'].append(p.min_entry_score)
        
        # 转换为列表
        result = []
        for dept, data in dept_stats.items():
            avg_comp = sum(data['competition_ratios']) / len(data['competition_ratios']) if data['competition_ratios'] else None
            avg_score = sum(data['entry_scores']) / len(data['entry_scores']) if data['entry_scores'] else None
            
            # 判断难度级别
            if avg_comp:
                if avg_comp > 40:
                    difficulty = '较难'
                elif avg_comp > 25:
                    difficulty = '中等'
                else:
                    difficulty = '推荐✓'
            else:
                difficulty = '未知'
            
            result.append({
                'department_name': dept,
                'position_count': len(data['positions']),
                'recruit_count': data['recruit_count'],
                'avg_competition': round(avg_comp, 1) if avg_comp else None,
                'avg_entry_score': round(avg_score, 1) if avg_score else None,
                'difficulty': difficulty,
                'positions': [{
                    'id': p.id,
                    'position_name': p.position_name,
                    'education': p.education,
                    'competition_ratio': p.competition_ratio,
                    'min_entry_score': p.min_entry_score,
                } for p in data['positions'][:3]]  # 最多显示3个岗位
            })
        
        # 按竞争比排序（低的在前）
        result.sort(key=lambda x: x['avg_competition'] or 999)
        
        return result
    
    @staticmethod
    def get_sihong_year_trend(exam_type: str = '省考') -> List[Dict]:
        """获取泗洪县近三年趋势"""
        years = [2024, 2025, 2026]
        trend = []
        
        for year in years:
            overview = PositionDashboardService.get_sihong_overview(year, exam_type)
            overview['year'] = year
            trend.append(overview)
        
        return trend
    
    @staticmethod
    def get_sihong_department_year_stats(exam_type: str = '省考') -> List[Dict]:
        """
        获取泗洪县各单位近三年招录数据对比
        
        Returns:
            各单位近三年招录数据
        """
        years = [2024, 2025, 2026]
        dept_year_data = {}
        
        for year in years:
            positions = Position.query.filter(
                Position.year == year,
                Position.exam_type == exam_type,
                or_(
                    Position.region_name.contains('泗洪'),
                    Position.department_name.contains('泗洪'),
                )
            ).all()
            
            for p in positions:
                dept = p.department_name or '其他'
                if dept not in dept_year_data:
                    dept_year_data[dept] = {
                        'department_name': dept,
                        'years': {2024: {'positions': 0, 'recruit': 0}, 
                                  2025: {'positions': 0, 'recruit': 0}, 
                                  2026: {'positions': 0, 'recruit': 0}},
                        'total_positions': 0,
                        'total_recruit': 0
                    }
                
                dept_year_data[dept]['years'][year]['positions'] += 1
                dept_year_data[dept]['years'][year]['recruit'] += (p.recruit_count or 1)
                dept_year_data[dept]['total_positions'] += 1
                dept_year_data[dept]['total_recruit'] += (p.recruit_count or 1)
        
        # 转换为列表并排序
        result = list(dept_year_data.values())
        result.sort(key=lambda x: x['total_recruit'], reverse=True)
        
        return result
    
    @staticmethod
    def get_suqian_district_year_stats(exam_type: str = '省考') -> List[Dict]:
        """
        获取宿迁市各区县近三年招录数据对比
        
        Returns:
            各区县近三年招录数据
        """
        years = [2024, 2025, 2026]
        district_map = {
            '宿城区': ['宿城', '宿城区'],
            '宿豫区': ['宿豫', '宿豫区'],
            '沭阳县': ['沭阳', '沭阳县'],
            '泗阳县': ['泗阳', '泗阳县'],
            '泗洪县': ['泗洪', '泗洪县'],
            '市直': ['宿迁市', '市直', '市级']
        }
        
        district_year_data = {district: {
            'district': district,
            'years': {2024: {'positions': 0, 'recruit': 0}, 
                      2025: {'positions': 0, 'recruit': 0}, 
                      2026: {'positions': 0, 'recruit': 0}},
            'total_positions': 0,
            'total_recruit': 0
        } for district in district_map.keys()}
        
        for year in years:
            positions = Position.query.filter(
                Position.year == year,
                Position.exam_type == exam_type,
                or_(
                    Position.city == '宿迁市',
                    Position.region_name.contains('宿迁'),
                    Position.region_name.contains('宿城'),
                    Position.region_name.contains('宿豫'),
                    Position.region_name.contains('沭阳'),
                    Position.region_name.contains('泗阳'),
                    Position.region_name.contains('泗洪'),
                )
            ).all()
            
            for p in positions:
                search_text = (p.region_name or '') + (p.department_name or '')
                
                for district, keywords in district_map.items():
                    if any(kw in search_text for kw in keywords):
                        district_year_data[district]['years'][year]['positions'] += 1
                        district_year_data[district]['years'][year]['recruit'] += (p.recruit_count or 1)
                        district_year_data[district]['total_positions'] += 1
                        district_year_data[district]['total_recruit'] += (p.recruit_count or 1)
                        break
        
        # 转换为列表并排序
        result = [d for d in district_year_data.values() if d['total_positions'] > 0]
        result.sort(key=lambda x: x['total_recruit'], reverse=True)
        
        return result
    
    @staticmethod
    def get_sihong_suggestions(year: int = 2026, exam_type: str = '省考') -> List[str]:
        """生成泗洪选岗策略建议"""
        town_stats = PositionDashboardService.get_sihong_town_stats(year, exam_type)
        year_trend = PositionDashboardService.get_sihong_year_trend(exam_type)
        
        suggestions = []
        
        # 分析乡镇vs县直机关
        town_positions = [t for t in town_stats if '乡' in t['department_name'] or '镇' in t['department_name'] or '街道' in t['department_name']]
        county_positions = [t for t in town_stats if '乡' not in t['department_name'] and '镇' not in t['department_name'] and '街道' not in t['department_name']]
        
        if town_positions and county_positions:
            town_avg = sum(t['avg_competition'] or 0 for t in town_positions) / len(town_positions) if any(t['avg_competition'] for t in town_positions) else 0
            county_avg = sum(t['avg_competition'] or 0 for t in county_positions) / len(county_positions) if any(t['avg_competition'] for t in county_positions) else 0
            
            if town_avg and county_avg:
                diff = county_avg - town_avg
                if diff > 5:
                    suggestions.append(f"乡镇岗位竞争明显低于县直机关，分数要求低约{int(diff)}分")
        
        # 分析年度趋势
        if len(year_trend) >= 2:
            recent = year_trend[-1]
            prev = year_trend[-2]
            
            if recent['total_positions'] > prev['total_positions']:
                suggestions.append(f"近年招录趋势向好，{recent['year']}年比{prev['year']}年多招{recent['total_positions'] - prev['total_positions']}个岗位")
            
            if recent['avg_competition'] and prev['avg_competition']:
                if recent['avg_competition'] < prev['avg_competition']:
                    suggestions.append(f"竞争逐年下降（{prev['avg_competition']}:1 → {recent['avg_competition']}:1），上岸机会增加")
        
        # 推荐低竞争单位
        low_comp_depts = [t for t in town_stats if t['avg_competition'] and t['avg_competition'] < 25]
        if low_comp_depts:
            dept_names = [t['department_name'][:6] for t in low_comp_depts[:3]]
            suggestions.append(f"低竞争单位推荐：{'、'.join(dept_names)}")
        
        return suggestions
    
    # ==================== 选岗视角专用 ====================
    
    @staticmethod
    def get_matching_positions_stats(year: int = 2026, exam_type: str = '省考',
                                     education: str = None, major: str = None) -> Dict[str, Any]:
        """
        获取匹配岗位的统计（选岗视角用）
        
        根据学历和专业条件，统计可报岗位数量和分布
        """
        query = Position.query.filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        
        # 学历匹配
        if education:
            education_conditions = []
            if education == '本科':
                education_conditions = ['本科及以上', '仅限本科', '大专及以上', '大专或本科', '不限']
            elif education == '研究生' or education == '硕士':
                education_conditions = ['研究生及以上', '仅限研究生', '硕士及以上', '本科及以上', '大专及以上', '不限']
            elif education == '专科':
                education_conditions = ['大专及以上', '大专或本科', '不限']
            
            if education_conditions:
                edu_filters = [Position.education.contains(e) for e in education_conditions]
                query = query.filter(or_(*edu_filters))
        
        # 专业匹配
        if major:
            query = query.filter(or_(
                Position.major_requirement.contains(major),
                Position.major_requirement.contains('不限')
            ))
        
        total_matching = query.count()
        
        # 低竞争岗位（<20）
        low_comp_query = query.filter(
            Position.competition_ratio.isnot(None),
            Position.competition_ratio < 20
        )
        low_competition_count = low_comp_query.count()
        
        # 按城市分布
        city_distribution = db.session.query(
            Position.city,
            func.count(Position.id).label('count')
        ).filter(
            Position.year == year,
            Position.exam_type == exam_type
        )
        
        if education:
            if education_conditions:
                edu_filters = [Position.education.contains(e) for e in education_conditions]
                city_distribution = city_distribution.filter(or_(*edu_filters))
        
        if major:
            city_distribution = city_distribution.filter(or_(
                Position.major_requirement.contains(major),
                Position.major_requirement.contains('不限')
            ))
        
        city_distribution = city_distribution.group_by(Position.city).all()
        
        return {
            'total_matching': total_matching,
            'low_competition_count': low_competition_count,
            'city_distribution': [{
                'city': c.city,
                'count': c.count
            } for c in city_distribution if c.city]
        }
