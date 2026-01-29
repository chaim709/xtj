"""
岗位管理路由 - 智能选岗功能
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from app import db
from app.models.position import Position, StudentPosition
from app.models.student import Student
from app.models.major import MajorCategory, Major
from app.services.position_service import PositionService
from app.services.major_service import MajorService
from app.services.import_service import ImportService
from app.services.position_dashboard_service import PositionDashboardService

positions_bp = Blueprint('positions', __name__, url_prefix='/positions')


# ==================== 智能选岗向导 ====================

@positions_bp.route('/wizard')
@login_required
def wizard():
    """智能选岗向导"""
    # 获取城市列表
    cities = PositionService.get_cities(2026, '省考')
    return render_template('positions/wizard.html', cities=cities)


@positions_bp.route('/wizard/result')
@login_required
def wizard_result():
    """智能选岗向导结果"""
    # 获取筛选参数
    my_education = request.args.get('my_education', '本科')
    political_status = request.args.get('political_status', '')
    work_years = request.args.get('work_years', '0', type=int)
    gender = request.args.get('gender', '')
    age = request.args.get('age', type=int)
    exam_type = request.args.get('exam_type', '省考')
    year = request.args.get('year', 2026, type=int)
    cities = request.args.getlist('cities')
    my_major = request.args.get('my_major', '')
    include_unlimited = request.args.get('include_unlimited', 'on') == 'on'
    
    # 构建查询
    query = Position.query.filter(
        Position.year == year,
        Position.exam_type == exam_type
    )
    
    # 1. 学历匹配
    education_conditions = []
    education_mapping = {
        '专科': ['大专及以上', '大专或本科', '不限'],
        '本科': ['本科及以上', '仅限本科', '大专及以上', '大专或本科', '本科或硕士', '不限'],
        '硕士研究生': ['研究生及以上', '仅限研究生', '硕士及以上', '本科及以上', '本科或硕士', '大专及以上', '不限'],
        '博士研究生': ['博士及以上', '仅限博士', '研究生及以上', '硕士及以上', '本科及以上', '大专及以上', '不限'],
    }
    allowed_educations = education_mapping.get(my_education, ['不限'])
    for edu in allowed_educations:
        education_conditions.append(Position.education.contains(edu))
    query = query.filter(or_(*education_conditions))
    
    # 2. 城市筛选
    if cities:
        query = query.filter(Position.city.in_(cities))
    
    # 3. 专业匹配
    if my_major:
        major_conditions = [Position.major_requirement.contains(my_major)]
        if include_unlimited:
            major_conditions.append(Position.major_requirement.contains('不限'))
        query = query.filter(or_(*major_conditions))
    elif include_unlimited:
        # 如果没有输入专业但勾选了包含不限，显示所有
        pass
    
    # 4. 排序：优先显示限制条件多的岗位（竞争更小），按竞争比升序
    positions = query.order_by(
        Position.competition_ratio.asc().nullslast(),
        Position.recruit_count.desc()
    ).all()
    
    # 5. 进一步过滤（在Python中处理复杂条件）
    filtered_positions = []
    for p in positions:
        # 检查政治面貌
        if political_status == '党员':
            # 党员可以报考所有岗位
            pass
        elif political_status in ['团员', '群众']:
            # 非党员不能报考要求党员的岗位
            if p.other_requirements and ('党员' in p.other_requirements or '中共党员' in p.other_requirements):
                continue
        
        # 检查基层工作经历
        if work_years == 0:
            # 无工作经历，排除要求工作经历的岗位
            if p.other_requirements and ('基层工作' in p.other_requirements and '年' in p.other_requirements):
                continue
        
        # 检查性别
        if gender:
            if p.other_requirements:
                if gender == '男' and ('限女' in p.other_requirements or '女性' in p.other_requirements):
                    continue
                if gender == '女' and ('限男' in p.other_requirements or '男性' in p.other_requirements):
                    continue
        
        # 计算岗位的"限制条件得分"（条件越多分数越高，竞争越小）
        restriction_score = 0
        if p.education and '仅限' in p.education:
            restriction_score += 2
        if p.education and '及以上' in p.education and '大专' not in p.education:
            restriction_score += 1
        if p.major_requirement and '不限' not in p.major_requirement:
            restriction_score += 2
        if p.other_requirements:
            if '党员' in p.other_requirements:
                restriction_score += 2
            if '基层' in p.other_requirements:
                restriction_score += 1
            if '应届' in p.other_requirements:
                restriction_score += 1
        
        filtered_positions.append({
            'position': p,
            'restriction_score': restriction_score
        })
    
    # 按限制条件得分和竞争比排序
    filtered_positions.sort(key=lambda x: (-x['restriction_score'], x['position'].competition_ratio or 9999))
    
    # 统计信息
    stats = {
        'total': len(filtered_positions),
        'low_competition': len([p for p in filtered_positions if p['position'].competition_ratio and p['position'].competition_ratio < 20]),
        'medium_competition': len([p for p in filtered_positions if p['position'].competition_ratio and 20 <= p['position'].competition_ratio < 50]),
        'high_competition': len([p for p in filtered_positions if p['position'].competition_ratio and p['position'].competition_ratio >= 50]),
    }
    
    # 筛选条件摘要
    filters_summary = {
        'my_education': my_education,
        'political_status': political_status or '不限',
        'work_years': work_years,
        'gender': gender or '不限',
        'exam_type': exam_type,
        'year': year,
        'cities': cities or ['全部城市'],
        'my_major': my_major or '不限',
        'include_unlimited': include_unlimited,
    }
    
    return render_template('positions/wizard_result.html',
                          positions=filtered_positions,
                          stats=stats,
                          filters=filters_summary)


# ==================== 岗位列表和搜索 ====================

@positions_bp.route('/')
@login_required
def list():
    """岗位列表"""
    # 获取筛选参数
    filters = {
        'year': request.args.get('year', 2026, type=int),
        'exam_type': request.args.get('exam_type', '省考'),
        'city': request.args.get('city', ''),
        'system_type': request.args.get('system_type', ''),
        'department_name': request.args.get('department_name', ''),
        'position_name': request.args.get('position_name', ''),
        'education': request.args.get('education', ''),
        'major': request.args.get('major', ''),
        'keyword': request.args.get('keyword', ''),
        'sort_by': request.args.get('sort_by', 'competition_ratio'),
        'sort_order': request.args.get('sort_order', 'asc'),
    }
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 搜索岗位
    positions, total = PositionService.search_positions(filters, page, per_page)
    
    # 获取城市列表（根据考试类型动态获取）
    cities = PositionService.get_cities(filters['year'], filters['exam_type'])
    
    # 获取系统类型列表
    system_types = PositionService.get_system_types(filters['year'], filters['exam_type'])
    
    # 获取统计信息
    stats = PositionService.get_statistics(filters['year'], filters['exam_type'])
    
    # 计算分页
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('positions/list.html',
                          positions=positions,
                          total=total,
                          page=page,
                          total_pages=total_pages,
                          filters=filters,
                          cities=cities,
                          system_types=system_types,
                          stats=stats)


@positions_bp.route('/<int:id>')
@login_required
def detail(id):
    """岗位详情"""
    position = Position.query.get_or_404(id)
    
    # 1. 获取近几年同岗位历史数据（通过职位代码+单位匹配）
    history_positions = Position.query.filter(
        Position.position_code == position.position_code,
        Position.department_name == position.department_name,
        Position.exam_type == position.exam_type,
        Position.id != position.id
    ).order_by(Position.year.desc()).all()
    
    # 如果没有找到，尝试通过单位名称+职位名称模糊匹配
    if not history_positions and position.position_name:
        history_positions = Position.query.filter(
            Position.department_name == position.department_name,
            Position.position_name == position.position_name,
            Position.exam_type == position.exam_type,
            Position.id != position.id
        ).order_by(Position.year.desc()).limit(5).all()
    
    # 2. 获取同单位当年其他岗位（可报考的岗位）
    same_dept_positions = Position.query.filter(
        Position.department_name == position.department_name,
        Position.year == position.year,
        Position.exam_type == position.exam_type,
        Position.id != position.id
    ).order_by(Position.recruit_count.desc()).limit(10).all()
    
    # 3. 获取同城市/地区类似岗位（按专业要求相似度）
    similar_positions = []
    if position.major_requirement and position.major_requirement != '不限':
        # 取专业要求的前10个字符作为关键词
        major_keyword = position.major_requirement[:10]
        similar_positions = Position.query.filter(
            Position.year == position.year,
            Position.exam_type == position.exam_type,
            Position.city == position.city,
            Position.major_requirement.contains(major_keyword),
            Position.id != position.id
        ).order_by(Position.competition_ratio.asc().nullslast()).limit(5).all()
    
    # 4. 获取相同专业+学历条件的所有可报考岗位
    same_condition_positions = []
    same_condition_count = 0
    if position.major_requirement:
        # 构建查询条件
        query = Position.query.filter(
            Position.year == position.year,
            Position.exam_type == position.exam_type,
            Position.id != position.id
        )
        
        # 专业匹配：如果不是"不限"，则匹配相同专业或包含"不限"
        if position.major_requirement != '不限':
            from sqlalchemy import or_
            # 提取专业要求中的关键专业类别（取前两个专业作为匹配）
            major_parts = position.major_requirement.replace('，', ',').replace('、', ',').split(',')
            major_keywords = [m.strip() for m in major_parts[:2] if m.strip()]
            
            if major_keywords:
                # 匹配包含这些专业的岗位，或者专业不限的岗位
                conditions = [Position.major_requirement.contains('不限')]
                for kw in major_keywords:
                    conditions.append(Position.major_requirement.contains(kw))
                query = query.filter(or_(*conditions))
        
        # 学历匹配
        if position.education:
            query = query.filter(Position.education == position.education)
        
        # 获取总数和分页数据
        same_condition_count = query.count()
        same_condition_positions = query.order_by(
            Position.competition_ratio.asc().nullslast(),
            Position.recruit_count.desc()
        ).limit(20).all()
    
    return render_template('positions/detail.html',
                          position=position,
                          history_positions=history_positions,
                          same_dept_positions=same_dept_positions,
                          similar_positions=similar_positions,
                          same_condition_positions=same_condition_positions,
                          same_condition_count=same_condition_count)


# ==================== 学员岗位匹配 ====================

@positions_bp.route('/match/<int:student_id>')
@login_required
def match_for_student(student_id):
    """为学员匹配岗位"""
    student = Student.query.get_or_404(student_id)
    
    # 检查学员信息完整性
    if not student.is_position_eligible():
        return jsonify({
            'success': False,
            'message': '学员选岗信息不完整，请先完善：学历、专业、政治面貌、性别、出生日期'
        })
    
    # 获取筛选参数
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    filters = {}
    if city:
        filters['city'] = city
    
    # 匹配岗位
    matched = PositionService.match_positions_for_student(
        student_id, year, exam_type, filters
    )
    
    return jsonify({
        'success': True,
        'student': student.to_dict(),
        'total': len(matched),
        'positions': matched[:50]  # 限制返回数量
    })


@positions_bp.route('/api/match/<int:student_id>')
@login_required
def api_match(student_id):
    """API: 为学员匹配岗位"""
    return match_for_student(student_id)


# ==================== 数据导入 ====================

@positions_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    """数据导入页面"""
    if not current_user.is_admin():
        flash('只有管理员可以导入数据', 'danger')
        return redirect(url_for('positions.list'))
    
    if request.method == 'POST':
        import_type = request.form.get('import_type')
        year = request.form.get('year', type=int)
        exam_type = request.form.get('exam_type', '省考')
        
        if 'file' not in request.files:
            flash('请选择文件', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('请选择文件', 'danger')
            return redirect(request.url)
        
        # 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)
        file.save(temp_path)
        
        try:
            if import_type == 'positions':
                # 导入岗位数据
                result = ImportService.import_positions_from_excel(
                    temp_path, year, exam_type
                )
                if result['success']:
                    flash(f'导入成功！新增 {result["imported"]} 条，更新 {result["updated"]} 条', 'success')
                else:
                    flash(f'导入失败：{result["errors"][:3]}', 'danger')
            
            elif import_type == 'majors':
                # 导入专业目录（暂不支持，需要PDF解析）
                flash('专业目录导入暂不支持，请联系管理员', 'warning')
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return redirect(url_for('positions.import_data'))
    
    # 获取导入统计
    stats = ImportService.get_import_stats()
    
    return render_template('positions/import.html', stats=stats)


# ==================== 专业搜索 ====================

@positions_bp.route('/api/majors/search')
@login_required
def search_majors():
    """搜索专业"""
    keyword = request.args.get('q', '')
    education = request.args.get('education', '')
    
    if len(keyword) < 2:
        return jsonify([])
    
    majors = MajorService.search_majors(keyword, education, limit=20)
    
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'category_id': m.category_id,
        'category_name': m.category.name if m.category else '',
        'education_level': m.education_level
    } for m in majors])


@positions_bp.route('/api/categories')
@login_required
def get_categories():
    """获取专业大类列表"""
    categories = MajorService.get_all_categories()
    return jsonify([c.to_dict() for c in categories])


# ==================== 统计接口 ====================

@positions_bp.route('/api/stats')
@login_required
def get_stats():
    """获取统计信息"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    stats = PositionService.get_statistics(year, exam_type)
    return jsonify(stats)


