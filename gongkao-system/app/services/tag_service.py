"""
标签服务 - 薄弱项标签管理
"""
from datetime import datetime, date
from app import db
from app.models.tag import WeaknessTag, ModuleCategory


class TagService:
    """标签服务类"""
    
    # 默认模块分类
    DEFAULT_MODULES = {
        '常识判断': ['科技常识', '法律常识', '时事政治', '地理常识', '人文常识', '经济常识'],
        '言语理解': ['篇章阅读', '语句表达', '逻辑填空', '片段阅读'],
        '数量关系': ['行程问题', '经济利润问题', '比赛计数问题', '几何问题', '排列组合', '工程问题'],
        '判断推理': ['图形推理', '定义判断', '类比推理', '逻辑判断'],
        '资料分析': ['增长率计算', '比重问题', '平均数问题'],
        '申论': ['归纳概括', '综合分析', '提出对策', '贯彻执行', '申发论述'],
    }
    
    @staticmethod
    def add_tag(student_id, module, sub_module=None, accuracy_rate=None, level=None):
        """
        添加薄弱项标签
        
        Args:
            student_id: 学员ID
            module: 一级模块
            sub_module: 子模块
            accuracy_rate: 正确率
            level: 等级(red/yellow/green)，如果不提供则根据正确率计算
        
        Returns:
            创建的标签对象
        """
        # 计算等级
        if level is None and accuracy_rate is not None:
            level = WeaknessTag.get_level_from_rate(accuracy_rate)
        elif level is None:
            level = 'yellow'  # 默认黄色
        
        # 检查是否已存在相同标签
        existing = WeaknessTag.query.filter_by(
            student_id=student_id,
            module=module,
            sub_module=sub_module
        ).first()
        
        if existing:
            # 更新现有标签
            existing.accuracy_rate = accuracy_rate
            existing.level = level
            existing.practice_count += 1
            existing.last_practice_date = date.today()
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            return existing
        
        # 创建新标签
        tag = WeaknessTag(
            student_id=student_id,
            module=module,
            sub_module=sub_module,
            accuracy_rate=accuracy_rate,
            level=level,
            practice_count=1,
            last_practice_date=date.today()
        )
        db.session.add(tag)
        db.session.commit()
        return tag
    
    @staticmethod
    def update_tag(tag_id, data):
        """
        更新标签
        
        Args:
            tag_id: 标签ID
            data: 更新数据
        
        Returns:
            更新后的标签对象
        """
        tag = WeaknessTag.query.get(tag_id)
        if not tag:
            return None
        
        for key, value in data.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
        
        # 如果更新了正确率，重新计算等级
        if 'accuracy_rate' in data and data['accuracy_rate'] is not None:
            tag.level = WeaknessTag.get_level_from_rate(data['accuracy_rate'])
        
        tag.updated_at = datetime.utcnow()
        db.session.commit()
        return tag
    
    @staticmethod
    def delete_tag(tag_id):
        """
        删除标签
        
        Args:
            tag_id: 标签ID
        
        Returns:
            是否删除成功
        """
        tag = WeaknessTag.query.get(tag_id)
        if not tag:
            return False
        
        db.session.delete(tag)
        db.session.commit()
        return True
    
    @staticmethod
    def get_tags_by_student(student_id, level=None):
        """
        获取学员的所有标签
        
        Args:
            student_id: 学员ID
            level: 筛选等级
        
        Returns:
            标签列表
        """
        query = WeaknessTag.query.filter_by(student_id=student_id)
        if level:
            query = query.filter_by(level=level)
        return query.order_by(WeaknessTag.level.desc(), WeaknessTag.updated_at.desc()).all()
    
    @staticmethod
    def auto_tag_from_homework(student_id, module, sub_module, accuracy_rate):
        """
        根据作业完成情况自动打标签
        
        Args:
            student_id: 学员ID
            module: 模块
            sub_module: 子模块
            accuracy_rate: 正确率
        
        Returns:
            标签对象（如果正确率<70%才创建）
        """
        # 只有正确率低于70%才打标签
        if accuracy_rate >= 70:
            return None
        
        return TagService.add_tag(
            student_id=student_id,
            module=module,
            sub_module=sub_module,
            accuracy_rate=accuracy_rate
        )
    
    @staticmethod
    def mark_resolved(tag_id):
        """
        标记标签为已攻克
        
        Args:
            tag_id: 标签ID
        
        Returns:
            标签对象
        """
        tag = WeaknessTag.query.get(tag_id)
        if tag:
            tag.is_resolved = True
            tag.level = 'green'
            tag.updated_at = datetime.utcnow()
            db.session.commit()
        return tag
    
    @staticmethod
    def get_modules():
        """获取所有模块分类"""
        return TagService.DEFAULT_MODULES
    
    @staticmethod
    def init_module_categories():
        """初始化模块分类到数据库"""
        for level1, level2_list in TagService.DEFAULT_MODULES.items():
            for level2 in level2_list:
                existing = ModuleCategory.query.filter_by(level1=level1, level2=level2).first()
                if not existing:
                    category = ModuleCategory(level1=level1, level2=level2)
                    db.session.add(category)
        db.session.commit()
