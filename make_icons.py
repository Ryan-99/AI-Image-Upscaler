# -*- coding: utf-8 -*-
"""生成界面按钮用的扁平图标 PNG（浅/深两套配色），打包前运行。
运行时 gui.py 用 Tk 原生 PhotoImage 加载这些 PNG，无需在 exe 里打包 Pillow。"""
import os
from PIL import Image, ImageDraw

S = 4              # 超采样倍数
OUT = 24           # 最终边长(px)
N = OUT * S        # 绘制画布边长

OUTDIR = os.path.join("assets", "icons")
os.makedirs(OUTDIR, exist_ok=True)


def canvas():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    img.resize((OUT, OUT), Image.LANCZOS).save(os.path.join(OUTDIR, name))


# ---------- 各图标绘制 ----------
def ic_plus(col):
    img, d = canvas()
    t = N * 0.16
    cx = cy = N / 2
    d.rounded_rectangle([cx - t/2, N*0.20, cx + t/2, N*0.80], radius=t/2, fill=col)
    d.rounded_rectangle([N*0.20, cy - t/2, N*0.80, cy + t/2], radius=t/2, fill=col)
    return img


def ic_folder(col):
    img, d = canvas()
    d.rounded_rectangle([N*0.12, N*0.26, N*0.52, N*0.42], radius=N*0.05, fill=col)
    d.rounded_rectangle([N*0.12, N*0.34, N*0.88, N*0.76], radius=N*0.07, fill=col)
    return img


def ic_trash(col):
    img, d = canvas()
    d.rounded_rectangle([N*0.40, N*0.18, N*0.60, N*0.26], radius=N*0.03, fill=col)  # 提手
    d.rounded_rectangle([N*0.22, N*0.24, N*0.78, N*0.32], radius=N*0.04, fill=col)  # 盖
    d.polygon([(N*0.28, N*0.34), (N*0.72, N*0.34), (N*0.66, N*0.80), (N*0.34, N*0.80)], fill=col)  # 桶
    return img


def ic_dots(col):
    img, d = canvas()
    r = N * 0.075
    cy = N / 2
    for cx in (N*0.28, N*0.50, N*0.72):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return img


def ic_play(col):
    img, d = canvas()
    d.polygon([(N*0.32, N*0.22), (N*0.32, N*0.78), (N*0.80, N*0.50)], fill=col)
    return img


def ic_stop(col):
    img, d = canvas()
    d.rounded_rectangle([N*0.27, N*0.27, N*0.73, N*0.73], radius=N*0.09, fill=col)
    return img


def ic_sun(col):
    img, d = canvas()
    cx = cy = N / 2
    r = N * 0.18
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    rt = N * 0.05
    import math
    for k in range(8):
        a = math.radians(k * 45)
        x = cx + math.cos(a) * N * 0.34
        y = cy + math.sin(a) * N * 0.34
        d.ellipse([x - rt, y - rt, x + rt, y + rt], fill=col)
    return img


def ic_moon(col):
    img, d = canvas()
    d.ellipse([N*0.22, N*0.18, N*0.80, N*0.82], fill=col)        # 主圆
    cut = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(cut).ellipse([N*0.40, N*0.10, N*0.95, N*0.74], fill=col)  # 偏移圆
    img.paste((0, 0, 0, 0), (0, 0), cut.split()[3])             # 用偏移圆挖出月牙
    return img


GLYPHS = {
    "plus": ic_plus, "folder": ic_folder, "trash": ic_trash,
    "dots": ic_dots, "sun": ic_sun, "moon": ic_moon,
}

# 浅色主题按钮(浅底) -> 深灰图标；深色主题按钮(深底) -> 浅灰图标
COL_LIGHT = "#3c3c3c"
COL_DARK = "#e6e6e6"

for name, fn in GLYPHS.items():
    save(fn(COL_LIGHT), f"{name}_light.png")
    save(fn(COL_DARK), f"{name}_dark.png")

# 主按钮(蓝底)恒为白色 play；停止按钮用红色
save(ic_play("#ffffff"), "play_white.png")
save(ic_stop("#cf222e"), "stop_light.png")
save(ic_stop("#f87171"), "stop_dark.png")

print("按钮图标已生成到", OUTDIR)
print("文件:", sorted(os.listdir(OUTDIR)))
