# -*- coding: utf-8 -*-
"""
扣子智能体API
"""
import requests
from flask import Blueprint, jsonify, request, current_app, g
from app.routes.wx_api import require_student_auth

coze_api_bp = Blueprint('coze_api', __name__, url_prefix='/api/v1/coze')


@coze_api_bp.route('/chat', methods=['POST'])
@require_student_auth
def chat_with_coze():
    """
    与扣子智能体对话
    
    Request Body:
        message: 用户消息
        conversation_id: 会话ID（可选）
    
    Returns:
        扣子回复
    """
    student = g.student
    data = request.get_json() or {}
    
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id', '')
    
    if not user_message:
        return jsonify({
            'success': False,
            'message': '消息不能为空'
        }), 400
    
    # 获取扣子配置
    coze_bot_id = current_app.config.get('COZE_BOT_ID', '')
    coze_token = current_app.config.get('COZE_TOKEN', '')
    
    if not coze_bot_id or not coze_token:
        # 开发模式：返回模拟回复
        return jsonify({
            'success': True,
            'data': {
                'reply': f'【模拟回复】{student.name}同学，我收到了您的消息：{user_message}',
                'conversationId': 'dev_conv_123'
            }
        })
    
    # 构建学员上下文
    context = {
        'student_name': student.name,
        'class_name': student.class_name,
        'exam_type': student.exam_type,
        'target_position': student.target_position,
        'checkin_days': student.total_checkin_days or 0
    }
    
    try:
        # 调用扣子API
        coze_url = 'https://api.coze.cn/v1/conversation/message/list'
        headers = {
            'Authorization': f'Bearer {coze_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'bot_id': coze_bot_id,
            'user_id': str(student.id),
            'conversation_id': conversation_id,
            'query': user_message,
            'additional_messages': [
                {
                    'role': 'assistant',
                    'content': f'学员信息：{context}'
                }
            ]
        }
        
        resp = requests.post(coze_url, json=payload, headers=headers, timeout=30)
        result = resp.json()
        
        # 解析扣子响应
        if result.get('code') == 0:
            messages = result.get('data', {}).get('messages', [])
            reply = messages[-1].get('content', '抱歉，我没有理解') if messages else '抱歉，我没有理解'
            
            return jsonify({
                'success': True,
                'data': {
                    'reply': reply,
                    'conversationId': result.get('data', {}).get('conversation_id', '')
                }
            })
        else:
            raise Exception(result.get('msg', '扣子API调用失败'))
    
    except Exception as e:
        current_app.logger.error(f'扣子对话失败: {e}')
        return jsonify({
            'success': False,
            'message': '对话失败，请稍后重试',
            'error_code': 'COZE_ERROR'
        }), 500
