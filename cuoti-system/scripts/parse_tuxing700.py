#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形推理700题 专用解析器
解析超格教育的图形推理700题PDF
"""
import os
import sys
import json
import re
from datetime import datetime
from pdf2image import convert_from_path

# PDF路径
PDF_PATH = '/Users/chaim/CodeBuddy/公考项目/docs/错题收集系统/图形推理700题.pdf'
OUTPUT_DIR = 'data/parsed/图形推理700题'

# 答案数据（从PDF第261-264页手动提取）
ANSWERS = {
    # 挑战图推700题（一）1-20
    1: 'C', 2: 'C', 3: 'D', 4: 'A', 5: 'A',
    6: 'A', 7: 'D', 8: 'A', 9: 'B', 10: 'D',
    11: 'B', 12: 'D', 13: 'A', 14: 'A', 15: 'B',
    16: 'A', 17: 'C', 18: 'C', 19: 'B', 20: 'D',
    
    # 挑战图推700题（二）21-40
    21: 'B', 22: 'D', 23: 'A', 24: 'D', 25: 'B',
    26: 'C', 27: 'D', 28: 'A', 29: 'C', 30: 'D',
    31: 'B', 32: 'B', 33: 'B', 34: 'C', 35: 'C',
    36: 'C', 37: 'A', 38: 'A', 39: 'B', 40: 'A',
    
    # 挑战图推700题（三）41-60
    41: 'B', 42: 'C', 43: 'C', 44: 'D', 45: 'B',
    46: 'C', 47: 'C', 48: 'D', 49: 'C', 50: 'B',
    51: 'B', 52: 'B', 53: 'C', 54: 'A', 55: 'A',
    56: 'D', 57: 'D', 58: 'B', 59: 'B', 60: 'B',
    
    # 挑战图推700题（四）61-80
    61: 'D', 62: 'B', 63: 'B', 64: 'B', 65: 'D',
    66: 'D', 67: 'D', 68: 'B', 69: 'A', 70: 'B',
    71: 'D', 72: 'B', 73: 'C', 74: 'C', 75: 'C',
    76: 'C', 77: 'D', 78: 'A', 79: 'C', 80: 'C',
    
    # 挑战图推700题（五）81-100
    81: 'D', 82: 'A', 83: 'A', 84: 'C', 85: 'D',
    86: 'A', 87: 'B', 88: 'C', 89: 'B', 90: 'B',
    91: 'A', 92: 'D', 93: 'D', 94: 'B', 95: 'A',
    96: 'A', 97: 'B', 98: 'B', 99: 'B', 100: 'C',
    
    # 挑战图推700题（六）101-120
    101: 'A', 102: 'B', 103: 'A', 104: 'A', 105: 'B',
    106: 'D', 107: 'D', 108: 'B', 109: 'D', 110: 'B',
    111: 'C', 112: 'C', 113: 'D', 114: 'A', 115: 'D',
    116: 'D', 117: 'A', 118: 'D', 119: 'C', 120: 'B',
    
    # 挑战图推700题（七）121-140
    121: 'D', 122: 'B', 123: 'D', 124: 'B', 125: 'D',
    126: 'C', 127: 'C', 128: 'C', 129: 'D', 130: 'A',
    131: 'B', 132: 'C', 133: 'C', 134: 'D', 135: 'C',
    136: 'B', 137: 'D', 138: 'A', 139: 'C', 140: 'D',
    
    # 挑战图推700题（八）141-160
    141: 'D', 142: 'B', 143: 'C', 144: 'C', 145: 'A',
    146: 'C', 147: 'B', 148: 'A', 149: 'D', 150: 'C',
    151: 'C', 152: 'C', 153: 'C', 154: 'D', 155: 'C',
    156: 'B', 157: 'D', 158: 'C', 159: 'A', 160: 'A',
    
    # 挑战图推700题（九）161-180
    161: 'B', 162: 'A', 163: 'A', 164: 'B', 165: 'C',
    166: 'A', 167: 'C', 168: 'D', 169: 'D', 170: 'D',
    171: 'A', 172: 'B', 173: 'A', 174: 'D', 175: 'C',
    176: 'C', 177: 'C', 178: 'D', 179: 'D', 180: 'C',
    
    # 挑战图推700题（十）181-200
    181: 'C', 182: 'C', 183: 'C', 184: 'C', 185: 'C',
    186: 'C', 187: 'B', 188: 'B', 189: 'B', 190: 'B',
    191: 'D', 192: 'D', 193: 'D', 194: 'D', 195: 'C',
    196: 'A', 197: 'A', 198: 'C', 199: 'C', 200: 'B',
    
    # 以下答案需要从PDF继续提取...
    # 暂时用占位符
}

# 题目来源信息（从图片中识别）
QUESTION_SOURCES = {
    1: '25重庆事业', 2: '24四川事业', 3: '25国考',
    4: '20国考', 5: '20联考', 6: '19江苏',
    7: '25天津', 8: '23福建事业', 9: '21安徽事业',
    10: '25国家', 11: '23江苏事业', 12: '19广东',
    13: '22联考',
    # 更多来源信息...
}


def convert_pdf_to_images(pdf_path, output_dir, start_page=7, end_page=258):
    """将PDF题目页转换为图片"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"正在转换PDF页面 {start_page} - {end_page}...")
    
    # 分批转换避免内存问题
    batch_size = 20
    all_paths = []
    
    for batch_start in range(start_page, end_page + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_page)
        
        images = convert_from_path(
            pdf_path, 
            dpi=150, 
            first_page=batch_start, 
            last_page=batch_end
        )
        
        for i, img in enumerate(images, batch_start):
            path = os.path.join(output_dir, f"page_{i:03d}.png")
            img.save(path, 'PNG')
            all_paths.append(path)
        
        print(f"  已转换: 第{batch_start}-{batch_end}页")
    
    return all_paths


