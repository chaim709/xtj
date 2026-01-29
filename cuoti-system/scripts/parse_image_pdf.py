#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片型PDF解析器 - 使用AI视觉识别
支持图形推理、资料分析等含图题目
"""
import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime

# PDF转图片
try:
    from pdf2image import convert_from_path
except ImportError:
    print("请安装 pdf2image: pip install pdf2image")
    print("还需要安装 poppler: brew install poppler")
    sys.exit(1)

# AI API
try:
    from openai import OpenAI
except ImportError:
    print("请安装 openai: pip install openai")
    sys.exit(1)


def pdf_to_images(pdf_path, output_dir, dpi=150):
    """将PDF转换为图片"""
    print(f"正在转换PDF: {pdf_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    images = convert_from_path(pdf_path, dpi=dpi)
    
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
        image.save(image_path, "PNG")
        image_paths.append(image_path)
        print(f"  已保存: page_{i+1:03d}.png")
    
    print(f"共转换 {len(images)} 页")
    return image_paths


def encode_image(image_path):
    """将图片编码为base64"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def analyze_page_with_ai(image_path, client, model="gpt-4o"):
    """使用AI分析单页图片"""
    
    base64_image = encode_image(image_path)
    
    prompt = """请分析这张公务员考试图形推理题目的图片，提取所有题目信息。

对于每道题目，请提取：
1. 题号
2. 题干描述（用文字描述图形的特征、排列方式等）
3. 选项描述（A、B、C、D各选项的图形特征）
4. 如果能看到答案，也请提取

请以JSON格式输出，格式如下：
```json
{
  "page_type": "题目页/答案页/其他",
  "questions": [
    {
      "number": 1,
      "stem": "题干的文字描述，包括图形排列方式（如九宫格、类比、顺序等）和图形特征",
      "options": {
        "A": "选项A的图形描述",
        "B": "选项B的图形描述",
        "C": "选项C的图形描述",
        "D": "选项D的图形描述"
      },
      "answer": "如果可见则填写，否则留空",
      "pattern": "识别到的规律类型（如：旋转、对称、叠加、数量递增等）"
    }
  ]
}
```

注意：
- 尽可能详细描述图形特征
- 如果是答案页，提取题号和答案
- 如果页面为空或无法识别，返回空questions数组"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # 提取JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content.strip())
        
    except Exception as e:
        print(f"  分析失败: {e}")
        return {"page_type": "error", "error": str(e), "questions": []}


def process_pdf(pdf_path, api_key, output_dir=None, start_page=1, end_page=None, model="gpt-4o"):
    """处理整个PDF"""
    
    pdf_name = Path(pdf_path).stem
    
    if output_dir is None:
        output_dir = f"output/{pdf_name}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 转换PDF为图片
    images_dir = os.path.join(output_dir, "images")
    image_paths = pdf_to_images(pdf_path, images_dir)
    
    # 确定处理范围
    if end_page is None:
        end_page = len(image_paths)
    
    # 初始化AI客户端
    client = OpenAI(api_key=api_key)
    
    # 分析每页
    all_questions = []
    all_answers = {}
    
    print(f"\n开始AI分析 (第{start_page}页 到 第{end_page}页)...")
    
    for i, image_path in enumerate(image_paths[start_page-1:end_page], start=start_page):
        print(f"\n分析第 {i}/{end_page} 页...")
        
        result = analyze_page_with_ai(image_path, client, model)
        
        # 保存单页结果
        page_result_path = os.path.join(output_dir, f"page_{i:03d}.json")
        with open(page_result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 收集结果
        if result.get("page_type") == "题目页":
            for q in result.get("questions", []):
                q["source_page"] = i
                all_questions.append(q)
                print(f"  识别到题目 #{q.get('number', '?')}")
        
        elif result.get("page_type") == "答案页":
            for q in result.get("questions", []):
                if q.get("number") and q.get("answer"):
                    all_answers[q["number"]] = q["answer"]
            print(f"  识别到 {len(result.get('questions', []))} 个答案")
        
        else:
            print(f"  页面类型: {result.get('page_type', '未知')}")
    
    # 合并答案到题目
    for q in all_questions:
        num = q.get("number")
        if num and num in all_answers:
            q["answer"] = all_answers[num]
    
    # 保存最终结果
    final_result = {
        "source_file": pdf_path,
        "parse_time": datetime.now().isoformat(),
        "total_questions": len(all_questions),
        "questions": all_questions
    }
    
    result_path = os.path.join(output_dir, "result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n===== 处理完成 =====")
    print(f"识别题目: {len(all_questions)} 道")
    print(f"结果保存: {result_path}")
    
    return final_result


def main():
    parser = argparse.ArgumentParser(description="图片型PDF解析器")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--api-key", help="OpenAI API Key (或设置OPENAI_API_KEY环境变量)")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--start", type=int, default=1, help="起始页码")
    parser.add_argument("--end", type=int, help="结束页码")
    parser.add_argument("--model", default="gpt-4o", help="AI模型 (默认gpt-4o)")
    
    args = parser.parse_args()
    
    # 获取API Key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请提供API Key (--api-key 或 OPENAI_API_KEY环境变量)")
        sys.exit(1)
    
    # 处理PDF
    process_pdf(
        args.pdf_path,
        api_key,
        output_dir=args.output,
        start_page=args.start,
        end_page=args.end,
        model=args.model
    )


if __name__ == "__main__":
    main()
