"""
竞争力评估路由
"""
from flask import Blueprint, render_template, request, jsonify
from app.services.competitiveness_service import CompetitivenessService

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')


@evaluation_bp.route('/')
def index():
    """竞争力评估首页"""
    return render_template('evaluation/index.html')


@evaluation_bp.route('/result', methods=['POST'])
def result():
    """评估结果"""
    user_profile = {
        'education': request.form.get('education'),
        'major': request.form.get('major'),
        'graduation_status': request.form.get('graduation_status'),
        'estimated_score': int(request.form.get('estimated_score', 130)),
        'political_status': request.form.get('political_status'),
        'special_status': request.form.get('special_status'),
        'has_work_experience': request.form.get('has_work_experience') == 'on',
        'preferred_cities': request.form.getlist('cities'),
        'base_layer_willing': request.form.get('base_layer_willing') == 'on'
    }
    
    evaluation = CompetitivenessService.evaluate(user_profile)
    
    return render_template('evaluation/result.html',
                         user_profile=user_profile,
                         evaluation=evaluation)