def create_question_records():
    """创建题目记录"""
    questions = []
    
    for num in range(1, 701):
        # 计算章节
        chapter = (num - 1) // 20 + 1
        chapter_name = f"挑战图推700题（{'一二三四五六七八九十'[chapter-1] if chapter <= 10 else str(chapter)}）"
        
        # 计算页码（每页约3题，从第7页开始）
        page_num = 7 + (num - 1) // 3
        
        question = {
            'number': num,
            'chapter': chapter,
            'chapter_name': chapter_name,
            'source': QUESTION_SOURCES.get(num, ''),
            'stem': '（图形推理题，需查看图片）',
            'options': {'A': '', 'B': '', 'C': '', 'D': ''},
            'answer': ANSWERS.get(num, ''),
            'category': '判断推理',
            'subcategory': '图形推理',
            'difficulty': '中等',
            'image_page': page_num,
            'image_path': f"images/page_{page_num:03d}.png"
        }
        
        questions.append(question)
    
    return questions


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. 转换PDF为图片
    images_dir = os.path.join(OUTPUT_DIR, 'images')
    
    if not os.path.exists(images_dir) or len(os.listdir(images_dir)) < 100:
        print("=== 步骤1: 转换PDF为图片 ===")
        convert_pdf_to_images(PDF_PATH, images_dir, start_page=7, end_page=258)
    else:
        print("图片已存在，跳过转换")
    
    # 2. 创建题目记录
    print("\n=== 步骤2: 创建题目记录 ===")
    questions = create_question_records()
    
    # 3. 保存结果
    result = {
        'source_file': PDF_PATH,
        'parse_time': datetime.now().isoformat(),
        'total_questions': len(questions),
        'category': '判断推理-图形推理',
        'source': '超格教育',
        'questions': questions
    }
    
    result_path = os.path.join(OUTPUT_DIR, 'questions.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 处理完成 ===")
    print(f"题目数量: {len(questions)}")
    print(f"有答案: {sum(1 for q in questions if q['answer'])}")
    print(f"结果保存: {result_path}")
    
    # 4. 生成导入脚本
    import_script = f'''#!/usr/bin/env python3
# 导入图形推理700题到题库
import json
import sys
sys.path.insert(0, '/Users/chaim/CodeBuddy/公考项目/cuoti-system')

from app import create_app, db
from app.models import Question

app = create_app()

with open('{result_path}', 'r') as f:
    data = json.load(f)

with app.app_context():
    count = 0
    for q in data['questions']:
        if q['answer']:  # 只导入有答案的
            question = Question(
                uid=f"TX700-{{q['number']:03d}}",
                stem=f"[图形推理第{{q['number']}}题] {{q['source']}}",
                option_a="见图",
                option_b="见图", 
                option_c="见图",
                option_d="见图",
                answer=q['answer'],
                analysis="",
                category="判断推理",
                subcategory="图形推理",
                source="超格教育-图形推理700题",
                difficulty="中等"
            )
            db.session.add(question)
            count += 1
    
    db.session.commit()
    print(f"成功导入 {{count}} 道题目")
'''
    
    import_path = os.path.join(OUTPUT_DIR, 'import_to_db.py')
    with open(import_path, 'w', encoding='utf-8') as f:
        f.write(import_script)
    
    print(f"导入脚本: {import_path}")


if __name__ == '__main__':
    main()
