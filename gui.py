# -*- coding: utf-8 -*-
"""
AI 生图放大器  ·  AIImageUpscaler
基于 Real-ESRGAN ncnn-vulkan，调用本机显卡(Vulkan)加速。
界面：sv-ttk 现代主题，纯标准库 + sv_ttk。
"""
import os
import re
import sys
import json
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

import sv_ttk

APP_NAME = "AI 生图放大器"

# ---------- 路径解析（兼容 PyInstaller 打包） ----------
if getattr(sys, "frozen", False):
    # 打包后：引擎/模型/图标在解压出的临时资源目录，输入输出与配置放在 exe 同级目录
    RES_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
else:
    RES_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = RES_DIR

EXE = os.path.join(RES_DIR, "bin", "realesrgan-ncnn-vulkan.exe")
MODELS_DIR = os.path.join(RES_DIR, "bin", "models")
ICON = os.path.join(RES_DIR, "assets", "icon.ico")
ICONS_DIR = os.path.join(RES_DIR, "assets", "icons")
CONFIG = os.path.join(APP_DIR, "config.json")
DEFAULT_OUT = os.path.join(APP_DIR, "output")

# 设计配色（浅色 / 深色 各一套，切主题时自动适配）
ACCENT = {"light": "#005fb8", "dark": "#60cdff"}   # 强调蓝
MUTED = {"light": "#9aa1ab", "dark": "#8b9298"}     # 次要浅灰文字（解释/标注）

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

MODEL_INFO = {
    "realesrgan-x4plus-anime": "漫画/插画专用 4x（质量最佳，推荐）",
    "realesr-animevideov3-x2": "动漫风 2x（速度快）",
    "realesr-animevideov3-x3": "动漫风 3x",
    "realesr-animevideov3-x4": "动漫风 4x（速度快）",
    "realesrgan-x4plus":       "通用照片 4x（写实风）",
}

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

ST_WAIT, ST_RUN, ST_OK, ST_FAIL = "待处理", "处理中…", "✓ 完成", "✗ 失败"


def list_images_in_dir(folder):
    out = []
    try:
        for name in sorted(os.listdir(folder)):
            full = os.path.join(folder, name)
            if name.lower().endswith(IMG_EXTS) and os.path.isfile(full):
                out.append(full)
    except OSError:
        pass
    return out


