#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题目导入脚本

使用方法:
    python3 scripts/import_questions.py --json <json文件路径>
    python3 scripts/import_questions.py --demo  # 导入演示数据
"""
import os
import sys
import json
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def import_from_json(json_file):
    """从JSON文件导入题目"""
    from app import create_app, db
    from app.models import Question
    
    app = create_app('development')
    
    with app.app_context():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions_data = data.get('questions', data) if isinstance(data, dict) else data
        
        if not isinstance(questions_data, list):
            print("JSON格式错误，需要questions数组")
            return
        
        # 获取当前最大ID
        max_id = db.session.query(db.func.max(Question.id)).scalar() or 0
        
        imported = 0
        for i, q in enumerate(questions_data):
            try:
                # 生成UID
                uid = f'Q-{str(max_id + i + 1).zfill(5)}'
                
                # 处理选项
                options = q.get('options', {})
                if isinstance(options, dict):
                    option_a = options.get('A', '')
                    option_b = options.get('B', '')
                    option_c = options.get('C', '')
                    option_d = options.get('D', '')
                else:
                    option_a = q.get('option_a', '')
                    option_b = q.get('option_b', '')
                    option_c = q.get('option_c', '')
                    option_d = q.get('option_d', '')
                
                # 处理分类
                category_data = q.get('category', {})
                if isinstance(category_data, dict):
                    category = category_data.get('level1', '')
                    subcategory = category_data.get('level2', '')
                    knowledge_point = category_data.get('level3', '')
                else:
                    category = q.get('category', '')
                    subcategory = q.get('subcategory', '')
                    knowledge_point = q.get('knowledge_point', '')
                
                question = Question(
                    uid=uid,
                    stem=q.get('stem', ''),
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    answer=q.get('answer', ''),
                    analysis=q.get('analysis', ''),
                    category=category,
                    subcategory=subcategory,
                    knowledge_point=knowledge_point,
                    source=q.get('source', q.get('source_file', '')),
                    difficulty=q.get('difficulty', '中等')
                )
                
                db.session.add(question)
                imported += 1
                
                if imported % 100 == 0:
                    db.session.commit()
                    print(f"已导入 {imported} 题...")
            
            except Exception as e:
                print(f"导入题目 {i+1} 失败: {e}")
                continue
        
        db.session.commit()
        print(f"\n导入完成！共导入 {imported} 道题目")


def import_demo_data():
    """导入演示数据"""
    from app import create_app, db
    from app.models import Question
    
    app = create_app('development')
    
    demo_questions = [
        {
            "stem": "根据《宪法》规定，下列关于我国国家机构的说法正确的是？",
            "option_a": "国务院是最高国家权力机关的执行机关",
            "option_b": "全国人大常委会是最高国家权力机关",
            "option_c": "国家主席可以直接领导国务院",
            "option_d": "地方各级人民政府是地方各级人大的执行机关",
            "answer": "A",
            "analysis": "根据宪法规定，国务院即中央人民政府，是最高国家权力机关的执行机关，是最高国家行政机关。",
            "category": "常识判断",
            "subcategory": "法律",
            "knowledge_point": "宪法"
        },
        {
            "stem": "下列诗句描写的季节与其他三项不同的是？",
            "option_a": "忽如一夜春风来，千树万树梨花开",
            "option_b": "小荷才露尖尖角，早有蜻蜓立上头",
            "option_c": "接天莲叶无穷碧，映日荷花别样红",
            "option_d": "稻花香里说丰年，听取蛙声一片",
            "answer": "A",
            "analysis": "A项描写的是冬季雪景，用梨花比喻雪花。B、C、D项都描写的是夏季景象。",
            "category": "常识判断",
            "subcategory": "历史",
            "knowledge_point": "文学常识"
        },
        {
            "stem": "某商场举办促销活动，所有商品打八折销售。小王购买了一件原价500元的商品，实际支付多少元？",
            "option_a": "400元",
            "option_b": "450元",
            "option_c": "350元",
            "option_d": "300元",
            "answer": "A",
            "analysis": "打八折就是原价乘以0.8，500×0.8=400元。",
            "category": "数量关系",
            "subcategory": "数学运算",
            "knowledge_point": "折扣问题"
        },
        {
            "stem": "所有参加考试的学生都通过了考试。小明参加了考试。由此可以推出：",
            "option_a": "小明通过了考试",
            "option_b": "小明没有通过考试",
            "option_c": "有的学生没有通过考试",
            "option_d": "不能确定小明是否通过考试",
            "answer": "A",
            "analysis": "根据三段论推理：大前提-所有参加考试的学生都通过了考试，小前提-小明参加了考试，结论-小明通过了考试。",
            "category": "判断推理",
            "subcategory": "逻辑判断",
            "knowledge_point": "三段论"
        },
        {
            "stem": "\"未雨绸缪\"这个成语中\"绸缪\"的意思是？",
            "option_a": "紧密缠绕",
            "option_b": "计划准备",
            "option_c": "修缮房屋",
            "option_d": "忧愁烦恼",
            "answer": "C",
            "analysis": "\"未雨绸缪\"出自《诗经》，原意是在下雨之前修缮房屋。绸缪：修缮。比喻事先做好准备。",
            "category": "言语理解与表达",
            "subcategory": "选词填空",
            "knowledge_point": "成语辨析"
        },
        {
            "stem": "2024年中央经济工作会议提出，要坚持稳中求进、以进促稳、先立后破。这体现了唯物辩证法的什么原理？",
            "option_a": "矛盾的普遍性与特殊性相互联结",
            "option_b": "主次矛盾相互依存相互影响",
            "option_c": "两点论与重点论的统一",
            "option_d": "矛盾双方在一定条件下相互转化",
            "answer": "C",
            "analysis": "\"稳中求进\"体现了在坚持稳定的同时追求发展，既要看到稳的重要性，也要看到进的必要性，是两点论与重点论的统一。",
            "category": "常识判断",
            "subcategory": "政治",
            "knowledge_point": "哲学"
        },
        {
            "stem": "下列关于我国地理知识的说法，正确的是？",
            "option_a": "我国地势西高东低，呈阶梯状分布",
            "option_b": "长江是我国第一大河，也是世界第一大河",
            "option_c": "青藏高原是世界上面积最大的高原",
            "option_d": "我国最大的淡水湖是洞庭湖",
            "answer": "A",
            "analysis": "我国地势西高东低，呈三级阶梯状分布。B项长江是世界第三大河；C项青藏高原是世界最高高原，面积最大的是南极高原；D项我国最大淡水湖是鄱阳湖。",
            "category": "常识判断",
            "subcategory": "地理",
            "knowledge_point": "中国地理"
        },
        {
            "stem": "根据资料，2023年某市GDP同比增长8%，达到5400亿元。则2022年该市GDP为多少亿元？",
            "option_a": "5000亿元",
            "option_b": "4968亿元",
            "option_c": "5100亿元",
            "option_d": "4800亿元",
            "answer": "A",
            "analysis": "设2022年GDP为x，则x×(1+8%)=5400，x=5400÷1.08=5000亿元。",
            "category": "资料分析",
            "subcategory": "综合分析",
            "knowledge_point": "增长率计算"
        },
        {
            "stem": "合同法规定，当事人订立合同，采取要约、承诺方式。下列关于要约的说法，错误的是？",
            "option_a": "要约必须包含合同的主要条款",
            "option_b": "要约一经发出即发生法律效力",
            "option_c": "要约可以撤回",
            "option_d": "要约邀请不是要约",
            "answer": "B",
            "analysis": "要约到达受要约人时生效，而不是发出即生效。要约在到达受要约人之前可以撤回。",
            "category": "常识判断",
            "subcategory": "法律",
            "knowledge_point": "合同法"
        },
        {
            "stem": "光年是什么单位？",
            "option_a": "时间单位",
            "option_b": "长度单位",
            "option_c": "速度单位",
            "option_d": "质量单位",
            "answer": "B",
            "analysis": "光年是长度单位，是光在真空中一年所走的距离，约等于9.46万亿千米。",
            "category": "常识判断",
            "subcategory": "科技",
            "knowledge_point": "物理常识"
        }
    ]
    
    with app.app_context():
        for i, q in enumerate(demo_questions):
            question = Question(
                uid=f'Q-{str(i+1).zfill(5)}',
                stem=q['stem'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                answer=q['answer'],
                analysis=q['analysis'],
                category=q['category'],
                subcategory=q['subcategory'],
                knowledge_point=q['knowledge_point'],
                difficulty='中等'
            )
            db.session.add(question)
        
        db.session.commit()
        print(f"已导入 {len(demo_questions)} 道演示题目")


def main():
    parser = argparse.ArgumentParser(description='题目导入工具')
    parser.add_argument('--json', type=str, help='JSON文件路径')
    parser.add_argument('--demo', action='store_true', help='导入演示数据')
    
    args = parser.parse_args()
    
    if args.demo:
        import_demo_data()
    elif args.json:
        import_from_json(args.json)
    else:
        print("请指定 --json <文件路径> 或 --demo")
        print("示例:")
        print("  python3 scripts/import_questions.py --demo")
        print("  python3 scripts/import_questions.py --json data/questions.json")


if __name__ == '__main__':
    main()