@positions_bp.route('/api/cities')
@login_required
def get_cities():
    """获取城市列表"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    cities = PositionService.get_cities(year, exam_type)
    return jsonify(cities)


# ==================== 岗位数据仪表盘 ====================

@positions_bp.route('/dashboard')
@login_required
def dashboard():
    """岗位数据仪表盘 - 主页面"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    view = request.args.get('view', 'admin')  # admin 或 student
    
    # 获取城市列表
    cities = PositionService.get_cities(year, exam_type)
    
    # 获取基础概览数据
    overview = PositionDashboardService.get_overview(year, exam_type)
    
    return render_template('positions/dashboard/index.html',
                          year=year,
                          exam_type=exam_type,
                          view=view,
                          cities=cities,
                          overview=overview)


@positions_bp.route('/suqian')
@login_required
def suqian_dashboard():
    """宿迁专项选岗指南"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    # 获取宿迁数据
    overview = PositionDashboardService.get_suqian_overview(year, exam_type)
    district_stats = PositionDashboardService.get_suqian_district_stats(year, exam_type)
    district_year_stats = PositionDashboardService.get_suqian_district_year_stats(exam_type)
    suggestions = PositionDashboardService.get_suqian_suggestions(year, exam_type)
    
    return render_template('positions/dashboard/suqian.html',
                          year=year,
                          exam_type=exam_type,
                          overview=overview,
                          district_stats=district_stats,
                          district_year_stats=district_year_stats,
                          suggestions=suggestions)


@positions_bp.route('/sihong')
@login_required
def sihong_dashboard():
    """泗洪县专项选岗指南"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    # 获取泗洪数据
    overview = PositionDashboardService.get_sihong_overview(year, exam_type)
    town_stats = PositionDashboardService.get_sihong_town_stats(year, exam_type)
    year_trend = PositionDashboardService.get_sihong_year_trend(exam_type)
    dept_year_stats = PositionDashboardService.get_sihong_department_year_stats(exam_type)
    suggestions = PositionDashboardService.get_sihong_suggestions(year, exam_type)
    
    return render_template('positions/dashboard/sihong.html',
                          year=year,
                          exam_type=exam_type,
                          overview=overview,
                          town_stats=town_stats,
                          year_trend=year_trend,
                          dept_year_stats=dept_year_stats,
                          suggestions=suggestions)


