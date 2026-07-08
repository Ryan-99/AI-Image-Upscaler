# -*- coding: utf-8 -*-
"""生成程序图标 assets/icon.ico —— 蓝色圆角底 + 白色向上双箭头(寓意放大/提升)"""
import os
from PIL import Image, ImageDraw

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 圆角方形背景 + 竖向蓝色渐变
radius = 56
top = (43, 143, 255)      # #2b8fff
bot = (0, 95, 184)        # #005fb8
bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
bgd = ImageDraw.Draw(bg)
for y in range(SIZE):
    t = y / SIZE
    r = int(top[0] + (bot[0] - top[0]) * t)
    g = int(top[1] + (bot[1] - top[1]) * t)
    b = int(top[2] + (bot[2] - top[2]) * t)
    bgd.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))
# 圆角遮罩
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255)
img.paste(bg, (0, 0), mask)

# 白色向上双箭头(V 形朝上)
d = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
cx = SIZE // 2
w = 64          # 半宽
th = 26         # 线宽


def chevron(cy):
    # 以 (cx,cy) 为顶点的朝上 V 形
    d.line([(cx - w, cy + w * 0.7), (cx, cy)], fill=white, width=th, joint="curve")
    d.line([(cx, cy), (cx + w, cy + w * 0.7)], fill=white, width=th, joint="curve")


chevron(96)     # 上箭头
chevron(150)    # 下箭头

os.makedirs("assets", exist_ok=True)
img.save(os.path.join("assets", "icon.ico"),
         sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(os.path.join("assets", "icon.png"))
print("图标已生成: assets/icon.ico")
