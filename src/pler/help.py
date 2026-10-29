"""Versioned offline help from fixed bundled chapters, never a caller-selected file."""
from html import escape
from pathlib import Path

from . import __version__

_FOLDER = Path(__file__).with_name('help')
_CHAPTERS = {
    ('en', 'guide'): 'en.html', ('tr', 'guide'): 'tr.html',
    ('en', 'accounting'): 'en-accounting.html', ('tr', 'accounting'): 'tr-accounting.html',
}


def render(lang='en', chapter='guide'):
    """Return local documentation HTML with the current installed version.

    Language fallback matches the application. Chapters are a fixed allowlist;
    no path, URL, project name, source log or cache value can enter this page.
    """
    lang = lang if isinstance(lang, str) and lang in ('en', 'tr') else 'en'
    if not isinstance(chapter, str) or chapter not in ('guide', 'accounting'):
        raise ValueError('unknown help chapter')
    page = (_FOLDER / _CHAPTERS[(lang, chapter)]).read_text(encoding='utf-8')
    page = page.replace('__PLER_VERSION__', escape(__version__, quote=True))
    if chapter == 'accounting':
        contract = (_FOLDER / 'accounting.txt').read_text(encoding='utf-8')
        page = page.replace('__ACCOUNTING__', escape(contract))
    return page
