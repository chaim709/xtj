# -*- coding: utf-8 -*-
"""
微信小程序API路由
处理微信登录、手机号绑定、订阅消息等
"""
import jwt
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, jsonify, request, current_app, g
from app import db
from app.models.student import Student

wx_api_bp = Blueprint('wx_api', __name__, url_prefix='/api/v1/wx')


def generate_token(student_id):
    """生成JWT Token"""
    payload = {
        'student_id': student_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(
        payload, 
        current_app.config.get('SECRET_KEY', 'dev-secret-key'), 
        algorithm='HS256'
    )


def require_student_auth(f):
    """学员认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        if not token:
            return jsonify({
                'success': False,
                'message': '未登录',
                'error_code': 'UNAUTHORIZED'
            }), 401
        
        try:
            payload = jwt.decode(
                token, 
                current_app.config.get('SECRET_KEY', 'dev-secret-key'), 
                algorithms=['HS256']
            )
            g.student_id = payload['student_id']
            g.student = Student.query.get(payload['student_id'])
            if not g.student:
                return jsonify({
                    'success': False,
                    'message': '用户不存在',
                    'error_code': 'USER_NOT_FOUND'
                }), 401
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': '登录已过期，请重新登录',
                'error_code': 'TOKEN_EXPIRED'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': '无效的登录凭证',
                'error_code': 'INVALID_TOKEN'
            }), 401
        
        return f(*args, **kwargs)
    return decorated


@wx_api_bp.route('/login', methods=['POST'])
def wx_login():
    """
    微信登录
    
    接收小程序wx.login()获取的code，换取openid
    如果openid已绑定学员，返回token
    如果未绑定，返回needBind标识
    
    Request Body:
        code: 微信登录code
    
    Returns:
        已绑定: {success: true, data: {token, userInfo}}
        未绑定: {success: true, data: {needBind: true, sessionKey}}
    """
    data = request.get_json() or {}
    code = data.get('code')
    
    if not code:
        return jsonify({
            'success': False,
            'message': '缺少登录code',
            'error_code': 'MISSING_CODE'
        }), 400
    
    # 获取微信配置
    appid = current_app.config.get('WX_APPID', '')
    secret = current_app.config.get('WX_SECRET', '')
    
    if not appid or not secret:
        # 开发模式：模拟登录
        current_app.logger.warning('微信AppID/Secret未配置，使用开发模式')
        
        # 开发模式下，使用固定的openid进行测试
        mock_openid = f'dev_openid_{code[:8]}'
        
        # 查找是否已绑定
        student = Student.query.filter_by(wx_openid=mock_openid).first()
        
        if student:
            token = generate_token(student.id)
            return jsonify({
                'success': True,
                'data': {
                    'token': token,
                    'userInfo': {
                        'id': student.id,
                        'name': student.name,
                        'phone': student.phone[:3] + '****' + student.phone[-4:] if student.phone else '',
                        'className': student.class_name
                    }
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'needBind': True,
                    'sessionKey': f'dev_session_{code[:8]}',
                    'openid': mock_openid
                }
            })
    
    # 正式环境：调用微信API
    try:
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': appid,
            'secret': secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        resp = requests.get(wx_url, params=params, timeout=10)
        result = resp.json()
        
        if 'errcode' in result and result['errcode'] != 0:
            return jsonify({
                'success': False,
                'message': f'微信登录失败: {result.get("errmsg", "未知错误")}',
                'error_code': 'WX_LOGIN_FAILED'
            }), 400
        
        openid = result.get('openid')
        session_key = result.get('session_key')
        unionid = result.get('unionid')
        
        # 查找是否已绑定学员
        student = Student.query.filter_by(wx_openid=openid).first()
        
        if student:
            # 已绑定，返回token
            token = generate_token(student.id)
            return jsonify({
                'success': True,
                'data': {
                    'token': token,
                    'userInfo': {
                        'id': student.id,
                        'name': student.name,
                        'phone': student.phone[:3] + '****' + student.phone[-4:] if student.phone else '',
                        'className': student.class_name
                    }
                }
            })
        else:
            # 未绑定，需要绑定手机号
            return jsonify({
                'success': True,
                'data': {
                    'needBind': True,
                    'sessionKey': session_key,
                    'openid': openid
                }
            })
    
    except requests.RequestException as e:
        current_app.logger.error(f'微信API请求失败: {e}')
        return jsonify({
            'success': False,
            'message': '微信服务暂时不可用',
            'error_code': 'WX_SERVICE_ERROR'
        }), 500


@wx_api_bp.route('/bind-phone', methods=['POST'])
def bind_phone():
    """
    绑定手机号
    
    接收小程序getPhoneNumber获取的加密数据，解密后匹配学员
    
    Request Body:
        openid: 微信openid
        sessionKey: 会话密钥
        encryptedData: 加密数据（正式环境）
        iv: 加密向量（正式环境）
        phone: 手机号（开发环境直接传入）
    
    Returns:
        绑定成功: {success: true, data: {token, userInfo}}
        绑定失败: {success: false, message: '错误信息'}
    """
    data = request.get_json() or {}
    openid = data.get('openid')
    session_key = data.get('sessionKey')
    phone = data.get('phone')  # 开发环境直接传手机号
    
    if not openid:
        return jsonify({
            'success': False,
            'message': '缺少openid',
            'error_code': 'MISSING_OPENID'
        }), 400
    
    # 开发模式或正式解密
    if not phone:
        # 正式环境需要解密
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        
        if not encrypted_data or not iv or not session_key:
            return jsonify({
                'success': False,
                'message': '缺少解密参数',
                'error_code': 'MISSING_DECRYPT_PARAMS'
            }), 400
        
        # TODO: 实现AES解密获取手机号
        # 这里需要使用pycryptodome库进行解密
        return jsonify({
            'success': False,
            'message': '请在开发模式下直接传入手机号',
            'error_code': 'DECRYPT_NOT_IMPLEMENTED'
        }), 501
    
    # 通过手机号查找学员
    student = Student.query.filter_by(phone=phone).first()
    
    if not student:
        return jsonify({
            'success': False,
            'message': f'未找到手机号为 {phone} 的学员，请确认您已在机构报名',
            'error_code': 'STUDENT_NOT_FOUND'
        }), 404
    
    # 检查是否已被其他微信绑定
    if student.wx_openid and student.wx_openid != openid:
        return jsonify({
            'success': False,
            'message': '该学员账号已绑定其他微信',
            'error_code': 'ALREADY_BINDIED'
        }), 400
    
    # 绑定openid
    try:
        student.wx_openid = openid
        db.session.commit()
        
        # 生成token
        token = generate_token(student.id)
        
        return jsonify({
            'success': True,
            'message': '绑定成功',
            'data': {
                'token': token,
                'userInfo': {
                    'id': student.id,
                    'name': student.name,
                    'phone': phone[:3] + '****' + phone[-4:],
                    'className': student.class_name
                }
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'绑定失败: {e}')
        return jsonify({
            'success': False,
            'message': '绑定失败，请重试',
            'error_code': 'BINDIED_FAILED'
        }), 500


@wx_api_bp.route('/check-bindied', methods=['GET'])
def check_bindied():
    """检查openid是否已绑定"""
    openid = request.args.get('openid')
    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'}), 400
    
    student = Student.query.filter_by(wx_openid=openid).first()
    return jsonify({
        'success': True,
        'data': {
            'bindied': student is not None
        }
    })
