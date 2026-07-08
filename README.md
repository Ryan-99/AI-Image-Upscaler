# 🖼 AI 生图放大器

> 本地显卡加速的 AI 图片批量超分辨率放大工具，专治 **AI 生图分辨率不足**。
> 纯 Python 标准库 + sv-ttk 现代界面，开箱即用，支持打包成独立 exe 分发。

做 AI 漫画/AI 插画时，Midjourney、Stable Diffusion 等生成的图经常分辨率不够，
直接用于公众号、网页或印刷会糊。本项目把这些图**批量、无损、4 倍放大**到生产可用质量，
全部在本机显卡上跑，无需联网、无需上传。

---

## ✨ 特性

- **批量放大** —— 一次导入整批图片，自动排队处理，实时显示每张进度与 ✓/✗ 状态
- **GPU 加速** —— 基于 Real-ESRGAN (ncnn-vulkan)，走 Vulkan，AMD / Intel / NVIDIA 显卡通吃
- **漫画专用模型** —— 内置 `realesrgan-x4plus-anime` 等多种模型，对线条和色块还原极佳
- **现代界面** —— Win11 Fluent 风格（sv-ttk）、自绘圆角按钮、图标化操作、蓝/灰层次配色
- **🌙 浅/深色一键切换** —— 切换流畅无黑闪
- **💾 记住上次设置** —— 模型、倍数、格式、输出目录、主题自动恢复
- **免环境分发** —— 可一键打包成独立 exe，对方电脑无需装 Python

## 📷 界面预览

> 截图占位：建议在 `docs/` 放 `light.png` / `dark.png` 后替换此处
>
> `![浅色界面](docs/light.png)`　`![深色界面](docs/dark.png)`

## 🚀 快速开始

### 方式一：直接用打包好的 exe（推荐，普通用户）

1. 到 [Releases](../../releases) 下载 `AI生图放大器.zip`
2. 解压，双击 **`AI生图放大器.exe`**
3. 把要放大的图拖进「添加图片」，选模型 → 点「开始放大」→ 去 `output` 拿图

> 对方电脑无需安装 Python，无需联网，引擎和模型已全部打包进去。

### 方式二：从源码运行（开发者）

```bash
git clone https://github.com/Ryan-99/AI-Image-Upscaler.git
cd AI-Image-Upscaler

# 1. 放置引擎（见下方"获取引擎"）
# 2. 安装依赖
pip install sv-ttk pillow           # 运行界面；pillow 仅生成图标/打包用
pip install pyinstaller             # 打包用（可选）

# 3. 生成按钮图标和程序图标
python make_icons.py
python make_icon.py

# 4. 运行
python gui.py
```

### 获取放大引擎

引擎（Real-ESRGAN 预编译版）体积较大且为第三方产物，**不在本仓库**。请手动下载：

1. 下载 [`realesrgan-ncnn-vulkan-20220424-windows.zip`](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip)
2. 解压后的内容放入项目的 `bin/` 目录，使结构如下：
   ```
   bin/
   ├─ realesrgan-ncnn-vulkan.exe
   ├─ vcomp140.dll
   └─ models/        # 含 realesrgan-x4plus-anime 等模型
   ```

## 🧰 使用说明

| 控件 | 说明 |
|------|------|
| ① 待放大的图片 | 「添加图片」多选 / 「添加文件夹」批量导入 / 「清空」 |
| ② 放大设置 | 模型 / 倍数（2/3/4）/ 格式（png/jpg/webp） |
| ③ 输出目录 | 默认 `output`，可改、可一键打开 |
| 开始放大 | 底部主按钮，始终可见，带进度条 |
| 🌙/☀ 按钮 | 右上角，浅/深色切换 |

**模型选择建议**

| 模型 | 适用 | 倍数 |
|------|------|------|
| `realesrgan-x4plus-anime` ⭐默认 | 漫画/插画/线稿，质量最佳 | 4x |
| `realesr-animevideov3-x2` | 动漫风，要 2 倍 | 2x |
| `realesr-animevideov3-x4` | 动漫风，要 4 倍但更快 | 4x |
| `realesrgan-x4plus` | 真实照片/写实风 | 4x |

## 🏗 打包成 exe

```bash
# 直接用打包脚本（会自动清理旧产物）
./打包EXE.bat
# 或手动：
pyinstaller --noconfirm --windowed --name "AI生图放大器" ^
    --icon "assets/icon.ico" ^
    --add-data "bin;bin" --add-data "assets;assets" ^
    --collect-all sv_ttk gui.py
```

产物在 `dist/AI生图放大器/`，把整个文件夹压缩即可分发。

## 🛠 技术栈

- **[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)** (ncnn-vulkan) —— AI 超分辨率引擎（Vulkan GPU 加速）
- **Python + tkinter** —— GUI，纯标准库
- **[sv-ttk](https://github.com/rdbende/Sun-Valley-ttk-theme)** —— Win11 Fluent 主题
- **Pillow** —— 仅用于构建期生成图标 PNG / ICO
- **PyInstaller** —— 打包成独立 exe

## 📁 项目结构

```
AI-Image-Upscaler/
├─ gui.py              # GUI 主程序
├─ upscale.ps1         # 命令行批量脚本（无界面）
├─ make_icon.py        # 生成程序图标 ICO
├─ make_icons.py       # 生成界面按钮图标 PNG
├─ assets/             # 图标资源（程序图标 + 按钮图标）
├─ bin/                # 放大引擎（需自行下载，见上文）
├─ 打包EXE.bat          # 一键打包
├─ 启动GUI.bat          # 启动图形界面
└─ 一键放大.bat          # 命令行一键批处理
```

## ⚖️ 许可证与致谢

- 本项目代码采用 **MIT License**
- 放大能力由 **Real-ESRGAN**（BSD 3-Clause）提供，引擎版权归其作者所有
- 界面主题来自 **sv-ttk**（MIT）

## 🙏 鸣谢

- [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [rdbende/Sun-Valley-ttk-theme](https://github.com/rdbende/Sun-Valley-ttk-theme)
