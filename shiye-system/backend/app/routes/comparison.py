"""
地区对比路由
"""
from flask import Blueprint, render_template, request
from app.services.analysis_service import AnalysisService

comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')


@comparison_bp.route('/cities')
def cities():
    """16地市对比"""
    city_data = AnalysisService.get_city_comparison_data()
    
    return render_template('comparison/cities.html', city_data=city_data)
