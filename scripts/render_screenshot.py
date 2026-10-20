"""渲染“版本控制记录”截图：终端风格的仓库结构与提交记录。

运行：python3 scripts/render_screenshot.py
输出：docs/figures/version-control.png
内容取自真实仓库状态（目录树 + git log），不做手工排版。
"""
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs' / 'figures' / 'version-control.png'

SIZE = 26
LH = 38
CELL = 16          # Menlo 等宽字符宽度
PAD = 30
TITLE_H = 46
MAX_CELLS = 104
MENLO = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', SIZE)
SONGTI = ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc', SIZE)

BG = '#0d1117'
BAR = '#161b22'
FG = '#c9d1d9'
CMD = '#e6edf3'
PROMPT = '#7ee787'
DIM = '#8b949e'
HASH = '#ffa657'
REF = '#79c0ff'


def _wide(ch):
    return unicodedata.east_asian_width(ch) in 'WF'


def cells(text):
    return sum(2 if _wide(c) else 1 for c in text)


def draw_line(draw, x, y, text, color):
    for ch in text:
        if _wide(ch):
            w = CELL * 2
            gw = SONGTI.getlength(ch)
            draw.text((x + (w - gw) / 2, y), ch, font=SONGTI, fill=color)
            x += w
        else:
            draw.text((x, y), ch, font=MENLO, fill=color)
            x += CELL


def tree_lines(root, depth=2):
    """按真实目录生成 tree 风格输出（目录优先，跳过 .git 与系统文件）。"""
    skip = {'.git', '__pycache__', '.DS_Store', '.idea', '.venv', 'mysql-data'}
    out = []

    def walk(path, prefix, level):
        if level > depth:
            return
        entries = sorted([e for e in path.iterdir() if e.name not in skip],
                         key=lambda e: (not e.is_dir(), e.name.lower()))
        for i, e in enumerate(entries):
            last = i == len(entries) - 1
            branch = '└── ' if last else '├── '
            out.append(prefix + branch + e.name + ('/' if e.is_dir() else ''))
            if e.is_dir() and level < depth:
                walk(e, prefix + ('    ' if last else '│   '), level + 1)

    out.append(root.name + '/')
    walk(root, '', 1)
    return out


def git_log_lines():
    r = subprocess.run(['git', 'log', '--oneline', '--graph', '--decorate'],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.rstrip().splitlines()


def build_items():
    items = []
    items.append(('cmd', '$ cd ~/Documents/Codex/2026-10-13/ctf-training-platform'))
    items.append(('out', ''))
    items.append(('cmd', '$ tree -L 2 --dirsfirst'))
    for line in tree_lines(ROOT):
        items.append(('tree', line))
    items.append(('out', ''))
    items.append(('cmd', '$ git log --oneline --graph --decorate'))
    for line in git_log_lines():
        items.append(('log', line))
    return items


def style_for(kind, text):
    if kind == 'cmd':
        return text, CMD
    if kind == 'tree':
        if text.endswith('/'):
            return text, REF
        return text, FG
    if kind == 'log':
        return text, FG
    if kind == 'ok':
        return text, PROMPT
    return text, DIM


def wrap(text, limit):
    """按显示宽度折行，避免超出窗口。"""
    if cells(text) <= limit:
        return [text]
    lines, cur, w = [], '', 0
    for ch in text:
        cw = 2 if _wide(ch) else 1
        if w + cw > limit:
            lines.append(cur)
            cur, w = '  ' + ch, 2 + cw   # 续行缩进
        else:
            cur += ch
            w += cw
    if cur:
        lines.append(cur)
    return lines


def main():
    items = build_items()
    rows = []
    for kind, text in items:
        for seg in wrap(text, MAX_CELLS):
            rows.append((kind, seg))

    width_cells = max(cells(t) for _, t in rows)
    img_w = PAD * 2 + width_cells * CELL
    img_h = TITLE_H + PAD * 2 + len(rows) * LH
    img = Image.new('RGB', (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    # 标题栏
    draw.rectangle([0, 0, img_w, TITLE_H], fill=BAR)
    for i, color in enumerate(['#ff5f56', '#ffbd2e', '#27c93f']):
        cx = 22 + i * 24
        draw.ellipse([cx - 8, TITLE_H / 2 - 8, cx + 8, TITLE_H / 2 + 8], fill=color)
    title = 'ggboss@MacBook-Pro — ctf-training-platform — zsh'
    tw = sum(CELL * (2 if _wide(c) else 1) for c in title)
    draw_line(draw, (img_w - tw) / 2, TITLE_H / 2 - SIZE / 2 - 2, title, DIM)

    y = TITLE_H + PAD
    for kind, text in rows:
        if kind == 'cmd':
            prompt, rest = '$ ', text[2:] if text.startswith('$ ') else text
            draw_line(draw, PAD, y, prompt, PROMPT)
            draw_line(draw, PAD + cells(prompt) * CELL, y, rest, CMD)
        elif kind == 'log':
            # 哈希与引用着色
            parts = text.split()
            x = PAD
            for tok in parts:
                color = FG
                if tok.startswith('*'):
                    color = DIM
                elif len(tok) == 7 and all(c in '0123456789abcdef' for c in tok):
                    color = HASH
                elif tok.startswith('(HEAD') or tok.startswith('(origin') or tok.startswith('(main'):
                    color = REF
                draw_line(draw, x, y, tok, color)
                x += (cells(tok) + 1) * CELL
        else:
            _, color = style_for(kind, text)
            draw_line(draw, PAD, y, text, color)
        y += LH

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT, img.size)


if __name__ == '__main__':
    main()