# ==================== 仪表盘 API 接口 ====================

@positions_bp.route('/api/dashboard/overview')
@login_required
def api_dashboard_overview():
    """API: 获取概览数据"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_overview(year, exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/city-stats')
@login_required
def api_city_stats():
    """API: 获取城市统计"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_city_stats(year, exam_type)
    return jsonify(data)


@positions_bp.route('/api/dashboard/system-stats')
@login_required
def api_system_stats():
    """API: 获取系统分布统计"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_system_stats(year, exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/education-stats')
@login_required
def api_education_stats():
    """API: 获取学历分布统计"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_education_stats(year, exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/competition')
@login_required
def api_competition():
    """API: 获取竞争比分析"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_competition_distribution(year, exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/score-distribution')
@login_required
def api_score_distribution():
    """API: 获取进面分分布"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_score_distribution(year, exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/year-comparison')
@login_required
def api_year_comparison():
    """API: 获取年度对比"""
    exam_type = request.args.get('exam_type', '省考')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_year_comparison(exam_type, city if city else None)
    return jsonify(data)


@positions_bp.route('/api/dashboard/major-ranking')
@login_required
def api_major_ranking():
    """API: 获取专业热度排行"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_major_ranking(year, exam_type)
    return jsonify(data)


@positions_bp.route('/api/dashboard/low-competition')
@login_required
def api_low_competition():
    """API: 获取低竞争岗位推荐"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    education = request.args.get('education', '')
    major = request.args.get('major', '')
    city = request.args.get('city', '')
    
    data = PositionDashboardService.get_low_competition_positions(
        year, exam_type,
        education if education else None,
        major if major else None,
        city if city else None
    )
    return jsonify(data)


