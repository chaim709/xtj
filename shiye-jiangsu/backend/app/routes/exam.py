"""
考试大纲和备考指南路由
"""
from flask import Blueprint, render_template

exam_bp = Blueprint('exam', __name__, url_prefix='/exam')


@exam_bp.route('/syllabus')
def syllabus():
    """考试大纲总览"""
    
    # 五大类别详细信息
    exam_categories = {
        'A': {
            'name': '综合管理类（A类）',
            'icon': '📋',
            'color': 'blue',
            '适用岗位': ['行政管理', '办公文秘', '党政办公室', '综合事务管理'],
            'difficulty': 4,
            'study_time': '3-6个月',
            'subjects': {
                '职业能力倾向测验': {
                    'time': '90分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '常识判断', 'questions': '约20题', 'time': '10分钟', 'tips': '快速作答，不纠结'},
                        {'name': '言语理解与表达', 'questions': '约30题', 'time': '25分钟', 'tips': '语感优先，适当跳过'},
                        {'name': '数量关系', 'questions': '约10题', 'time': '12分钟', 'tips': '先易后难，可放弃'},
                        {'name': '判断推理', 'questions': '约30题', 'time': '25分钟', 'tips': '重点模块，稳扎稳打'},
                        {'name': '资料分析', 'questions': '约15题', 'time': '18分钟', 'tips': '最重要，必须拿分'}
                    ]
                },
                '综合应用能力': {
                    'time': '120分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '案例分析题', 'score': '约40分', 'tips': '分析问题、提出对策'},
                        {'name': '公文写作题', 'score': '约30分', 'tips': '格式规范、内容完整'},
                        {'name': '综合分析题', 'score': '约80分', 'tips': '逻辑清晰、论证充分'}
                    ]
                }
            },
            'key_points': [
                '范围广泛，需要全面复习',
                '资料分析是得分重点',
                '公文写作要掌握格式',
                '案例分析要有管理思维'
            ],
            'resources': [
                '华图综合管理类教材',
                '中公A类专项题库',
                '历年真题集（2020-2025）'
            ]
        },
        'B': {
            'name': '社会科学专技类（B类）',
            'icon': '📖',
            'color': 'purple',
            '适用岗位': ['经济、新闻、律师', '文博、图书、艺术', '出版、会计、翻译'],
            'difficulty': 4,
            'study_time': '2-4个月',
            'subjects': {
                '职业能力倾向测验': {
                    'time': '90分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '常识判断', 'questions': '约25题', 'time': '12分钟', 'tips': '侧重社会科学'},
                        {'name': '言语理解与表达', 'questions': '约30题', 'time': '25分钟', 'tips': '人文性强'},
                        {'name': '数量分析', 'questions': '约15题', 'time': '18分钟', 'tips': '数据分析为主'},
                        {'name': '判断推理', 'questions': '约35题', 'time': '28分钟', 'tips': '逻辑推理'},
                        {'name': '综合分析', 'questions': '约10题', 'time': '7分钟', 'tips': '综合判断'}
                    ]
                },
                '综合应用能力': {
                    'time': '120分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '概念分析题', 'score': '约30分', 'tips': '概念辨析、关系分析'},
                        {'name': '校阅改错题', 'score': '约20分', 'tips': '语言文字功底'},
                        {'name': '论证评价题', 'score': '约40分', 'tips': '逻辑思维能力'},
                        {'name': '材料分析题', 'score': '约30分', 'tips': '综合分析能力'},
                        {'name': '写作题', 'score': '约30分', 'tips': '学术写作能力'}
                    ]
                }
            },
            'key_points': [
                '侧重人文社科知识',
                '强调逻辑思维和论证',
                '校阅改错需要扎实语言功底',
                '写作要有学术性'
            ],
            'resources': [
                '华图社会科学专技类教材',
                '中公B类专项训练',
                '论证评价专项突破'
            ]
        },
        'C': {
            'name': '自然科学专技类（C类）',
            'icon': '🔬',
            'color': 'green',
            '适用岗位': ['工程、农技、统计', '船舶、民航飞行', '实验员、技术员'],
            'difficulty': 3,
            'study_time': '2-3个月',
            'subjects': {
                '职业能力倾向测验': {
                    'time': '90分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '常识判断', 'questions': '约20题', 'time': '10分钟', 'tips': '侧重自然科学'},
                        {'name': '言语理解与表达', 'questions': '约25题', 'time': '20分钟', 'tips': '科技文献理解'},
                        {'name': '判断推理', 'questions': '约35题', 'time': '28分钟', 'tips': '科学思维'},
                        {'name': '综合分析', 'questions': '约15题', 'time': '15分钟', 'tips': '数据处理'},
                        {'name': '数量分析', 'questions': '约20题', 'time': '17分钟', 'tips': '数学运算'}
                    ]
                },
                '综合应用能力': {
                    'time': '120分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '科技文献阅读题', 'score': '约50分', 'tips': '快速提取信息'},
                        {'name': '论证评价题', 'score': '约30分', 'tips': '科学论证分析'},
                        {'name': '科技实务题', 'score': '约40分', 'tips': '实践应用能力'},
                        {'name': '材料作文题', 'score': '约30分', 'tips': '科技写作'}
                    ]
                }
            },
            'key_points': [
                '自然科学基础知识重要',
                '科技文献阅读能力关键',
                '数据分析和计算能力必备',
                '实践应用题要多练习'
            ],
            'resources': [
                '华图自然科学专技类教材',
                '中公C类专项题库',
                '科技文献阅读训练'
            ]
        },
        'D': {
            'name': '中小学教师类（D类）',
            'icon': '🎓',
            'color': 'yellow',
            '适用岗位': ['中小学教师', '中专教师', '教育机构教师'],
            'difficulty': 3,
            'study_time': '2-3个月',
            '细分': ['D1-小学教师岗位', 'D2-中学教师岗位'],
            'subjects': {
                '职业能力倾向测验': {
                    'time': '90分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '常识判断', 'questions': '约25题', 'time': '12分钟', 'tips': '侧重教育领域'},
                        {'name': '言语理解与表达', 'questions': '约30题', 'time': '25分钟', 'tips': '教育文本理解'},
                        {'name': '判断推理', 'questions': '约30题', 'time': '23分钟', 'tips': '教育逻辑'},
                        {'name': '数量分析', 'questions': '约10题', 'time': '10分钟', 'tips': '教育数据'},
                        {'name': '策略选择', 'questions': '约20题', 'time': '20分钟', 'tips': '教育情境应对'}
                    ]
                },
                '综合应用能力': {
                    'time': '120分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '教育情境辨析题', 'score': '约30分', 'tips': '师德和职业认知'},
                        {'name': '教育方案设计题', 'score': '约40分', 'tips': '教学设计能力'},
                        {'name': '教育活动分析题', 'score': '约40分', 'tips': '教育活动组织'},
                        {'name': '教学设计题', 'score': '约40分', 'tips': '分学段设计'}
                    ]
                }
            },
            'key_points': [
                '教育理论知识是基础',
                '教学设计能力是重点',
                '策略选择是特色题型',
                '分学段准备很重要'
            ],
            'resources': [
                '华图教师类教材',
                '中公D类专项训练',
                '教学设计案例集'
            ]
        },
        'E': {
            'name': '医疗卫生类（E类）',
            'icon': '🏥',
            'color': 'red',
            '适用岗位': ['医疗卫生机构专业技术岗位'],
            'difficulty': 5,
            'study_time': '4-6个月',
            '细分': ['E1-中医临床', 'E2-西医临床', 'E3-药剂', 'E4-护理', 'E5-医学技术', 'E6-公共卫生管理'],
            'subjects': {
                '职业能力倾向测验': {
                    'time': '90分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '常识判断', 'questions': '约20题', 'time': '10分钟', 'tips': '侧重医学知识'},
                        {'name': '言语理解与表达', 'questions': '约25题', 'time': '20分钟', 'tips': '医学文献'},
                        {'name': '判断推理', 'questions': '约30题', 'time': '23分钟', 'tips': '医学逻辑'},
                        {'name': '数量分析', 'questions': '约15题', 'time': '12分钟', 'tips': '医学数据'},
                        {'name': '策略选择', 'questions': '约25题', 'time': '25分钟', 'tips': '医疗情境'}
                    ]
                },
                '综合应用能力': {
                    'time': '120分钟',
                    'score': '150分',
                    'modules': [
                        {'name': '医学专业知识题', 'score': '约60分', 'tips': '基础医学+临床'},
                        {'name': '病例分析题', 'score': '约50分', 'tips': '临床思维'},
                        {'name': '实务题', 'score': '约40分', 'tips': '专业实践'}
                    ]
                }
            },
            'key_points': [
                '医学基础知识是核心',
                '临床思维能力是重点',
                '分小类准备很重要',
                '实践经验有优势'
            ],
            'resources': [
                '华图医疗卫生类教材',
                '中公E类专项题库',
                '临床病例分析训练'
            ]
        }
    }
    
    return render_template('exam/syllabus.html', exam_categories=exam_categories)


