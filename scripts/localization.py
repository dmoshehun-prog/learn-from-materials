"""Localize template-owned strings only; never translate supplied material text."""
from contextvars import ContextVar
from functools import lru_cache, wraps
from pathlib import Path
import re

LOCALE = ContextVar('learning_page_locale', default='zh-CN')


@lru_cache(maxsize=1)
def catalog():
    rows = (Path(__file__).resolve().parents[1] / 'templates/locales/en.txt').read_text(encoding='utf-8').splitlines()
    pairs = dict(row.split(' => ', 1) for row in rows if row and not row.startswith('#'))
    return pairs, re.compile('|'.join(re.escape(key) + (r'(?![\u3400-\u9fff])' if key == ' 题' else '') for key in sorted(pairs, key=len, reverse=True)))


def translate_static(value, language='en'):
    if language != 'en':
        return value
    pairs, pattern = catalog()
    return pattern.sub(lambda match: pairs[match.group()], value)


def t(value):
    return translate_static(value, LOCALE.get())


def localized(function):
    @wraps(function)
    def wrapped(data, *args, **kwargs):
        token = LOCALE.set((data.get('meta') or {}).get('language', 'zh-CN'))
        try:
            return function(data, *args, **kwargs)
        finally:
            LOCALE.reset(token)
    return wrapped


CATEGORY_EN = dict(zip(
    ('英文缩写', '领域术语', '方法框架', '角色与流程', '指标与工具'),
    ('Abbreviations', 'Domain terms', 'Methods and frameworks', 'Roles and processes', 'Metrics and tools'),
))
ABILITY_EN = dict(zip(('记忆', '解释', '应用', '迁移'), ('Recall', 'Explain', 'Apply', 'Transfer')))


def localized_enum(value):
    if LOCALE.get() == 'en':
        return CATEGORY_EN.get(value, ABILITY_EN.get(value, value))
    return value