class RoundedButton(tk.Canvas):
    """自绘圆角按钮（Canvas），支持图标+文字、悬停、禁用，圆角可自定义。"""

    def __init__(self, parent, text="", image=None, command=None,
                 radius=16, height=44, padx=22, gap=8,
                 font=("Microsoft YaHei UI", 11), weight="normal",
                 fill="#e8e8e8", fg="#1a1a1a", active=None,
                 disabled_fill="#dddddd", disabled_fg="#9a9a9a", bg="#fafafa"):
        super().__init__(parent, height=height, bg=bg,
                         highlightthickness=0, bd=0, relief="flat")
        self.command = command
        self.radius = radius
        self.padx = padx
        self.gap = gap
        self._font = tkfont.Font(family=font[0], size=font[1], weight=weight)
        self._text = text
        self._image = image
        self._fill = fill
        self._fg = fg
        self._active = active or fill
        self._dfill = disabled_fill
        self._dfg = disabled_fg
        self._state = "normal"
        self._hover = False
        self.configure(width=self._content_width())
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _content_width(self):
        tw = self._font.measure(self._text) if self._text else 0
        iw = self._image.width() if self._image else 0
        g = self.gap if (self._text and self._image) else 0
        return tw + iw + g + self.padx * 2

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        if w <= 1:
            w = self._content_width()
        h = int(self["height"])
        r = max(2, min(self.radius, h // 2, w // 2))
        if self._state == "disabled":
            fill, fg = self._dfill, self._dfg
        elif self._hover:
            fill, fg = self._active, self._fg
        else:
            fill, fg = self._fill, self._fg
        d = 2 * r
        # 圆角矩形：四角圆 + 两条矩形
        self.create_oval(0, 0, d, d, fill=fill, outline=fill)
        self.create_oval(w - d, 0, w, d, fill=fill, outline=fill)
        self.create_oval(0, h - d, d, h, fill=fill, outline=fill)
        self.create_oval(w - d, h - d, w, h, fill=fill, outline=fill)
        self.create_rectangle(r, 0, w - r, h, fill=fill, outline=fill)
        self.create_rectangle(0, r, w, h - r, fill=fill, outline=fill)
        # 居中内容（图标 + 文字）
        tw = self._font.measure(self._text) if self._text else 0
        iw = self._image.width() if self._image else 0
        g = self.gap if (self._text and self._image) else 0
        x = (w - (tw + iw + g)) // 2
        cy = h // 2
        if self._image:
            self.create_image(x, cy, image=self._image, anchor="w")
            x += iw + g
        if self._text:
            self.create_text(x, cy, text=self._text, fill=fg, font=self._font, anchor="w")

    def _enter(self, e):
        if self._state == "normal":
            self._hover = True
            self._draw()

    def _leave(self, e):
        self._hover = False
        self._draw()

    def _click(self, e):
        if self._state == "normal" and self.command:
            if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= int(self["height"]):
                self.command()

    def set_state(self, state):
        self._state = state
        self._draw()

    def set_style(self, fill=None, fg=None, active=None, bg=None, image=False):
        if fill is not None:
            self._fill = fill
        if fg is not None:
            self._fg = fg
        if active is not None:
            self._active = active
        if bg is not None:
            self.configure(bg=bg)
        if image is not False:
            self._image = image
        self.configure(width=self._content_width())
        self._draw()


class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.withdraw()  # 构建期间先隐藏，避免控件未就绪时黑闪
        root.geometry("1180x820")
        # 让任务栏图标与窗口/exe 图标一致（独立 AppUserModelID）
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID("AIImageUpscaler.App")
        except Exception:
            pass
        try:
            root.iconbitmap(default=ICON)
        except Exception:
            pass

        self.files = []
        self.worker = None
        self.proc = None
        self.stop_flag = threading.Event()
        self.msgq = queue.Queue()
        self.cfg = self._load_config()
        self.theme = self.cfg.get("theme", "light")
        self.icons = {}          # 当前主题下加载的按钮图标(PhotoImage)
        self._round_btns = []    # 自绘圆角按钮，切主题时统一改色
        self._muted_labels = []  # 浅灰解释文字(原生tk.Label，sv-ttk的ttk.Label不认foreground)

        self._init_style()
        self._load_icons()
        self._build_ui()
        self._apply_config_to_ui()
        self._fit_window()       # 按屏幕大小自适应并居中，避免超出屏幕被截断
        self._poll_queue()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        # 先显示窗口，再异步应用圆角/标题栏配色（这两者需窗口已映射，且耗时，放后面不阻塞显示）
        self.root.after(20, self.root.deiconify)
        self.root.after(60, self._apply_window_chrome)

        if not os.path.exists(EXE):
            self.log(f"[错误] 找不到放大引擎：{EXE}")
            messagebox.showerror("缺少引擎", f"未找到放大引擎：\n{EXE}")

    # ---------- 窗口外观（Win11 圆角 + 深/浅色标题栏） ----------
    def _apply_window_chrome(self):
        if os.name != "nt":
            return
        try:
            from ctypes import windll, byref, c_int, sizeof
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2（Win11 圆角）
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, byref(c_int(2)), sizeof(c_int))
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20（标题栏跟随浅/深色）
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, byref(c_int(1 if self.is_dark else 0)), sizeof(c_int))
        except Exception:
            pass

    def _fit_window(self):
        """按当前屏幕大小自适应窗口并居中，避免窗口超出屏幕导致底部被截断。
        注意：此处不调用 update_idletasks（那会触发一次昂贵的全量重排），
        直接用 winfo_screen* 读屏幕尺寸即可。"""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(1200, max(1000, int(sw * 0.92)))
        h = min(840, max(640, int(sh * 0.85)))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 16)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(min(1000, w), min(640, h))

    # ---------- 配置持久化 ----------
    def _load_config(self):
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        data = {
            "model": self.model_var.get(),
            "scale": self.scale_var.get(),
            "fmt": self.fmt_var.get(),
            "out": self.out_var.get(),
            "theme": self.theme,
        }
        try:
            with open(CONFIG, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _apply_config_to_ui(self):
        c = self.cfg
        model = c.get("model")
        if model in MODEL_INFO:
            idx = list(MODEL_INFO.keys()).index(model)
            self.cmb_model.current(idx)
            self.model_var.set(model)
        if c.get("scale") in ("2", "3", "4"):
            self.scale_var.set(c["scale"])
        if c.get("fmt") in ("png", "jpg", "webp"):
            self.fmt_var.set(c["fmt"])
        if c.get("out"):
            self.out_var.set(c["out"])

    def _on_close(self):
        self._save_config()
        try:
            self.root.after_cancel(self._poll_id)
        except Exception:
            pass
        self.root.destroy()

    # ---------- 样式 ----------
    def _init_style(self):
        sv_ttk.set_theme(self.theme)
        self.is_dark = (self.theme == "dark")
        self.style = ttk.Style()
        self._apply_styles()

    def _load_icons(self):
        """按当前主题加载按钮图标 PNG（Tk 原生，无需 Pillow）。"""
        v = "dark" if self.is_dark else "light"
        spec = {
            "plus": f"plus_{v}.png", "folder": f"folder_{v}.png",
            "trash": f"trash_{v}.png", "dots": f"dots_{v}.png",
            "sun": f"sun_{v}.png", "moon": f"moon_{v}.png",
            "play": "play_white.png", "stop": f"stop_{v}.png",
        }
        self.icons = {}
        for key, fn in spec.items():
            try:
                self.icons[key] = tk.PhotoImage(file=os.path.join(ICONS_DIR, fn))
            except Exception:
                self.icons[key] = None

    def _refresh_icons(self):
        self._load_icons()
        self._recolor_buttons()

    # ---------- 圆角按钮：配色 / 工厂 / 主题刷新 ----------
    def _btn_bg(self):
        return self.style.lookup("TFrame", "background") or (
            "#1c1c1c" if self.is_dark else "#fafafa")

    def _palette(self):
        bg = self._btn_bg()
        if self.is_dark:
            tool = ("#3a3a3a", "#e8e8e8", "#474747")   # 填充 / 文字 / 悬停
            stop = ("#3a3a3a", "#f87171", "#474747")
        else:
            tool = ("#ececec", "#1a1a1a", "#e0e0e0")
            stop = ("#ececec", "#cf222e", "#e0e0e0")
        accent = ("#0a84ff", "#ffffff", "#3a9bff")     # 主按钮蓝，两套主题一致
        return bg, tool, accent, stop

    def _round_button(self, parent, role, text, icon_key, command,
                      radius=14, height=42, font_size=11, weight="normal", padx=20):
        bg, tool, accent, stop = self._palette()
        if role == "accent":
            f, fg, ac = accent; img = self.icons.get("play")
        elif role == "stop":
            f, fg, ac = stop; img = self.icons.get("stop")
        elif role == "theme":
            f, fg, ac = tool; img = self.icons.get("sun" if self.is_dark else "moon")
        else:
            f, fg, ac = tool; img = self.icons.get(icon_key)
        btn = RoundedButton(parent, text=text, image=img, command=command,
                            radius=radius, height=height, padx=padx,
                            font=("Microsoft YaHei UI", font_size), weight=weight,
                            fill=f, fg=fg, active=ac, bg=bg)
        self._round_btns.append({"w": btn, "role": role, "icon": icon_key})
        return btn

    def _recolor_buttons(self):
        bg, tool, accent, stop = self._palette()
        for d in self._round_btns:
            btn, role, icon_key = d["w"], d["role"], d["icon"]
            if role == "accent":
                btn.set_style(fill=accent[0], fg=accent[1], active=accent[2],
                              bg=bg, image=self.icons.get("play"))
            elif role == "stop":
                btn.set_style(fill=stop[0], fg=stop[1], active=stop[2],
                              bg=bg, image=self.icons.get("stop"))
            elif role == "theme":
                btn.set_style(fill=tool[0], fg=tool[1], active=tool[2], bg=bg,
                              image=self.icons.get("sun" if self.is_dark else "moon"))
            else:
                btn.set_style(fill=tool[0], fg=tool[1], active=tool[2],
                              bg=bg, image=self.icons.get(icon_key))

    # ---------- 浅灰解释文字（原生 tk.Label，确保 foreground 生效）----------
    def _muted_label(self, parent, text, small=False):
        font = ("Microsoft YaHei UI", 10 if small else 11)
        bg = self.style.lookup(parent.winfo_class(), "background") or self._btn_bg()
        lbl = tk.Label(parent, text=text, font=font, fg=MUTED[self.theme],
                       bg=bg, bd=0, highlightthickness=0)
        self._muted_labels.append(lbl)
        return lbl

    def _recolor_muted(self):
        for lbl in self._muted_labels:
            p = lbl.nametowidget(lbl.winfo_parent())
            bg = self.style.lookup(p.winfo_class(), "background") or self._btn_bg()
            lbl.configure(fg=MUTED[self.theme], bg=bg)

    def _apply_styles(self):
        """配置自定义样式。sv_ttk 切换主题会重置 ttk 样式，故每次切换后都要重调。"""
        style = self.style
        base = "Microsoft YaHei UI"
        self.root.option_add("*Font", (base, 10))
        accent = ACCENT[self.theme]
        muted = MUTED[self.theme]

        style.configure("Title.TLabel", font=(base, 23, "bold"))
        style.configure("Muted.TLabel", font=(base, 11), foreground=muted)
        style.configure("MutedSmall.TLabel", font=(base, 10), foreground=muted)
        style.configure("Card.TLabelframe.Label", font=(base, 13, "bold"), foreground=accent)
        # 普通图标按钮：加大内边距，图标+文字
        style.configure("Tool.TButton", font=(base, 11), padding=(14, 10))
        # 主按钮（蓝色填充）：更大、更粗
        style.configure("Accent.TButton", font=(base, 14, "bold"), padding=(20, 15))
        # 停止按钮
        style.configure("Stop.TButton", font=(base, 12), padding=(16, 12))
        # 主题切换：图标按钮
        style.configure("Icon.TButton", padding=10)
        style.configure("Treeview", rowheight=34, font=(base, 11))
        style.configure("Treeview.Heading", font=(base, 11, "bold"))

    def toggle_theme(self):
        # 切换过程盖上纯色遮罩，避免控件半旧半新造成的黑闪
        bg = self.style.lookup("TFrame", "background") or self._btn_bg()
        overlay = tk.Frame(self.root, bg=bg)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.lift()

        def _do():
            sv_ttk.toggle_theme()
            self.is_dark = not self.is_dark
            self.theme = "dark" if self.is_dark else "light"
            self._apply_styles()
            self._refresh_icons()
            self._recolor_muted()
            self._config_tree_tags()
            self._apply_window_chrome()
            # 让重绘落定后再撤掉遮罩
            self.root.after(30, lambda: overlay.destroy())

        self.root.after(10, _do)

    def _config_tree_tags(self):
        if self.is_dark:
            ok, fail, run = "#4ade80", "#f87171", "#60cdff"
        else:
            ok, fail, run = "#1a7f37", "#cf222e", "#0969da"
        self.tree.tag_configure("ok", foreground=ok)
        self.tree.tag_configure("fail", foreground=fail)
        self.tree.tag_configure("run", foreground=run)

    # ---------- 界面 ----------
    def _build_ui(self):
        ic = self.icons

        # 顶部标题栏
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=28, pady=(20, 12))
        ttk.Label(header, text="🖼  " + APP_NAME, style="Title.TLabel").pack(side="left")
        self.btn_theme = self._round_button(header, "theme", "", None,
                                            self.toggle_theme, radius=14, height=44, padx=14)
        self.btn_theme.pack(side="right", anchor="n")

        ttk.Separator(self.root).pack(fill="x", padx=28)

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=28, pady=16)

        # --- 左列：文件队列 ---
        left_col = ttk.Frame(body)
        left_col.pack(side="left", fill="both", expand=True)

        fq = ttk.LabelFrame(left_col, text=" ① 待放大的图片 ", style="Card.TLabelframe")
        fq.pack(fill="both", expand=True)

        tbar = ttk.Frame(fq)
        tbar.pack(fill="x", padx=14, pady=(14, 4))
        b1 = self._round_button(tbar, "tool", " 添加图片", "plus", self.add_files,
                                radius=14, height=40, padx=16)
        b1.pack(side="left")
        b2 = self._round_button(tbar, "tool", " 添加文件夹", "folder", self.add_folder,
                                radius=14, height=40, padx=16)
        b2.pack(side="left", padx=10)
        b3 = self._round_button(tbar, "tool", " 清空", "trash", self.clear_files,
                                radius=14, height=40, padx=16)
        b3.pack(side="left")
        self.lbl_count = self._muted_label(tbar, "共 0 张")
        self.lbl_count.pack(side="right")
        self._muted_label(fq, "支持 PNG / JPG / WEBP / BMP，可多选或添加整个文件夹",
                          small=True).pack(anchor="w", padx=16, pady=(0, 8))

        tree_wrap = ttk.Frame(fq)
        tree_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tree = ttk.Treeview(tree_wrap, columns=("name", "status"),
                                 show="headings", selectmode="extended")
        self.tree.heading("name", text="文件名")
        self.tree.heading("status", text="状态")
        self.tree.column("name", width=380, anchor="w")
        self.tree.column("status", width=110, anchor="center")
        tsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")
        self._config_tree_tags()

        # --- 右列：设置 + 控制 ---
        right_col = ttk.Frame(body)
        right_col.pack(side="right", fill="y", padx=(20, 0))
        right_col.configure(width=400)
        right_col.pack_propagate(False)

        fs = ttk.LabelFrame(right_col, text=" ② 放大设置 ", style="Card.TLabelframe")
        fs.pack(fill="x")
        inner = ttk.Frame(fs)
        inner.pack(fill="x", padx=16, pady=16)

        self._muted_label(inner, "模型").pack(anchor="w")
        self.model_var = tk.StringVar(value="realesrgan-x4plus-anime")
        self.cmb_model = ttk.Combobox(inner, state="readonly",
                                      values=[f"{k} — {v}" for k, v in MODEL_INFO.items()])
        self.cmb_model.current(0)
        self.cmb_model.pack(fill="x", pady=(4, 2))
        self.cmb_model.bind("<<ComboboxSelected>>", self._on_model_change)
        self._muted_label(inner, "漫画/插画选默认项即可", small=True).pack(anchor="w", pady=(0, 12))

        row2 = ttk.Frame(inner)
        row2.pack(fill="x")
        c1 = ttk.Frame(row2); c1.pack(side="left", expand=True, fill="x")
        self._muted_label(c1, "倍数").pack(anchor="w")
        self.scale_var = tk.StringVar(value="4")
        ttk.Combobox(c1, state="readonly", width=8, values=["2", "3", "4"],
                     textvariable=self.scale_var).pack(anchor="w", pady=(4, 0))
        c2 = ttk.Frame(row2); c2.pack(side="left", expand=True, fill="x")
        self._muted_label(c2, "格式").pack(anchor="w")
        self.fmt_var = tk.StringVar(value="png")
        ttk.Combobox(c2, state="readonly", width=8, values=["png", "jpg", "webp"],
                     textvariable=self.fmt_var).pack(anchor="w", pady=(4, 0))

        fo = ttk.LabelFrame(right_col, text=" ③ 输出目录 ", style="Card.TLabelframe")
        fo.pack(fill="x", pady=16)
        oin = ttk.Frame(fo)
        oin.pack(fill="x", padx=16, pady=16)
        self.out_var = tk.StringVar(value=DEFAULT_OUT)
        ttk.Entry(oin, textvariable=self.out_var).pack(fill="x")
        obtn = ttk.Frame(oin)
        obtn.pack(fill="x", pady=(10, 0))
        bb = self._round_button(obtn, "tool", " 浏览", "dots", self.choose_output,
                                radius=14, height=40, padx=14)
        bb.pack(side="left", expand=True, fill="x", padx=(0, 6))
        bo = self._round_button(obtn, "tool", " 打开", "folder", self.open_output,
                                radius=14, height=40, padx=14)
        bo.pack(side="left", expand=True, fill="x", padx=(6, 0))

        # ---- 窗口底部固定操作区（居中按钮组，始终完整可见）----
        action_bar = ttk.Frame(self.root)
        action_bar.pack(side="bottom", fill="x", padx=28, pady=(12, 20))
        btns = ttk.Frame(action_bar)
        btns.pack()  # 不填充 -> 按钮组水平居中
        self.btn_start = self._round_button(btns, "accent", "  开始放大", "play",
                                            self.start, radius=18, height=46,
                                            font_size=13, weight="bold", padx=30)
        self.btn_start.pack(side="left")
        self.btn_stop = self._round_button(btns, "stop", "  停止", "stop",
                                           self.stop, radius=18, height=46,
                                           font_size=12, padx=24)
        self.btn_stop.pack(side="left", padx=(14, 0))
        self.btn_stop.set_state("disabled")

        prog = ttk.Frame(self.root)
        prog.pack(side="bottom", fill="x", padx=28)
        self.lbl_status = self._muted_label(prog, "就绪")
        self.lbl_status.pack(anchor="w")
        self.pb_all = ttk.Progressbar(prog, mode="determinate")
        self.pb_all.pack(fill="x", pady=(6, 3))
        self.pb_one = ttk.Progressbar(prog, mode="determinate", maximum=100)
        self.pb_one.pack(fill="x")

        self.txt = None  # 已移除日志面板（节省垂直空间，让操作按钮始终完整可见）

    # ---------- 文件列表 ----------
    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(self.files):
            self.tree.insert("", "end", iid=str(i),
                             values=(os.path.basename(p), ST_WAIT))
        self.lbl_count.config(text=f"共 {len(self.files)} 张")

    def _set_row(self, i, status, tag=""):
        iid = str(i)
        if self.tree.exists(iid):
            name = self.tree.item(iid, "values")[0]
            self.tree.item(iid, values=(name, status), tags=(tag,) if tag else ())
            self.tree.see(iid)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有文件", "*.*")])
        added = 0
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                added += 1
        if added:
            self._refresh_list()
            self.log(f"添加了 {added} 张图片")

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return
        found = [p for p in list_images_in_dir(folder) if p not in self.files]
        self.files.extend(found)
        self._refresh_list()
        self.log(f"从文件夹添加了 {len(found)} 张图片")

    def clear_files(self):
        self.files = []
        self._refresh_list()

    def choose_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.out_var.set(folder)

    def open_output(self):
        out = self.out_var.get()
        os.makedirs(out, exist_ok=True)
        if os.name == "nt":
            os.startfile(out)

    def _on_model_change(self, _=None):
        idx = self.cmb_model.current()
        model = list(MODEL_INFO.keys())[idx]
        self.model_var.set(model)
        if model.endswith("x2"):
            self.scale_var.set("2")
        elif model.endswith("x3"):
            self.scale_var.set("3")
        else:
            self.scale_var.set("4")

    # ---------- 日志 / 队列轮询 ----------
    def log(self, text):
        # 日志面板已移除；保留方法以兼容调用，无操作
        if self.txt is None:
            return
        self.txt.configure(state="normal")
        self.txt.insert(tk.END, text + "\n")
        self.txt.see(tk.END)
        self.txt.configure(state="disabled")

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.msgq.get_nowait()
                if kind == "log":
                    self.log(payload)
                elif kind == "status":
                    self.lbl_status.config(text=payload)
                elif kind == "one":
                    self.pb_one["value"] = payload
                elif kind == "all":
                    done, total = payload
                    self.pb_all["maximum"] = total
                    self.pb_all["value"] = done
                elif kind == "row":
                    i, status, tag = payload
                    self._set_row(i, status, tag)
                elif kind == "done":
                    self._on_finished(payload)
        except queue.Empty:
            pass
        self._poll_id = self.root.after(100, self._poll_queue)

    # ---------- 运行 ----------
    def start(self):
        if self.worker and self.worker.is_alive():
            return
        if not self.files:
            messagebox.showwarning("没有图片", "请先添加要放大的图片。")
            return
        if not os.path.exists(EXE):
            messagebox.showerror("缺少引擎", f"未找到：\n{EXE}")
            return

        out_dir = self.out_var.get().strip()
        os.makedirs(out_dir, exist_ok=True)

        model = self.model_var.get()
        scale = self.scale_var.get()
        fmt = self.fmt_var.get()
        self._save_config()  # 记住本次设置

        self.stop_flag.clear()
        self.btn_start.set_state("disabled")
        self.btn_stop.set_state("normal")
        self.pb_all["value"] = 0
        self.pb_one["value"] = 0
        for i in range(len(self.files)):
            self._set_row(i, ST_WAIT, "")

        files = list(self.files)
        self.log("=" * 46)
        self.log(f"开始：{len(files)} 张 | {model} | {scale}x | {fmt}")

        self.worker = threading.Thread(
            target=self._run_batch, args=(files, out_dir, model, scale, fmt), daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_flag.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.msgq.put(("status", "正在停止…"))

    def _run_batch(self, files, out_dir, model, scale, fmt):
        total = len(files)
        ok = fail = 0
        pct_re = re.compile(rb"(\d+(?:\.\d+)?)%")

        for i, src in enumerate(files):
            if self.stop_flag.is_set():
                break
            base = os.path.splitext(os.path.basename(src))[0]
            dst = os.path.join(out_dir, f"{base}.{fmt}")

            self.msgq.put(("status", f"处理中 {i+1}/{total}：{os.path.basename(src)}"))
            self.msgq.put(("row", (i, ST_RUN, "run")))
            self.msgq.put(("one", 0))

            cmd = [EXE, "-i", src, "-o", dst, "-n", model,
                   "-s", scale, "-f", fmt, "-m", MODELS_DIR]
            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                    creationflags=CREATE_NO_WINDOW)
            except Exception as e:
                self.msgq.put(("log", f"  ✗ 启动失败：{e}"))
                self.msgq.put(("row", (i, ST_FAIL, "fail")))
                fail += 1
                continue

            buf = b""
            while True:
                chunk = self.proc.stderr.read(64)
                if not chunk:
                    break
                buf += chunk
                m = None
                for m in pct_re.finditer(buf):
                    pass
                if m:
                    try:
                        self.msgq.put(("one", float(m.group(1))))
                    except ValueError:
                        pass
                    buf = buf[-16:]
            self.proc.wait()

            if self.stop_flag.is_set():
                self.msgq.put(("row", (i, ST_WAIT, "")))
                self.msgq.put(("log", "  已停止"))
                break

            if self.proc.returncode == 0 and os.path.exists(dst):
                self.msgq.put(("one", 100))
                self.msgq.put(("row", (i, ST_OK, "ok")))
                self.msgq.put(("log", f"  ✓ {os.path.basename(src)} → {base}.{fmt}"))
                ok += 1
            else:
                self.msgq.put(("row", (i, ST_FAIL, "fail")))
                self.msgq.put(("log", f"  ✗ 失败：{os.path.basename(src)}"))
                fail += 1

            self.msgq.put(("all", (i + 1, total)))

        self.proc = None
        self.msgq.put(("done", (ok, fail, self.stop_flag.is_set())))

    def _on_finished(self, payload):
        ok, fail, stopped = payload
        self.btn_start.set_state("normal")
        self.btn_stop.set_state("disabled")
        if stopped:
            self.lbl_status.config(text=f"已停止（成功 {ok} / 失败 {fail}）")
            self.log(f"已停止。成功 {ok}，失败 {fail}。")
        else:
            self.lbl_status.config(text=f"✓ 完成！成功 {ok} / 失败 {fail}")
            self.log("=" * 46)
            self.log(f"全部完成：成功 {ok}，失败 {fail}。输出：{self.out_var.get()}")
            if ok and not fail:
                messagebox.showinfo("完成", f"全部 {ok} 张放大完成！\n\n输出目录：\n{self.out_var.get()}")


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
