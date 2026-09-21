# -*- coding: utf-8 -*-
import re
from typing import List, Dict, Any, Optional

def _split_by_numbered_items(text: str) -> List[str]:
    """按数字编号分割，不严格依赖换行。"""
    text = text.strip()
    # 用捕获组 split，保留匹配到的标题
    pattern = re.compile(r'(?=\d+[\.、\)）]?\s*《[^》]+》)')
    parts = pattern.split(text)
    # 过滤掉前言和空块
    blocks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(r'^\d+[\.、\)）]?\s*《', part):
            blocks.append(part)
    return blocks

def _extract_article_from_text(text: str, title: str) -> str:
    m = re.search(r'第[一二三四五六七八九十百零\d]+条', text)
    return m.group(0) if m else ""

def _parse_single_law_block(block: str) -> Optional[Dict[str, Any]]:
    name_match = re.search(r'《([^》]+)》', block)
    law_name = f"《{name_match.group(1)}》" if name_match else "相关法律"

    doc_match = re.search(r'文号[：:]\s*([^\n]+)', block)
    doc_number = doc_match.group(1).strip().rstrip('，。,') if doc_match else ""

    status_match = re.search(r'(已被修改|有效|失效|废止)', block)
    status = status_match.group(1) if status_match else ""

    article = _extract_article_from_text(block, law_name)

    content = block
    # 1. 去掉开头的编号
    content = re.sub(r'^\d+[\.、\)）]?\s*', '', content)
    # 2. 去掉法律名称行（行首或紧跟换行）
    content = re.sub(r'^《[^》]+》\s*', '', content)
    # 3. 去掉文号行
    content = re.sub(r'(?:^|\n)\s*文号[：:]\s*[^\n]*', '\n', content)
    # 4. 去掉效力状态行
    content = re.sub(r'(?:^|\n)\s*(?:已被修改|有效|失效|废止)\s*(?:\n|$)', '\n', content)
    # 5. 去掉核心法条摘要 / CONTENTS SUMMARY（整行）
    content = re.sub(r'(?:^|\n)\s*核心法条摘要\s*CONTENTS\s*SUMMARY\s*(?:\n|$)', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'(?:^|\n)\s*CONTENTS\s*SUMMARY\s*(?:\n|$)', '\n', content, flags=re.IGNORECASE)
    # 6. 去掉总则行
    content = re.sub(r'(?:^|\n)\s*总则\s*(?:\n|$)', '\n', content)
    # 7. 去掉截断提示
    content = re.sub(r'[…\.]+\s*\(正文较长，此处仅展示核心概要\)', '', content)
    content = re.sub(r'\(正文较长，此处仅展示核心概要\)', '', content)
    # 8. 清理空白
    content = re.sub(r'\n{2,}', '\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = content.strip()
    content = content.strip('\n，。 ')

    if not content or len(content) < 5:
        return None

    return {
        "law_name": law_name,
        "article_number": article or "相关条款",
        "content": content,
        "doc_number": doc_number,
        "status": status,
        "relevance": 0.85,
    }

# 模拟带 HTML 的输入（<div> 包裹，无换行）
test_html = """<div>1. 《中华人民共和国劳动合同法》</div><div>文号：中华人民共和国主席令第65号</div><div>已被修改</div><div></div><div>核心法条摘要 CONTENTS SUMMARY</div><div>总则</div><div>【立法宗旨】为了完善劳动合同制度，明确劳动合同双方当事人的权利和义务，保护劳动者的合法权益，构建和发展和谐稳定的劳动关系，制定本法。</div><div>【适用范围】中华人民共和国境内的企业、个体经济组织、民办非企业单位等组织（div><div>国家机关、事业单位、社会团……(正文较长，此处仅展示核心概要)</div><div></div><div>2. 《最高人民法院关于审理劳动争议案件适用法律问题的解释(二)》</div><div>文号：法释〔2025〕12号</div><div>有效</div><div></div><div>核心法条摘要 CONTENTS SUMMARY</div><div>由【最高人民法院】于2025-07-31发布（文号：法释〔2025〕12号），其法律效力层级为【司法解释】，目前效力状态为【有效】。</div>"""

# 模拟 strip_html 处理（只处理 <br> 和 <p>，<div> 直接删除不保留换行）
def strip_html(text):
    text = re.sub(r"<br\s*/?>|</?p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text

clean_text = strip_html(test_html)
print("=== strip_html 后的文本 ===")
print(repr(clean_text[:200]))
print()

print("=== 分割测试 ===")
blocks = _split_by_numbered_items(clean_text)
print(f"分割出 {len(blocks)} 个 block\n")

for i, b in enumerate(blocks):
    print(f"--- Block {i+1} ---")
    result = _parse_single_law_block(b)
    if result:
        print(f"  law_name={result['law_name']}, status={result['status']}")
        print(f"  content={result['content'][:120]}...")
    else:
        print("  返回 None!")
    print()
