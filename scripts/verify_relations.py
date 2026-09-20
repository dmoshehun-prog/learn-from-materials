"""校验页面实际可见的框架关系图，以及有据的无规则/无关系例外。

用法：python3 scripts/verify_relations.py page.json --knowledge-base topic.learnkb
新系统学习页会从知识库绑定规范方法数据并校验逐单元行动规则账本。
旧页面可用 --legacy 与 --allow-empty 人工复核。退出码：0 通过；1 校验失败；2 读取失败。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RELATION_TYPES = {
    'prerequisite', 'sequence', 'causes', 'supports',
    'contrasts', 'part_of', 'applies', 'feedback', 'parallel',
}
MIN_EXPLANATION = {'zh-CN': 12, 'en': 40}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.info.append(msg)

    def as_dict(self) -> dict:
        return {'ok': not self.errors, 'errors': self.errors,
                'warnings': self.warnings, 'info': self.info}


def _node_ids(page: dict) -> list[str]:
    ids: list[str] = []
    for key in ('frameworks', 'decisionRules'):
        for item in page.get(key) or []:
            if isinstance(item, dict) and isinstance(item.get('id'), str):
                ids.append(item['id'])
    return ids


def check_page(page: dict, allow_empty: bool = False, strict_quick: bool = False,
               ledger: dict | None = None) -> Report:
    """对单个 overview page.json 执行关系图断言。"""
    rep = Report()
    if page.get('meta', {}).get('mode') != 'overview':
        rep.note('非 overview 页面，跳过关系图门禁')
        return rep

    lang = page.get('meta', {}).get('language', 'zh-CN')
    quick = page.get('meta', {}).get('learningDepth') == 'quick'
    # 快速了解模式边界更小：默认降级为 warning，除非显式 --strict-quick。
    soft = quick and not strict_quick
    soft_or_allowed = soft or (allow_empty and ledger is None)

    nodes = _node_ids(page)
    edges = page.get('relationships')
    if not isinstance(edges, list):
        rep.error('relationships 必须是数组')
        return rep

    framework_ids = {n['id'] for n in page.get('frameworks') or [] if isinstance(n, dict) and isinstance(n.get('id'), str)}
    visible = [e for e in edges if isinstance(e, dict) and e.get('from') in framework_ids and e.get('to') in framework_ids]
    independent = {x['frameworkId'] for x in (ledger or {}).get('independentFrameworks', [])}
    unsupported = (ledger or {}).get('relationStatus') == 'unsupported'
    rep.note(f'节点 {len(nodes)} 个（框架 {len(page.get("frameworks") or [])} / '
             f'规则 {len(page.get("decisionRules") or [])}），关系边 {len(edges)} 条，框架图可见 {len(visible)} 条')

    # R1 存在性：多个节点却零关系 —— 这是静默失败的原点。
    if len(framework_ids) >= 2 and not visible:
        msg = f'框架关系图为空：{len(framework_ids)} 个框架，0 条框架间关系边。框架到规则的边不会显示在该图中。'
        (rep.warn if soft_or_allowed or unsupported else rep.error)(msg)
    if unsupported and visible:
        rep.error('账本声明框架间关系不受材料支持，但页面提供了框架间连线')

    # R2 孤立节点：每张卡片都应至少参与一条关系。
    if visible:
        degree = {n: 0 for n in framework_ids}
        for edge in visible:
            for key in ('from', 'to'):
                if edge.get(key) in degree:
                    degree[edge[key]] += 1
        orphans = [n for n in framework_ids if degree[n] == 0 and n not in independent]
        if orphans:
            msg = (f'{len(orphans)} 个框架节点在可见图中没有连线：' + '、'.join(sorted(orphans)[:12])
                   + ('…' if len(orphans) > 12 else '')
                   + '。请补有据关系，或在规则账本中说明其独立性。')
            (rep.warn if soft_or_allowed else rep.error)(msg)

    # R3 端点与重复（端点存在性由 page_extensions 覆盖，这里补重边与自环冗余提示）
    seen_pairs: dict[tuple[str, str, str], int] = {}
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            rep.error(f'relationships[{index}] 必须是对象')
            continue
        pair = (str(edge.get('from')), str(edge.get('to')), str(edge.get('type')))
        if pair[0] == pair[1]:
            rep.error(f'relationships[{index}] 是自环')
        if pair in seen_pairs:
            rep.warn(f'relationships[{index}] 与 relationships[{seen_pairs[pair]}] '
                     f'重复同一条 {pair[0]} → {pair[1]}（{pair[2]}）')
        else:
            seen_pairs[pair] = index
        if edge.get('type') not in RELATION_TYPES:
            rep.error(f'relationships[{index}].type 不在允许的关系类型之内')

    # R4 取证强度：全部为推断的关系图不可声称来自材料。
    if edges:
        material = sum(1 for e in edges if isinstance(e, dict) and e.get('evidence') == 'material')
        inference = sum(1 for e in edges if isinstance(e, dict) and e.get('evidence') == 'inference')
        rep.note(f'取证分布：material {material} 条 / inference {inference} 条')
        if material == 0:
            rep.warn('全部关系边都是 inference，没有任何一条由原文直接陈述支撑')
        elif inference and inference / max(material + inference, 1) > 0.5:
            rep.warn(f'inference 占比 {inference}/{material + inference} 超过一半，'
                     '需确认这些边确实是综合解读而非原文已有')

    # R6 解释质量：写"相关"了事的边等于没有解释。
    floor = MIN_EXPLANATION.get(lang, 12)
    weak = [str(e.get('id') or i) for i, e in enumerate(edges)
            if isinstance(e, dict) and len(str(e.get('explanation') or '').strip()) < floor]
    if weak:
        rep.warn(f'{len(weak)} 条边的 explanation 过短（<{floor} 字符）：' + '、'.join(weak[:12]))

    # 数量比例仅提示，实际完整性由逐单元规则账本与原文复查判断。
    frameworks = page.get('frameworks') or []
    rules = page.get('decisionRules') or []
    if not quick and frameworks and not rules:
        if ledger and all(c['status'] == 'excluded' for c in ledger['candidates']) and all(u['status'] in ('reviewed', 'no-rules') for u in ledger['units']):
            rep.note('各单元已复核并说明没有可提炼的行动规则')
        else:
            rep.error('行动规则为 0 条；需逐单元复核并在规则账本说明没有规则的原因')
    elif not quick and rules and len(frameworks) >= 8 and len(rules) <= max(3, len(frameworks) // 10):
        rep.warn(f'行动规则只有 {len(rules)} 条，而框架有 {len(frameworks)} 个——'
                 f'这个比例偏低。契约要求"收录全部条件—行动—原因关系"，不是"凑够几条"；'
                 f'请回扫各单元的 takeaways 与实验步骤章节，确认没有把「当…就…」型论述漏在行动规则之外。')

    return rep


def check_methodology(model: dict) -> Report:
    """方法论图同属一类风险，做同样的断言（methodology.py 已有可达性检查，这里复核）。"""
    rep = Report()
    nodes = model.get('nodes') or []
    edges = model.get('edges') or []
    ids = {n['id'] for n in nodes if isinstance(n, dict) and isinstance(n.get('id'), str)}
    rep.note(f'方法论：{len(ids)} 节点 / {len(edges)} 边')
    if model.get('status') == 'ready':
        if len(ids) >= 2 and not edges:
            rep.error(f'方法论图为空：{len(ids)} 个节点，0 条边')
        if edges and ids:
            degree = {i: 0 for i in ids}
            for e in edges:
                if isinstance(e, dict):
                    if e.get('from') in degree:
                        degree[e['from']] += 1
                    if e.get('to') in degree:
                        degree[e['to']] += 1
            orphans = [i for i in ids if degree[i] == 0]
            if orphans:
                rep.error('方法论孤立节点：' + '、'.join(sorted(orphans)))
        if (model.get('structure') == 'process' and len(ids) >= 4
                and len(edges) == len(ids) - 1
                and all(isinstance(e, dict) and e.get('kind') == 'main' for e in edges)):
            rep.warn('方法论图仅有一条顺序主线；请回看原文是否存在并行、条件分支、对比或反馈。若材料确为线性流程，保留原状。')
    return rep


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('page', type=Path)
    p.add_argument('--knowledge-base', type=Path, default=None,
                   help='同时校验 <kb>/methodology.json 的关系图')
    p.add_argument('--allow-empty', action='store_true',
                   help='把“空关系图/孤立节点”降级为 warning（必须显式声明，不得默认）')
    p.add_argument('--strict-quick', action='store_true',
                   help='快速了解模式下也按 error 判定')
    p.add_argument('--legacy', action='store_true', help='仅检查旧页面，不要求新规则账本')
    p.add_argument('--json', action='store_true', help='输出机器可读结果')
    a = p.parse_args()

    try:
        page = json.loads(a.page.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(f'无法读取 page.json：{exc}', file=sys.stderr)
        return 2

    ledger = None
    if a.knowledge_base and page.get('meta', {}).get('learningDepth') == 'systematic' and not a.legacy:
        from action_rules import load_and_validate
        from methods import bind, read, validate_library
        try:
            library = validate_library(read(a.knowledge_base / 'methods.json'), a.knowledge_base)
            page = bind(page, library)
            page['methodology'] = read(a.knowledge_base / 'methodology.json')
            ledger = load_and_validate(page, a.knowledge_base)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f'规则账本校验失败：{exc}', file=sys.stderr)
            return 1
    rep = check_page(page, allow_empty=a.allow_empty, strict_quick=a.strict_quick, ledger=ledger)
    if a.knowledge_base:
        model_path = a.knowledge_base / 'methodology.json'
        if model_path.exists():
            try:
                rep2 = check_methodology(json.loads(model_path.read_text(encoding='utf-8')))
                rep.errors += rep2.errors
                rep.warnings += rep2.warnings
                rep.info += rep2.info
            except json.JSONDecodeError as exc:
                rep.error(f'methodology.json 无法解析：{exc}')
        else:
            rep.warn(f'未找到 {model_path}，跳过方法论关系图校验')

    if a.json:
        print(json.dumps(rep.as_dict(), ensure_ascii=False, indent=2))
    else:
        for line in rep.info:
            print(f'· {line}')
        for line in rep.warnings:
            print(f'WARN  {line}')
        for line in rep.errors:
            print(f'ERROR {line}')
        print(('关系图门禁通过' if not rep.errors else f'关系图门禁失败：{len(rep.errors)} 项'),
              f'（warning {len(rep.warnings)}）')
    return 1 if rep.errors else 0


if __name__ == '__main__':
    sys.exit(main())