@exam_bp.route('/category/<category_id>')
def category_detail(category_id):
    """考试类别详情"""
    
    # 这里可以根据category_id返回更详细的内容
    return render_template('exam/category_detail.html', category_id=category_id.upper())


@exam_bp.route('/preparation')
def preparation():
    """备考指南"""
    
    # 备考阶段
    preparation_stages = [
        {
            'stage': '基础阶段',
            'duration': '第1-2个月',
            'goal': '全面了解考试内容，掌握基础知识',
            'tasks': [
                '系统学习教材，建立知识框架',
                '完成章节练习，巩固基础',
                '做3-5套真题，了解题型',
                '制定学习计划，培养习惯'
            ],
            'target': '行测60分 + 综合50分 = 110分'
        },
        {
            'stage': '强化阶段',
            'duration': '第3-4个月',
            'goal': '提升做题速度和准确率',
            'tasks': [
                '专项突破弱项模块',
                '每周2-3套模拟题',
                '总结错题和知识点',
                '练习答题技巧'
            ],
            'target': '行测70分 + 综合60分 = 130分'
        },
        {
            'stage': '冲刺阶段',
            'duration': '第5个月',
            'goal': '达到目标分数，保持状态',
            'tasks': [
                '每周3-4套全真模拟',
                '限时训练，提升速度',
                '薄弱环节强化',
                '考前押题练习'
            ],
            'target': '行测75分 + 综合65分 = 140分'
        },
        {
            'stage': '考前阶段',
            'duration': '考前1个月',
            'goal': '保持状态，调整心态',
            'tasks': [
                '回顾错题本和笔记',
                '每周1-2套模拟保持手感',
                '调整作息，适应考试时间',
                '准备考试用品和证件'
            ],
            'target': '稳定在目标分数±5分'
        }
    ]
    
    # 各模块备考技巧
    module_tips = {
        '常识判断': {
            'icon': '📚',
            'importance': '中等',
            'score_rate': '60-70%',
            'tips': [
                '关注时政热点，每天看新闻',
                '积累党的创新理论知识',
                '掌握法律、经济、管理基础',
                '多刷题，见得多自然会'
            ]
        },
        '言语理解': {
            'icon': '📝',
            'importance': '重要',
            'score_rate': '70-80%',
            'tips': [
                '大量练习培养语感',
                '总结常见词语搭配',
                '注意逻辑关系词（因此、但是等）',
                '主旨题找中心句'
            ]
        },
        '数量关系': {
            'icon': '🔢',
            'importance': '一般',
            'score_rate': '40-60%',
            'tips': [
                '掌握基础公式和方法',
                '练习快速计算技巧',
                '学会代入排除法',
                '难题可以战略性放弃'
            ]
        },
        '判断推理': {
            'icon': '🧩',
            'importance': '重要',
            'score_rate': '70-85%',
            'tips': [
                '图形推理多总结规律',
                '定义判断看清关键词',
                '类比推理注意内在逻辑',
                '逻辑判断画图辅助'
            ]
        },
        '资料分析': {
            'icon': '📊',
            'importance': '极重要',
            'score_rate': '85-95%',
            'tips': [
                '这是拉分项，必须拿高分',
                '练习快速阅读和定位',
                '掌握估算技巧',
                '熟记常用公式'
            ]
        }
    }
    
    return render_template('exam/preparation.html', 
                         preparation_stages=preparation_stages,
                         module_tips=module_tips)
