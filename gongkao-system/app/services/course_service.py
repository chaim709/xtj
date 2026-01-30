"""
课程服务 - 管理科目、招生项目、报名套餐、班型、班次
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from app import db
from app.models.course import (
    Subject, Project, Package, ClassType, ClassBatch,
    Schedule, ScheduleChangeLog, StudentBatch, CourseRecording, Attendance
)


class CourseService:
    """课程服务类"""
    
    # ==================== 科目管理 ====================
    
    @staticmethod
    def get_subjects(exam_type=None, status='active', include_inactive=False):
        """
        获取科目列表
        
        Args:
            exam_type: 考试类型筛选 (civil/career/common)
            status: 状态筛选
            include_inactive: 是否包含停用的科目
        
        Returns:
            List[Subject]: 科目列表
        """
        query = Subject.query
        
        if exam_type:
            query = query.filter(Subject.exam_type == exam_type)
        
        if not include_inactive:
            query = query.filter(Subject.status == 'active')
        
        return query.order_by(Subject.sort_order, Subject.id).all()
    
    @staticmethod
    def get_subject(subject_id):
        """获取单个科目"""
        return Subject.query.get(subject_id)
    
    @staticmethod
    def create_subject(data):
        """
        创建科目
        
        Args:
            data: {name, short_name, exam_type, sort_order}
        
        Returns:
            Subject: 创建的科目
        """
        subject = Subject(
            name=data.get('name'),
            short_name=data.get('short_name'),
            exam_type=data.get('exam_type', 'common'),
            is_preset=False,
            sort_order=data.get('sort_order', 0),
            status='active'
        )
        db.session.add(subject)
        db.session.commit()
        return subject
    
    @staticmethod
    def update_subject(subject_id, data):
        """更新科目"""
        subject = Subject.query.get(subject_id)
        if not subject:
            raise ValueError('科目不存在')
        
        if 'name' in data:
            subject.name = data['name']
        if 'short_name' in data:
            subject.short_name = data['short_name']
        if 'exam_type' in data:
            subject.exam_type = data['exam_type']
        if 'sort_order' in data:
            subject.sort_order = data['sort_order']
        
        db.session.commit()
        return subject
    
    @staticmethod
    def toggle_subject_status(subject_id):
        """切换科目状态"""
        subject = Subject.query.get(subject_id)
        if not subject:
            raise ValueError('科目不存在')
        
        subject.status = 'inactive' if subject.status == 'active' else 'active'
        db.session.commit()
        return subject
    
    @staticmethod
    def delete_subject(subject_id):
        """删除科目（仅限自定义科目）"""
        subject = Subject.query.get(subject_id)
        if not subject:
            raise ValueError('科目不存在')
        
        if subject.is_preset:
            raise ValueError('预设科目不可删除')
        
        # 检查是否有关联的课表
        if subject.schedules.count() > 0:
            raise ValueError('该科目已有关联课表，无法删除')
        
        db.session.delete(subject)
        db.session.commit()
        return True
    
    # ==================== 招生项目管理 ====================
    
    @staticmethod
    def get_projects(status=None, year=None, page=1, per_page=20):
        """
        获取招生项目列表
        
        Args:
            status: 状态筛选
            year: 年份筛选
            page: 页码
            per_page: 每页数量
        
        Returns:
            Pagination: 分页对象
        """
        query = Project.query
        
        if status:
            query = query.filter(Project.status == status)
        if year:
            query = query.filter(Project.year == year)
        
        return query.order_by(Project.year.desc(), Project.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_all_projects(status=None):
        """获取所有项目（不分页）"""
        query = Project.query
        if status:
            query = query.filter(Project.status == status)
        return query.order_by(Project.year.desc(), Project.created_at.desc()).all()
    
    @staticmethod
    def get_project(project_id):
        """获取单个项目"""
        return Project.query.get(project_id)
    
    @staticmethod
    def create_project(data):
        """
        创建招生项目
        
        Args:
            data: {name, exam_type, year, start_date, end_date, description}
        
        Returns:
            Project: 创建的项目
        """
        project = Project(
            name=data.get('name'),
            exam_type=data.get('exam_type'),
            year=data.get('year'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            description=data.get('description'),
            status='preparing'
        )
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def update_project(project_id, data):
        """更新项目"""
        project = Project.query.get(project_id)
        if not project:
            raise ValueError('项目不存在')
        
        if 'name' in data:
            project.name = data['name']
        if 'exam_type' in data:
            project.exam_type = data['exam_type']
        if 'year' in data:
            project.year = data['year']
        if 'start_date' in data:
            project.start_date = data['start_date']
        if 'end_date' in data:
            project.end_date = data['end_date']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        return project
    
    @staticmethod
    def update_project_status(project_id, status):
        """更新项目状态"""
        project = Project.query.get(project_id)
        if not project:
            raise ValueError('项目不存在')
        
        project.status = status
        project.updated_at = datetime.utcnow()
        db.session.commit()
        return project
    
    @staticmethod
    def delete_project(project_id):
        """删除项目"""
        project = Project.query.get(project_id)
        if not project:
            raise ValueError('项目不存在')
        
        # 检查是否有关联数据
        if project.packages.count() > 0:
            raise ValueError('该项目下有报名套餐，无法删除')
        if project.class_types.count() > 0:
            raise ValueError('该项目下有班型，无法删除')
        
        db.session.delete(project)
        db.session.commit()
        return True
    
    # ==================== 报名套餐管理 ====================
    
    @staticmethod
    def get_packages(project_id=None, status=None):
        """
        获取报名套餐列表
        
        Args:
            project_id: 项目ID筛选
            status: 状态筛选
        
        Returns:
            List[Package]: 套餐列表
        """
        query = Package.query
        
        if project_id:
            query = query.filter(Package.project_id == project_id)
        if status:
            query = query.filter(Package.status == status)
        
        return query.order_by(Package.sort_order, Package.id).all()
    
    @staticmethod
    def get_package(package_id):
        """获取单个套餐"""
        return Package.query.get(package_id)
    
    @staticmethod
    def create_package(data):
        """
        创建报名套餐
        
        Args:
            data: {project_id, name, package_type, price, valid_days, ...}
        
        Returns:
            Package: 创建的套餐
        """
        package = Package(
            project_id=data.get('project_id'),
            name=data.get('name'),
            package_type=data.get('package_type'),
            price=Decimal(str(data.get('price', 0))),
            valid_days=data.get('valid_days'),
            valid_start=data.get('valid_start'),
            valid_end=data.get('valid_end'),
            include_all_types=data.get('include_all_types', True),
            included_type_ids=data.get('included_type_ids'),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0),
            status='active'
        )
        
        # 设置优惠规则
        if 'discount_rules' in data and data['discount_rules']:
            package.set_discount_rules(data['discount_rules'])
        
        db.session.add(package)
        db.session.commit()
        return package
    
    @staticmethod
    def update_package(package_id, data):
        """更新套餐"""
        package = Package.query.get(package_id)
        if not package:
            raise ValueError('套餐不存在')
        
        if 'name' in data:
            package.name = data['name']
        if 'package_type' in data:
            package.package_type = data['package_type']
        if 'price' in data:
            package.price = Decimal(str(data['price']))
        if 'valid_days' in data:
            package.valid_days = data['valid_days']
        if 'valid_start' in data:
            package.valid_start = data['valid_start']
        if 'valid_end' in data:
            package.valid_end = data['valid_end']
        if 'include_all_types' in data:
            package.include_all_types = data['include_all_types']
        if 'included_type_ids' in data:
            package.included_type_ids = data['included_type_ids']
        if 'description' in data:
            package.description = data['description']
        if 'sort_order' in data:
            package.sort_order = data['sort_order']
        if 'discount_rules' in data:
            package.set_discount_rules(data['discount_rules'])
        
        db.session.commit()
        return package
    
    @staticmethod
    def toggle_package_status(package_id):
        """切换套餐状态"""
        package = Package.query.get(package_id)
        if not package:
            raise ValueError('套餐不存在')
        
        package.status = 'inactive' if package.status == 'active' else 'active'
        db.session.commit()
        return package
    
    @staticmethod
    def calculate_price(package_id, discount_type=None, group_count=1):
        """
        计算套餐价格
        
        Args:
            package_id: 套餐ID
            discount_type: 优惠类型 (group/early_bird)
            group_count: 团报人数
        
        Returns:
            dict: {original_price, discount, final_price, discount_description}
        """
        package = Package.query.get(package_id)
        if not package:
            raise ValueError('套餐不存在')
        
        original_price = float(package.price)
        discount = 0
        discount_description = ''
        
        rules = package.get_discount_rules()
        
        # 团报优惠
        if discount_type == 'group' and 'group_discount' in rules:
            for rule in rules['group_discount']:
                if group_count >= rule.get('min_people', 0):
                    discount = rule.get('discount', 0)
                    discount_description = rule.get('description', f'{group_count}人团报')
        
        # 早鸟优惠
        elif discount_type == 'early_bird' and 'early_bird' in rules:
            early_bird = rules['early_bird']
            end_date = early_bird.get('end_date')
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                if date.today() <= end_date:
                    discount = early_bird.get('discount', 0)
                    discount_description = early_bird.get('description', '早鸟优惠')
        
        final_price = original_price - discount
        
        return {
            'original_price': original_price,
            'discount': discount,
            'final_price': max(0, final_price),
            'discount_description': discount_description
        }
    
    # ==================== 班型管理 ====================
    
    @staticmethod
    def get_class_types(project_id, status=None):
        """
        获取班型列表
        
        Args:
            project_id: 项目ID
            status: 状态筛选
        
        Returns:
            List[ClassType]: 班型列表
        """
        query = ClassType.query.filter(ClassType.project_id == project_id)
        
        if status:
            query = query.filter(ClassType.status == status)
        
        return query.order_by(ClassType.sort_order, ClassType.id).all()
    
    @staticmethod
    def get_class_type(type_id):
        """获取单个班型"""
        return ClassType.query.get(type_id)
    
    @staticmethod
    def create_class_type(data):
        """创建班型"""
        class_type = ClassType(
            project_id=data.get('project_id'),
            name=data.get('name'),
            planned_days=data.get('planned_days'),
            single_price=Decimal(str(data.get('single_price', 0))) if data.get('single_price') else None,
            sort_order=data.get('sort_order', 0),
            description=data.get('description'),
            status='active'
        )
        db.session.add(class_type)
        db.session.commit()
        return class_type
    
    @staticmethod
    def update_class_type(type_id, data):
        """更新班型"""
        class_type = ClassType.query.get(type_id)
        if not class_type:
            raise ValueError('班型不存在')
        
        if 'name' in data:
            class_type.name = data['name']
        if 'planned_days' in data:
            class_type.planned_days = data['planned_days']
        if 'single_price' in data:
            class_type.single_price = Decimal(str(data['single_price'])) if data['single_price'] else None
        if 'sort_order' in data:
            class_type.sort_order = data['sort_order']
        if 'description' in data:
            class_type.description = data['description']
        
        db.session.commit()
        return class_type
    
    @staticmethod
    def reorder_class_types(project_id, type_ids):
        """
        重新排序班型
        
        Args:
            project_id: 项目ID
            type_ids: 排序后的班型ID列表
        
        Returns:
            bool: 是否成功
        """
        for index, type_id in enumerate(type_ids):
            class_type = ClassType.query.get(type_id)
            if class_type and class_type.project_id == project_id:
                class_type.sort_order = index
        
        db.session.commit()
        return True
    
    @staticmethod
    def delete_class_type(type_id):
        """删除班型"""
        class_type = ClassType.query.get(type_id)
        if not class_type:
            raise ValueError('班型不存在')
        
        if class_type.batches.count() > 0:
            raise ValueError('该班型下有班次，无法删除')
        
        db.session.delete(class_type)
        db.session.commit()
        return True
    
    # ==================== 班次管理 ====================
    
    @staticmethod
    def get_batches(class_type_id=None, project_id=None, status=None, page=1, per_page=20):
        """
        获取班次列表
        
        Args:
            class_type_id: 班型ID筛选
            project_id: 项目ID筛选
            status: 状态筛选
            page: 页码
            per_page: 每页数量
        
        Returns:
            Pagination: 分页对象
        """
        query = ClassBatch.query
        
        if class_type_id:
            query = query.filter(ClassBatch.class_type_id == class_type_id)
        
        if project_id:
            query = query.join(ClassType).filter(ClassType.project_id == project_id)
        
        if status:
            query = query.filter(ClassBatch.status == status)
        
        return query.order_by(ClassBatch.start_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_all_batches(class_type_id=None, status=None):
        """获取所有班次（不分页）"""
        query = ClassBatch.query
        
        if class_type_id:
            query = query.filter(ClassBatch.class_type_id == class_type_id)
        if status:
            query = query.filter(ClassBatch.status == status)
        
        return query.order_by(ClassBatch.start_date.desc()).all()
    
    @staticmethod
    def get_batch(batch_id):
        """获取单个班次"""
        return ClassBatch.query.get(batch_id)
    
    @staticmethod
    def create_batch(data):
        """创建班次"""
        # 计算期数
        class_type_id = data.get('class_type_id')
        existing_count = ClassBatch.query.filter_by(class_type_id=class_type_id).count()
        batch_number = existing_count + 1
        
        # 计算实际天数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        actual_days = (end_date - start_date).days + 1 if start_date and end_date else None
        
        batch = ClassBatch(
            class_type_id=class_type_id,
            name=data.get('name') or f'{ClassType.query.get(class_type_id).name}第{batch_number}期',
            batch_number=batch_number,
            start_date=start_date,
            end_date=end_date,
            actual_days=actual_days,
            max_students=data.get('max_students'),
            classroom=data.get('classroom'),
            status='recruiting'
        )
        db.session.add(batch)
        db.session.commit()
        return batch
    
    @staticmethod
    def update_batch(batch_id, data):
        """更新班次"""
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        if 'name' in data:
            batch.name = data['name']
        if 'start_date' in data:
            batch.start_date = data['start_date']
        if 'end_date' in data:
            batch.end_date = data['end_date']
        if 'max_students' in data:
            batch.max_students = data['max_students']
        if 'classroom' in data:
            batch.classroom = data['classroom']
        
        # 重新计算实际天数
        if batch.start_date and batch.end_date:
            batch.actual_days = (batch.end_date - batch.start_date).days + 1
        
        db.session.commit()
        return batch
    
    @staticmethod
    def update_batch_status(batch_id, status):
        """更新班次状态"""
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        batch.status = status
        db.session.commit()
        return batch
    
    @staticmethod
    def copy_batch(batch_id, new_start_date):
        """
        复制班次
        
        Args:
            batch_id: 源班次ID
            new_start_date: 新班次开课日期
        
        Returns:
            ClassBatch: 新班次
        """
        source_batch = ClassBatch.query.get(batch_id)
        if not source_batch:
            raise ValueError('源班次不存在')
        
        # 计算日期偏移
        date_offset = (new_start_date - source_batch.start_date).days
        new_end_date = source_batch.end_date + timedelta(days=date_offset)
        
        # 创建新班次
        new_batch = CourseService.create_batch({
            'class_type_id': source_batch.class_type_id,
            'start_date': new_start_date,
            'end_date': new_end_date,
            'max_students': source_batch.max_students,
            'classroom': source_batch.classroom,
        })
        
        return new_batch
    
    @staticmethod
    def get_batch_students(batch_id):
        """获取班次学员列表"""
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            return []
        
        student_batches = batch.student_batches.filter_by(status='active').all()
        return [sb.student for sb in student_batches]
    
    @staticmethod
    def delete_batch(batch_id):
        """删除班次"""
        batch = ClassBatch.query.get(batch_id)
        if not batch:
            raise ValueError('班次不存在')
        
        if batch.student_batches.filter_by(status='active').count() > 0:
            raise ValueError('该班次有在学学员，无法删除')
        
        # 删除关联的录播记录
        CourseRecording.query.filter_by(batch_id=batch_id).delete()
        
        # 删除关联的考勤记录
        Attendance.query.filter_by(batch_id=batch_id).delete()
        
        # 删除关联的课表
        Schedule.query.filter_by(batch_id=batch_id).delete()
        
        # 删除关联的学员班次记录
        StudentBatch.query.filter_by(batch_id=batch_id).delete()
        
        db.session.delete(batch)
        db.session.commit()
        return True
    
    # ==================== 学员班次管理 ====================
    
    @staticmethod
    def add_student_to_batch(student_id, batch_id):
        """
        将学员添加到班次
        
        Args:
            student_id: 学员ID
            batch_id: 班次ID
        
        Returns:
            StudentBatch: 关联记录
        """
        # 检查是否已存在
        existing = StudentBatch.query.filter_by(
            student_id=student_id,
            batch_id=batch_id
        ).first()
        
        if existing:
            if existing.status == 'dropped':
                existing.status = 'active'
                existing.enroll_time = datetime.utcnow()
                db.session.commit()
                return existing
            else:
                raise ValueError('学员已在该班次中')
        
        # 检查班次是否已满
        batch = ClassBatch.query.get(batch_id)
        if batch.is_full:
            raise ValueError('该班次已满员')
        
        # 创建关联
        student_batch = StudentBatch(
            student_id=student_id,
            batch_id=batch_id,
            status='active',
            progress_day=0
        )
        db.session.add(student_batch)
        
        # 更新班次人数
        batch.update_enrolled_count()
        
        db.session.commit()
        return student_batch
    
    @staticmethod
    def remove_student_from_batch(student_id, batch_id):
        """将学员从班次移除"""
        student_batch = StudentBatch.query.filter_by(
            student_id=student_id,
            batch_id=batch_id
        ).first()
        
        if not student_batch:
            raise ValueError('学员不在该班次中')
        
        student_batch.status = 'dropped'
        
        # 更新班次人数
        batch = ClassBatch.query.get(batch_id)
        batch.update_enrolled_count()
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_student_batches(student_id):
        """获取学员的所有班次"""
        return StudentBatch.query.filter_by(
            student_id=student_id
        ).order_by(StudentBatch.enroll_time.desc()).all()
    
    @staticmethod
    def get_student_current_batch(student_id):
        """获取学员当前正在学习的班次"""
        student_batch = StudentBatch.query.filter_by(
            student_id=student_id,
            status='active'
        ).join(ClassBatch).filter(
            ClassBatch.status == 'ongoing'
        ).first()
        
        return student_batch
