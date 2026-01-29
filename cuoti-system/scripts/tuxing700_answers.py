#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形推理700题 完整答案
从PDF第261-263页提取
"""

# 答案格式：每章20题，共35章 = 700题
# 格式：1-5: XXXXX, 6-10: XXXXX, 11-15: XXXXX, 16-20: XXXXX

CHAPTER_ANSWERS = {
    # 第261页
    1:  ('CCDAA', 'ADABD', 'BDAAB', 'ACCBD'),  # 挑战图推700题（一）
    2:  ('BDADB', 'CDACD', 'BBBCC', 'CAABA'),  # 挑战图推700题（二）
    3:  ('BCCDB', 'CCDCB', 'BBCAA', 'DDBBB'),  # 挑战图推700题（三）
    4:  ('DBBBD', 'DDBAB', 'DBCCC', 'CDACC'),  # 挑战图推700题（四）
    5:  ('DAACD', 'ABCBB', 'ADDBA', 'ABBBC'),  # 挑战图推700题（五）
    6:  ('ABAAB', 'DDBDB', 'CCDAD', 'DADCB'),  # 挑战图推700题（六）
    7:  ('DBDBD', 'CCCDA', 'BCCDC', 'BDACD'),  # 挑战图推700题（七）
    8:  ('DBCCA', 'CBADC', 'CCCDC', 'BDCAA'),  # 挑战图推700题（八）
    9:  ('BAABC', 'ACDDD', 'ABADC', 'CCDDC'),  # 挑战图推700题（九）
    10: ('CCCCC', 'CBBBB', 'DDDDC', 'AACCB'),  # 挑战图推700题（十）
    11: ('CAAAC', 'DADBB', 'CABAC', 'CAADC'),  # 挑战图推700题（十一）
    
    # 第262页
    12: ('DBADC', 'BCDCA', 'DDABA', 'AAADD'),  # 挑战图推700题（十二）
    13: ('BADAD', 'CDDBB', 'CDCBC', 'CDDCA'),  # 挑战图推700题（十三）
    14: ('DDCCB', 'DCBAB', 'CAABA', 'DADBD'),  # 挑战图推700题（十四）
    15: ('ADBAD', 'DDDBA', 'ABCAB', 'BADDB'),  # 挑战图推700题（十五）
    16: ('BAAAA', 'DCCCC', 'DDCDB', 'CDAAD'),  # 挑战图推700题（十六）
    17: ('ADAAA', 'DCABC', 'ACBDB', 'CBBCA'),  # 挑战图推700题（十七）
    18: ('CCDBB', 'CADCA', 'BDBDD', 'AABBA'),  # 挑战图推700题（十八）
    19: ('DBDCD', 'DCDDD', 'DDBCA', 'DAACB'),  # 挑战图推700题（十九）
    20: ('CDADD', 'CCACC', 'CBDBB', 'CDDBC'),  # 挑战图推700题（二十）
    21: ('CAACB', 'ADCDA', 'CDAAC', 'ABAAC'),  # 挑战图推700题（二十一）
    22: ('BBAAC', 'DDCDD', 'DACCA', 'BCABA'),  # 挑战图推700题（二十二）
    23: ('DCAAC', 'CBCBC', 'BADBC', 'BBDAA'),  # 挑战图推700题（二十三）
    
    # 第263页
    24: ('DADBB', 'BCDCB', 'CDDDB', 'BAACA'),  # 挑战图推700题（二十四）
    25: ('CAADA', 'DCBBC', 'ADDAD', 'ADADB'),  # 挑战图推700题（二十五）
    26: ('CBAAD', 'AABDD', 'CBCDC', 'DCBBC'),  # 挑战图推700题（二十六）
    27: ('DDCBB', 'CCBCC', 'CDCAA', 'DACAB'),  # 挑战图推700题（二十七）
    28: ('CBBCB', 'ACCCA', 'DDDBA', 'BADCA'),  # 挑战图推700题（二十八）
    29: ('DCDBB', 'AAABB', 'ADDDA', 'CADCD'),  # 挑战图推700题（二十九）
    30: ('CBDDC', 'CDADC', 'CCAAC', 'DACAC'),  # 挑战图推700题（三十）
    31: ('AACBD', 'DADDC', 'CDABA', 'CCBAB'),  # 挑战图推700题（三十一）
    32: ('ABCCC', 'DBBBB', 'BADBB', 'BADCB'),  # 挑战图推700题（三十二）
    33: ('ACCDA', 'CDDDC', 'CCDCD', 'BBCDA'),  # 挑战图推700题（三十三）
    34: ('ADCDD', 'DDABA', 'AABBC', 'BCBDD'),  # 挑战图推700题（三十四）
    35: ('DCBCD', 'CAADD', 'ACDBB', 'DBBAA'),  # 挑战图推700题（三十五）
}


def get_all_answers():
    """生成完整的1-700题答案字典"""
    answers = {}
    
    for chapter, (g1, g2, g3, g4) in CHAPTER_ANSWERS.items():
        base = (chapter - 1) * 20
        
        # 1-5
        for i, ans in enumerate(g1):
            answers[base + i + 1] = ans
        
        # 6-10
        for i, ans in enumerate(g2):
            answers[base + 5 + i + 1] = ans
        
        # 11-15
        for i, ans in enumerate(g3):
            answers[base + 10 + i + 1] = ans
        
        # 16-20
        for i, ans in enumerate(g4):
            answers[base + 15 + i + 1] = ans
    
    return answers


if __name__ == '__main__':
    answers = get_all_answers()
    print(f"共生成 {len(answers)} 道题答案")
    
    # 验证
    for i in range(1, 21):
        print(f"{i}: {answers.get(i, '?')}", end='  ')
        if i % 5 == 0:
            print()