@positions_bp.route('/api/dashboard/matching-stats')
@login_required
def api_matching_stats():
    """API: 获取匹配岗位统计（选岗视角）"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    education = request.args.get('education', '')
    major = request.args.get('major', '')
    
    data = PositionDashboardService.get_matching_positions_stats(
        year, exam_type,
        education if education else None,
        major if major else None
    )
    return jsonify(data)


# ==================== 宿迁专项 API ====================

@positions_bp.route('/api/suqian/overview')
@login_required
def api_suqian_overview():
    """API: 宿迁概览"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_suqian_overview(year, exam_type)
    return jsonify(data)


@positions_bp.route('/api/suqian/district-stats')
@login_required
def api_suqian_district_stats():
    """API: 宿迁区县统计"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_suqian_district_stats(year, exam_type)
    return jsonify(data)


# ==================== 泗洪专项 API ====================

@positions_bp.route('/api/sihong/overview')
@login_required
def api_sihong_overview():
    """API: 泗洪概览"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_sihong_overview(year, exam_type)
    return jsonify(data)


@positions_bp.route('/api/sihong/town-stats')
@login_required
def api_sihong_town_stats():
    """API: 泗洪乡镇统计"""
    year = request.args.get('year', 2026, type=int)
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_sihong_town_stats(year, exam_type)
    return jsonify(data)


@positions_bp.route('/api/sihong/year-trend')
@login_required
def api_sihong_year_trend():
    """API: 泗洪年度趋势"""
    exam_type = request.args.get('exam_type', '省考')
    
    data = PositionDashboardService.get_sihong_year_trend(exam_type)
    return jsonify(data)
