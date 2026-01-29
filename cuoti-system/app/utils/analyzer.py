# -*- coding: utf-8 -*-
"""题目AI分析器"""
import os
import re
import json
from datetime import datetime


# 知识点分类体系
CATEGORY_KEYWORDS = {
    '言语理解与表达': {
        'keywords': ['阅读', '理解', '填空', '成语', '词语', '语句', '文段', '作者', '意图', '主旨'],
        'subcategories': {
            '片段阅读': ['主旨', '意图', '细节', '标题', '态度'],
            '逻辑填空': ['成语', '词语', '填空'],
            '语句表达': ['排序', '衔接', '语句'],
        }
    },
    '判断推理': {
        'keywords': ['推理', '判断', '图形', '定义', '类比', '逻辑'],
        'subcategories': {
            '图形推理': ['图形', '图案', '规律'],
            '定义判断': ['定义', '符合', '属于'],
            '类比推理': ['类比', '对应', '关系'],
            '逻辑判断': ['逻辑', '推理', '结论', '假设'],
        }
    },
    '数量关系': {
        'keywords': ['数量', '数字', '计算', '求', '多少', '几'],
        'subcategories': {
            '数字推理': ['数列', '规律'],
            '数学运算': ['计算', '求解', '工程', '行程', '利润'],
        }
    },
    '资料分析': {
        'keywords': ['资料', '增长', '比重', '增长率', '同比', '环比', '百分比', '%'],
        'subcategories': {
            '增长类': ['增长率', '增长量', '增速'],
            '比重类': ['比重', '占比', '份额'],
            '综合分析': ['综合', '判断'],
        }
    },
    '常识判断': {
        'keywords': ['常识', '知识', '历史', '政治', '法律', '科技', '地理'],
        'subcategories': {
            '政治': ['政治', '党', '政府', '制度'],
            '法律': ['法律', '法规', '权利', '义务', '犯罪'],
            '经济': ['经济', '市场', '货币', '通胀'],
            '历史': ['历史', '朝代', '战争', '事件'],
            '地理': ['地理', '气候', '地形', '省份'],
            '科技': ['科技', '科学', '技术', '发明'],
        }
    }
}

# 难度关键词
DIFFICULTY_INDICATORS = {
    '简单': ['直接', '明显', '基础', '常见'],
    '中等': ['需要', '分析', '理解'],
    '困难': ['复杂', '综合', '多步', '陷阱']
}


def analyze_question_local(question):
    """
    本地规则匹配分析题目
    
    返回：补充分析信息后的题目
    """
    stem = question.get('stem', '')
    options = question.get('options', {})
    
    # 合并所有文本用于分析
    full_text = stem + ' '.join(options.values())
    
    result = {
        'category': None,
        'subcategory': None,
        'knowledge_point': None,
        'difficulty': '中等',
        'analysis_source': 'local_rules'
    }
    
    # 匹配一级分类
    max_score = 0
    for category, config in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in config['keywords'] if kw in full_text)
        if score > max_score:
            max_score = score
            result['category'] = category
            
            # 匹配二级分类
            for subcat, sub_keywords in config['subcategories'].items():
                if any(kw in full_text for kw in sub_keywords):
                    result['subcategory'] = subcat
                    break
    
    # 如果没有匹配到，默认为常识判断
    if not result['category']:
        result['category'] = '常识判断'
    
    # 估算难度
    for difficulty, indicators in DIFFICULTY_INDICATORS.items():
        if any(ind in full_text for ind in indicators):
            result['difficulty'] = difficulty
            break
    
    # 提取可能的知识点（从题目中提取关键概念）
    # 这里使用简单的启发式方法
    quoted_terms = re.findall(r'[""「」『』【】]([^""「」『』【】]+)[""「」『』【】]', stem)
    if quoted_terms:
        result['knowledge_point'] = '、'.join(quoted_terms[:3])
    
    return result


def analyze_with_ai(question, api_config=None):
    """
    使用AI API分析题目
    
    api_config: {
        'provider': 'deepseek' | 'openai',
        'api_key': 'xxx',
        'base_url': 'xxx' (可选)
    }
    """
    if not api_config or not api_config.get('api_key'):
        # 无API配置，使用本地分析
        return analyze_question_local(question)
    
    try:
        from openai import OpenAI
        
        provider = api_config.get('provider', 'deepseek')
        
        if provider == 'deepseek':
            client = OpenAI(
                api_key=api_config['api_key'],
                base_url=api_config.get('base_url', 'https://api.deepseek.com/v1')
            )
            model = 'deepseek-chat'
        else:
            client = OpenAI(api_key=api_config['api_key'])
            model = api_config.get('model', 'gpt-3.5-turbo')
        
        # 构建prompt
        question_text = f"""
题干：{question.get('stem', '')}
选项：
A. {question.get('options', {}).get('A', '')}
B. {question.get('options', {}).get('B', '')}
C. {question.get('options', {}).get('C', '')}
D. {question.get('options', {}).get('D', '')}
"""
        
        prompt = f"""分析以下公务员考试题目，返回JSON格式结果：

{question_text}

请返回以下JSON格式（仅返回JSON，不要其他内容）：
{{
  "answer": "正确答案(A/B/C/D)",
  "analysis": "解析说明",
  "category": "一级分类(言语理解与表达/判断推理/数量关系/资料分析/常识判断)",
  "subcategory": "二级分类",
  "knowledge_point": "知识点",
  "difficulty": "难度(简单/中等/困难)"
}}
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是公务员考试专家，擅长分析行测题目。请用JSON格式回复。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # 提取JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content.strip())
        result['analysis_source'] = 'ai'
        return result
        
    except Exception as e:
        # AI分析失败，回退到本地分析
        local_result = analyze_question_local(question)
        local_result['analysis_error'] = str(e)
        return local_result


def batch_analyze(questions, api_config=None, use_ai=False):
    """
    批量分析题目
    
    返回：分析结果列表
    """
    results = []
    
    for q in questions:
        if use_ai and api_config:
            analysis = analyze_with_ai(q, api_config)
        else:
            analysis = analyze_question_local(q)
        
        # 合并分析结果到原题目
        q.update({
            'category': analysis.get('category') or q.get('category') or q.get('section'),
            'subcategory': analysis.get('subcategory') or q.get('subcategory', ''),
            'knowledge_point': analysis.get('knowledge_point') or q.get('knowledge_point', ''),
            'difficulty': analysis.get('difficulty') or q.get('difficulty', '中等'),
            'analysis_source': analysis.get('analysis_source', 'local'),
        })
        
        # 如果AI提供了答案和解析，也更新
        if analysis.get('answer') and not q.get('answer'):
            q['answer'] = analysis['answer']
        if analysis.get('analysis') and not q.get('analysis'):
            q['analysis'] = analysis['analysis']
        
        results.append(q)
    
    return results
