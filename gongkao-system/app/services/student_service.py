"""
学员服务 - 学员管理业务逻辑
"""
from datetime import datetime
from app import db
from app.models.student import Student


class StudentService:
    """学员服务类"""
    
    @staticmethod
    def create_student(data):
        """
        创建学员
        
        Args:
            data: 学员数据字典
        
        Returns:
            创建的学员对象
        """
        student = Student(
            name=data.get('name'),
            phone=data.get('phone'),
            wechat=data.get('wechat'),
            class_name=data.get('class_name'),
            exam_type=data.get('exam_type'),
            target_position=data.get('target_position'),
            has_basic=data.get('has_basic', False),
            is_agreement=data.get('is_agreement', False),
            base_level=data.get('base_level'),
            learning_style=data.get('learning_style'),
            study_plan=data.get('study_plan'),
            education=data.get('education'),
            id_number=data.get('id_number'),
            address=data.get('address'),
            parent_phone=data.get('parent_phone'),
            emergency_contact=data.get('emergency_contact'),
            supervisor_id=data.get('supervisor_id'),
            enrollment_date=data.get('enrollment_date'),
            payment_status=data.get('payment_status'),
            remarks=data.get('remarks'),
        )
        
        db.session.add(student)
        db.session.commit()
        return student
    
    @staticmethod
    def update_student(student_id, data):
        """
        更新学员信息
        
        Args:
            student_id: 学员ID
            data: 更新数据字典
        
        Returns:
            更新后的学员对象
        """
        student = Student.query.get(student_id)
        if not student:
            return None
        
        # 更新字段
        for key, value in data.items():
            if hasattr(student, key) and key not in ['id', 'created_at']:
                setattr(student, key, value)
        
        student.updated_at = datetime.utcnow()
        db.session.commit()
        return student
    
    @staticmethod
    def delete_student(student_id):
        """
        删除学员（软删除）
        
        Args:
            student_id: 学员ID
        
        Returns:
            是否删除成功
        """
        student = Student.query.get(student_id)
        if not student:
            return False
        
        student.status = 'inactive'
        student.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def get_student(student_id):
        """
        获取学员详情
        
        Args:
            student_id: 学员ID
        
        Returns:
            学员对象
        """
        return Student.query.get(student_id)
    
    @staticmethod
    def get_all_students(include_inactive=False):
        """
        获取所有学员
        
        Args:
            include_inactive: 是否包含已删除的学员
        
        Returns:
            学员列表
        """
        query = Student.query
        if not include_inactive:
            query = query.filter(Student.status == 'active')
        return query.order_by(Student.created_at.desc()).all()
    
    @staticmethod
    def search_students(filters, supervisor_id=None, page=1, per_page=20):
        """
        搜索学员
        
        Args:
            filters: 筛选条件字典
            supervisor_id: 督学人员ID（非管理员只能看自己负责的）
            page: 页码
            per_page: 每页数量
        
        Returns:
            分页结果
        """
        query = Student.query.filter(Student.status == 'active')
        
        # 督学人员只能看自己负责的学员
        if supervisor_id:
            query = query.filter(Student.supervisor_id == supervisor_id)
        
        # 搜索条件
        search = filters.get('search', '').strip()
        if search:
            query = query.filter(
                db.or_(
                    Student.name.ilike(f'%{search}%'),
                    Student.phone.ilike(f'%{search}%')
                )
            )
        
        # 班次筛选
        class_name = filters.get('class_name')
        if class_name:
            query = query.filter(Student.class_name == class_name)
        
        # 报考类型筛选
        exam_type = filters.get('exam_type')
        if exam_type:
            query = query.filter(Student.exam_type.ilike(f'%{exam_type}%'))
        
        # 是否协议班
        is_agreement = filters.get('is_agreement')
        if is_agreement is not None:
            query = query.filter(Student.is_agreement == is_agreement)
        
        # 是否需要关注
        need_attention = filters.get('need_attention')
        if need_attention:
            query = query.filter(Student.need_attention == True)
        
        # 排序
        query = query.order_by(Student.enrollment_date.desc(), Student.id.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination
    
    @staticmethod
    def get_students_by_supervisor(supervisor_id):
        """
        获取某督学负责的学员
        
        Args:
            supervisor_id: 督学人员ID
        
        Returns:
            学员列表
        """
        return Student.query.filter(
            Student.supervisor_id == supervisor_id,
            Student.status == 'active'
        ).all()
    
    @staticmethod
    def mark_attention(student_id, need_attention=True):
        """
        标记学员是否需要重点关注
        
        Args:
            student_id: 学员ID
            need_attention: 是否需要关注
        
        Returns:
            学员对象
        """
        student = Student.query.get(student_id)
        if student:
            student.need_attention = need_attention
            db.session.commit()
        return student
    
    @staticmethod
    def update_last_contact(student_id):
        """
        更新最后联系日期
        
        Args:
            student_id: 学员ID
        """
        student = Student.query.get(student_id)
        if student:
            student.last_contact_date = datetime.utcnow().date()
            db.session.commit()
        return student
