"""生成系统设计文档所需插图：功能模块图与 E-R 图。

运行：python3 scripts/build_figures.py
输出：docs/figures/module.png、docs/figures/er.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
from PIL import Image

FIG_DIR = Path(__file__).resolve().parent.parent / 'docs' / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = '/System/Library/Fonts/Supplemental/Songti.ttc'


def fp(size):
    return FontProperties(fname=FONT_PATH, size=size)


INK = '#1f2937'
LINE = '#7b8794'
BODY = '#eef3f8'
MID = '#dbe7f2'
ROOT = '#c3d7ea'


def box(ax, x, y, w, h, text, size=10, bg=BODY, lw=1.0):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle='round,pad=0,rounding_size=0.55',
                                linewidth=lw, edgecolor=INK, facecolor=bg, zorder=3))
    ax.text(x, y, text, ha='center', va='center', fontproperties=fp(size),
            color=INK, zorder=4, linespacing=1.6)


def seg(ax, pts, color=LINE, lw=1.0, arrow=False):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle='butt', zorder=2)
    if arrow:
        ax.annotate('', xy=pts[-1], xytext=pts[-2],
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                    shrinkA=0, shrinkB=0), zorder=2)


def module_figure():
    fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=200)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    box(ax, 50, 93, 34, 9, 'CTF 训练竞赛平台', size=13, bg=ROOT, lw=1.4)

    parents = [(16, '前台训练子系统'), (50, '后台管理子系统'), (84, '数据库服务层')]
    for x, name in parents:
        box(ax, x, 70, 28, 9, name, size=11, bg=MID)
        seg(ax, [(50, 88.5), (x, 74.5)])

    # 前台：两列各三项
    front = [(8.5, ['注册登录', '题库检索', '题目详情']),
             (24.5, ['flag 提交判定', '个人中心', '排行榜'])]
    for cx, names in front:
        for i, name in enumerate(names):
            y = 55.75 - i * 12
            box(ax, cx, y, 13, 7.5, name, size=9)
            if i == 0:
                seg(ax, [(16, 60.5), (cx, 60.5)])
                seg(ax, [(cx, 60.5), (cx, y + 3.75)])
            else:
                seg(ax, [(cx, y + 3.75 + 8.25), (cx, y + 3.75)])

    # 后台：两列各两项 + 中间一项
    back = [(43, ['题目管理', '公告管理']), (57, ['分类管理', '用户管理'])]
    for cx, names in back:
        for i, name in enumerate(names):
            y = 55.75 - i * 12
            box(ax, cx, y, 13, 7.5, name, size=9)
            if i == 0:
                seg(ax, [(cx, 60.5), (cx, y + 3.75)])
            else:
                seg(ax, [(cx, y + 3.75 + 8.25), (cx, y + 3.75)])
    seg(ax, [(43, 60.5), (57, 60.5)])
    box(ax, 50, 31.75, 13, 7.5, '审计日志', size=9)
    seg(ax, [(50, 60.5), (50, 35.5)])

    # 数据库服务层：两列各两项 + 中间一项
    db = [(75, ['视图查询', '触发器']), (89, ['存储过程', '基本表'])]
    for cx, names in db:
        for i, name in enumerate(names):
            y = 55.75 - i * 12
            box(ax, cx, y, 13, 7.5, name, size=9)
            if i == 0:
                seg(ax, [(cx, 60.5), (cx, y + 3.75)])
            else:
                seg(ax, [(cx, y + 3.75 + 8.25), (cx, y + 3.75)])
    seg(ax, [(75, 60.5), (89, 60.5)])
    box(ax, 82, 31.75, 13, 7.5, '完整性约束', size=9)
    seg(ax, [(82, 60.5), (82, 35.5)])
    # 父节点到总线
    seg(ax, [(16, 65.5), (16, 60.5)])
    seg(ax, [(50, 65.5), (50, 60.5)])
    seg(ax, [(84, 65.5), (84, 60.5)])

    fig.tight_layout(pad=0.2)
    fig.savefig(FIG_DIR / 'module.png', facecolor='white')
    plt.close(fig)
    Image.open(FIG_DIR / 'module.png').convert('RGB').save(FIG_DIR / 'module.png')
    print('已生成', FIG_DIR / 'module.png')


def er_figure():
    fig, ax = plt.subplots(figsize=(10.5, 7.0), dpi=200)
    ax.set_xlim(0, 108); ax.set_ylim(0, 100); ax.axis('off')

    W, H = 28, 13
    ents = {
        'users': (17, 80, '用户 Users', '用户编号 · 登录名\n口令散列 · 角色 · 状态'),
        'challenges': (52, 80, '题目 Challenges', '题目编号 · 题名 · 难度 · 分值\nflag 散列 · 上架状态'),
        'scorelogs': (88, 80, '积分日志 ScoreLogs', '日志编号 · 得分变动\n变动后总分 · 发生时间'),
        'solves': (88, 52, '解题计分 Solves', '用户编号 + 题目编号\n得分 · 首次正确提交 · 解出时间'),
        'categories': (17, 24, '题目分类 Categories', '分类编号 · 分类名称\n分类说明'),
        'submissions': (52, 24, '提交记录 Submissions', '提交编号 · flag 散列\n是否正确 · 提交时间'),
        'operationlogs': (88, 24, '操作日志 OperationLogs', '日志编号 · 操作类型\n操作对象 · 操作说明'),
    }
    pos = {}
    for key, (x, y, title, attrs) in ents.items():
        ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H,
                                    boxstyle='round,pad=0,rounding_size=0.55',
                                    linewidth=1.2, edgecolor=INK, facecolor=BODY, zorder=3))
        ax.text(x, y + 2.7, title, ha='center', va='center', fontproperties=fp(10),
                color=INK, zorder=4)
        ax.text(x, y - 2.5, attrs, ha='center', va='center', fontproperties=fp(8),
                color='#374151', zorder=4, linespacing=1.6)
        pos[key] = (x, y)

    def label(mx, my, text):
        ax.text(mx, my, text, ha='center', va='center', fontproperties=fp(8),
                color='#374151', zorder=6,
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.92))

    def line(pts, text, lx=None, ly=None):
        seg(ax, pts)
        if lx is None:
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
        label(lx, ly, text)

    def edge(a, side_a, b, side_b, text, lx=None, ly=None):
        xa, ya = pos[a]; xb, yb = pos[b]
        pa = {'r': (xa + W / 2, ya), 'l': (xa - W / 2, ya), 't': (xa, ya + H / 2),
              'b': (xa, ya - H / 2)}[side_a]
        pb = {'r': (xb + W / 2, yb), 'l': (xb - W / 2, yb), 't': (xb, yb + H / 2),
              'b': (xb, yb - H / 2)}[side_b]
        line([pa, pb], text, lx, ly)

    # 用户 → 题目（录入）
    edge('users', 'r', 'challenges', 'l', '录入 1:N', 34.5, 82.4)
    # 题目 → 积分日志（题目）
    edge('challenges', 'r', 'scorelogs', 'l', '题目 1:N', 70, 82.4)
    # 用户 → 积分日志（得分，走上边界）
    line([(17, 86.5), (17, 94.5), (88, 94.5), (88, 86.5)], '得分 1:N', 52, 96.3)
    # 分类 → 题目（归属）
    edge('categories', 't', 'challenges', 'b', '归属 1:N', 18.5, 50)
    # 题目 → 提交记录（被提交）
    edge('challenges', 'b', 'submissions', 't', '被提交 1:N', 52, 52)
    # 用户 → 提交记录（提交）
    edge('users', 'b', 'submissions', 'l', '提交 1:N', 31, 42)
    # 题目 → 解题计分（被解出）
    edge('challenges', 'r', 'solves', 't', '被解出 1:N', 72, 70)
    # 用户 → 解题计分（解出，走中线下方）
    line([(17, 73.5), (17, 64.5), (74, 64.5), (74, 52)], '解出 1:N', 46, 66)
    # 用户 → 操作日志（操作）
    edge('users', 'b', 'operationlogs', 'l', '操作 1:N', 56, 33)

    fig.tight_layout(pad=0.3)
    fig.savefig(FIG_DIR / 'er.png', facecolor='white')
    plt.close(fig)
    Image.open(FIG_DIR / 'er.png').convert('RGB').save(FIG_DIR / 'er.png')
    print('已生成', FIG_DIR / 'er.png')


if __name__ == '__main__':
    module_figure()
    er_figure()
