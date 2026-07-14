#!/usr/bin/env python3
"""
extract_ecg_questions.py
从 ECG-QA 数据集中提取唯一的问题模板，生成 CSV 文件。
"""

import os
import json
import csv
import ast
from pathlib import Path
from typing import Dict, List, Set

def extract_questions_from_json(json_dir: Path) -> Dict[int, Dict]:
    """
    遍历 JSON 目录，提取唯一的问题模板
    
    Args:
        json_dir: JSON 文件目录路径
    
    Returns:
        字典，key 为 template_id，value 包含问题信息
    """
    questions = {}  # template_id -> {question, question_type, answers}
    
    # 获取所有 JSON 文件
    json_files = list(json_dir.glob("*.json"))
    print(f"📂 找到 {len(json_files)} 个 JSON 文件")
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for sample in data:
            template_id = sample.get('template_id')
            question = sample.get('question')
            question_type = sample.get('question_type')
            attribute_type = sample.get('attribute_type')
            answer = sample.get('answer', [])
            
            # 如果该 template_id 还未记录，则保存
            if template_id not in questions:
                questions[template_id] = {
                    'question': question,
                    'question_type': question_type,
                    'attribute_type': attribute_type,
                    'answers': answer
                }
    
    print(f"✅ 提取到 {len(questions)} 个唯一问题模板")
    return questions

def load_answer_templates(csv_path: Path) -> Dict[int, List[str]]:
    """
    加载 answers_for_each_template.csv，获取每个模板的完整答案集
    
    Args:
        csv_path: answers_for_each_template.csv 路径
    
    Returns:
        字典，template_id -> 答案列表
    """
    answer_templates = {}
    
    if not csv_path.exists():
        print(f"⚠️ 文件不存在: {csv_path}")
        return answer_templates
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过 header
        for row in reader:
            if len(row) >= 2:
                template_id = int(row[0])
                try:
                    # 解析 Python 列表字符串
                    classes = ast.literal_eval(row[1])
                    if isinstance(classes, list):
                        answer_templates[template_id] = classes
                except:
                    # 如果解析失败，尝试其他方式
                    classes_str = row[1].strip('[]').replace("'", "").split(',')
                    classes = [c.strip() for c in classes_str if c.strip()]
                    answer_templates[template_id] = classes
    
    print(f"✅ 加载了 {len(answer_templates)} 个模板的答案集")
    return answer_templates

def generate_csv(
    questions: Dict[int, Dict],
    answer_templates: Dict[int, List[str]],
    output_path: Path
):
    """
    生成 CSV 文件
    
    CSV 列：
    1. template_id (int)
    2. question (string)
    3. question_type (string)
    4. attribute_type (string)
    5. answer_candidates (list of strings)
    """
    # 合并答案：优先使用 answers_for_each_template.csv 中的答案
    final_answers = {}
    for template_id, info in questions.items():
        if template_id in answer_templates and answer_templates[template_id]:
            final_answers[template_id] = answer_templates[template_id]
        else:
            final_answers[template_id] = info.get('answers', [])
    
    # 写入 CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['template_id', 'question', 'question_type', 'attribute_type', 'answer_candidates'])
        
        for template_id in sorted(questions.keys()):
            info = questions[template_id]
            row = [
                template_id,
                info.get('question', ''),
                info.get('question_type', ''),
                info.get('attribute_type', ''),
                str(final_answers.get(template_id, []))
            ]
            writer.writerow(row)
    
    print(f"✅ CSV 已保存到: {output_path}")

def main():
    """主函数"""
    # --- 配置路径 ---
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    # JSON 文件目录
    json_dir = project_root / "ecg-qa/ecgqa/ptbxl/template/valid"
    
    # answers_for_each_template.csv 路径
    answers_csv_path = project_root / "ecg-qa/ecgqa/ptbxl/answers_for_each_template.csv"
    
    # 输出 CSV 路径
    output_path = project_root / "ecg-qa/ecgqa_questions_extracted.csv"
    
    print("="*60)
    print("📋 ECG-QA 问题提取工具")
    print("="*60)
    print(f"   JSON 目录: {json_dir}")
    print(f"   答案模板: {answers_csv_path}")
    print(f"   输出文件: {output_path}")
    print("="*60)
    
    # 检查目录是否存在
    if not json_dir.exists():
        print(f"❌ JSON 目录不存在: {json_dir}")
        print("   请确认 ECG-QA 数据集已下载到正确位置")
        return
    
    # 1. 提取问题
    questions = extract_questions_from_json(json_dir)
    
    if not questions:
        print("❌ 未提取到任何问题")
        return
    
    # 2. 加载答案模板
    answer_templates = load_answer_templates(answers_csv_path)
    
    # 3. 生成 CSV
    generate_csv(questions, answer_templates, output_path)
    
    # 4. 打印统计信息
    print("\n" + "="*60)
    print("📊 统计信息")
    print("="*60)
    print(f"   问题模板总数: {len(questions)}")
    
    # 按类型统计
    type_counts = {}
    for info in questions.values():
        q_type = info.get('question_type', 'unknown')
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    print("\n   按问题类型分类:")
    for q_type, count in sorted(type_counts.items()):
        print(f"      {q_type}: {count}")

    # 按属性统计
    attribute_counts = {}
    for info in questions.values():
        a_type = info.get('attribute_type', 'unknown')
        attribute_counts[a_type] = attribute_counts.get(a_type, 0) + 1

    print("\n   按属性类型分类:")
    for a_type, count in sorted(attribute_counts.items()):
        print(f"      {a_type}: {count}")

    
    print("\n" + "="*60)
    print("✅ 完成！")

if __name__ == "__main__":
    main()