"""
工作台路由 - 督学人员首页
"""
from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, render_template, send_file, request, jsonify
from flask_login import login_required, current_user
from app.services.follow_up_service import FollowUpService
from app.services.schedule_service import ScheduleService
from app.services.reminder_service import ReminderService  # 第三阶段新增
from app.models.course import Project, ClassBatch
from app.models.teacher import Teacher
from app import db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """工作台首页"""
    # 获取统计数据
    supervisor_id = None if current_user.is_admin() else current_user.id
    
    stats = FollowUpService.get_dashboard_statistics(supervisor_id)
    recent_logs = FollowUpService.get_recent_logs(supervisor_id, limit=5)
    
    # 第二阶段新增：课程统计
    course_stats = get_course_statistics()
    today_schedules = ScheduleService.get_today_schedules()
    
    # 第三阶段新增：提醒数据
    reminders = ReminderService.get_dashboard_reminders()
    pending_follow_ups = ReminderService.get_pending_follow_ups(limit=5)
    attention_students = ReminderService.get_attention_students(limit=5)
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         recent_logs=recent_logs,
                         course_stats=course_stats,
                         today_schedules=today_schedules,
                         reminders=reminders,
                         pending_follow_ups=pending_follow_ups,
                         attention_students=attention_students,
                         now=datetime.now)


def get_course_statistics():
    """
    获取课程相关统计数据
    
    Returns:
        dict: 课程统计数据
    """
    # 招生中的项目数量
    recruiting_projects = Project.query.filter_by(status='recruiting').count()
    
    # 正在进行的班次
    ongoing_batches = ClassBatch.query.filter_by(status='ongoing').count()
    
    # 招生中的班次
    recruiting_batches = ClassBatch.query.filter_by(status='recruiting').count()
    
    # 今日上课班次数
    today = date.today()
    today_batch_count = len(set(s.batch_id for s in ScheduleService.get_today_schedules()))
    
    # 活跃老师数量
    active_teachers = Teacher.query.filter_by(status='active').count()
    
    return {
        'recruiting_projects': recruiting_projects,
        'ongoing_batches': ongoing_batches,
        'recruiting_batches': recruiting_batches,
        'today_batch_count': today_batch_count,
        'active_teachers': active_teachers,
    }


@dashboard_bp.route('/help')
@login_required
def help_center():
    """帮助中心 - 显示系统更新日志和帮助信息"""
    # 版本更新记录
    updates = [
        {
            'version': '1.0.2',
            'date': '2026-01-30',
            'title': '课程管理增强 & 数据备份功能',
            'changes': [
                '新增班次详情页批量添加学员功能',
                '新增班型、班次删除功能',
                '课表显示优化：支持晨读、上午、下午、晚间科目安排',
                '新增课程录播导入功能',
                '帮助中心新增数据导出/导入功能，支持全量备份恢复',
                '课程日历日期修正，正确显示2026年课程',
                '修复作业详情页target_students解析问题',
            ]
        },
        {
            'version': '1.0.1',
            'date': '2026-01-29',
            'title': '督学管理模块上线',
            'changes': [
                '新增督学管理工作台，一站式管理学员督学工作',
                '学员督学Tab：卡片式学员列表，显示心态、状态、计划进度，支持快速筛选和记录',
                '学习计划Tab：计划模板管理，支持批量创建学习计划',
                '督学记录Tab：时间线视图展示所有督学记录，支持日期范围筛选',
                '业绩统计Tab：督学工作量统计、学员心态分布图、30天趋势图',
                '快速记录功能：在学员列表页可直接快速记录督学日志',
                '学员分配功能：管理员可批量分配学员给督学老师',
            ]
        },
        {
            'version': '1.0.0',
            'date': '2026-01-28',
            'title': '系统初始版本',
            'changes': [
                '学员管理：学员信息录入、查询、编辑',
                '督学日志：记录与学员的沟通内容',
                '课程管理：项目、班次、课表管理',
                '智能选岗：岗位查询和选岗向导',
                '题库系统：题目管理和错题收集',
            ]
        },
    ]
    
    return render_template('dashboard/help.html', updates=updates)


@dashboard_bp.route('/settings')
@login_required
def settings():
    """系统设置页面"""
    return render_template('dashboard/settings.html')


@dashboard_bp.route('/export-data')
@login_required
def export_data():
    """导出全部数据库数据为Excel"""
    if not current_user.is_admin():
        return "没有权限", 403
    
    import pandas as pd
    from sqlalchemy import inspect, text
    
    output = BytesIO()
    
    # 获取所有表名
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    # 排除不需要导出的表（如alembic版本表）
    exclude_tables = ['alembic_version']
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for table_name in sorted(tables):
            if table_name in exclude_tables:
                continue
            
            try:
                # 直接用SQL查询表数据
                df = pd.read_sql_table(table_name, db.engine)
                if len(df) > 0:
                    # Excel sheet名称最多31个字符
                    sheet_name = table_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"导出表 {table_name} 失败: {e}")
                continue
    
    output.seek(0)
    
    filename = f'系统全量数据备份_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@dashboard_bp.route('/import-data', methods=['POST'])
@login_required
def import_data():
    """从Excel导入数据（全量恢复）"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '没有权限'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'})
    
    import pandas as pd
    from sqlalchemy import text
    
    try:
        xl = pd.ExcelFile(file)
        results = []
        
        # 导入顺序很重要（外键依赖）
        import_order = [
            'users', 'subjects', 'major_categories', 'majors', 'positions',
            'projects', 'packages', 'class_types', 'class_batches', 
            'teachers', 'students', 'student_batches', 'student_positions',
            'schedules', 'schedule_change_logs', 'attendances', 'course_recordings',
            'homework_tasks', 'homework_submissions',
            'study_plans', 'plan_templates', 'plan_tasks', 'plan_goals', 'plan_progress',
            'supervision_logs', 'weakness_tags', 'student_stats',
            'module_categories', 'questions', 'mistakes', 'mistake_reviews',
            'workbook_templates', 'workbooks', 'workbook_pages', 'workbook_items',
        ]
        
        for table_name in import_order:
            if table_name not in xl.sheet_names:
                continue
            
            try:
                df = pd.read_excel(xl, sheet_name=table_name)
                if len(df) == 0:
                    continue
                
                # 清空表并重新插入（简单粗暴但有效）
                # 注意：这会删除现有数据！
                # db.session.execute(text(f'DELETE FROM {table_name}'))
                
                # 逐行插入或更新
                count = 0
                for _, row in df.iterrows():
                    # 转换为字典，处理NaN值
                    data = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.isna(val):
                            data[col] = None
                        else:
                            data[col] = val
                    
                    if 'id' in data and data['id'] is not None:
                        # 检查是否存在
                        result = db.session.execute(
                            text(f"SELECT id FROM {table_name} WHERE id = :id"),
                            {'id': int(data['id'])}
                        ).fetchone()
                        
                        if result:
                            # 更新
                            set_clause = ', '.join([f"{k} = :{k}" for k in data.keys() if k != 'id'])
                            if set_clause:
                                db.session.execute(
                                    text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id"),
                                    data
                                )
                        else:
                            # 插入
                            cols = ', '.join(data.keys())
                            vals = ', '.join([f":{k}" for k in data.keys()])
                            db.session.execute(
                                text(f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"),
                                data
                            )
                        count += 1
                
                if count > 0:
                    results.append(f'{table_name}: {count}条')
                    
            except Exception as e:
                print(f"导入表 {table_name} 失败: {e}")
                continue
        
        db.session.commit()
        
        message = '导入完成！\n' + '\n'.join(results) if results else '没有数据被导入'
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})
