# ComfyUI-Qwen-Prompt-Rewrite

A ComfyUI custom node for Prompt Enhancer based on [Qwen-Image-2.1](https://github.com/QwenLM/Qwen-Image-2.1). Supports both Text-to-Image (T2I) prompt generation and Image-to-Image (I2I) prompt rewriting with dynamic UI that supports 1-9 image connections.

[中文指南](#中文安装指南) | [English Guide](#english-installation-guide)

---

## English Installation Guide

### 1. Install Custom Node
You can install this node via **ComfyUI Manager** by searching for this repository, or install it manually:

Navigate to your ComfyUI `custom_nodes` folder and clone this repository:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/kana112233/ComfyUI-kaola-qwen-image2.1-prompt-rewrite.git
cd ComfyUI-kaola-qwen-image2.1-prompt-rewrite
pip install -r requirements.txt
```

### 2. Download the Models
This node relies on standard HuggingFace directory formats, **NOT** single `.safetensors` files.

1. Go to HuggingFace or ModelScope to download the full repository:
   - For T2I (Text-only prompt enhancement): [Qwen/Qwen-Image-2.1-PE-T2I](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-T2I)
   - For I2I (Image reference prompt rewrite): [Qwen/Qwen-Image-2.1-PE-I2I](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I)
   - Uncensored I2I (Abliterated, community version): [base11231/Qwen-Image-2.1-PE-I2I-Abliterated](https://huggingface.co/base11231/Qwen-Image-2.1-PE-I2I-Abliterated)
2. Create a folder named after the model (e.g. `Qwen-Image-2.1-PE-I2I`) in your `ComfyUI/models/LLM` directory.
3. Put **all downloaded files** (including `config.json`, `tokenizer.json`, etc.) into this newly created folder.

### 3. Usage & Examples
Restart ComfyUI and load the workflow files from the `examples` folder:
- **`t2i_prompt_enhancer_workflow.json`**: Pure text prompt expansion.
- **`i2i_edit_workflow.json`**: Image-based prompt editing (dynamically supports 1-9 images).

*Note: This model uses the newest `qwen3_5` architecture. Ensure your `transformers` package is updated to the latest git branch as specified in `requirements.txt` (`pip install git+https://github.com/huggingface/transformers.git`).*

---

## 中文安装指南

### 1. 安装自定义节点
推荐使用 **ComfyUI Manager** 搜索并直接安装。如果你想手动安装：

进入 ComfyUI 的 `custom_nodes` 目录，克隆此仓库并安装依赖：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/kana112233/ComfyUI-kaola-qwen-image2.1-prompt-rewrite.git
cd ComfyUI-kaola-qwen-image2.1-prompt-rewrite
pip install -r requirements.txt
```

### 2. 下载模型
本项目基于标准的开源大语言模型架构（调用 `transformers`），因此**请勿**仅下载单文件，必须下载完整的模型文件夹。

1. 前往 HuggingFace 或魔搭社区 (ModelScope) 下载完整的模型仓库里的所有文件：
   - 纯文本提示词扩写模型：[Qwen/Qwen-Image-2.1-PE-T2I](https://modelscope.cn/models/qwen/Qwen-Image-2.1-PE-T2I)
   - 图像编辑重写模型：[Qwen/Qwen-Image-2.1-PE-I2I](https://modelscope.cn/models/qwen/Qwen-Image-2.1-PE-I2I)
   - 无审查 I2I 模型（社区破限版）：[base11231/Qwen-Image-2.1-PE-I2I-Abliterated](https://huggingface.co/base11231/Qwen-Image-2.1-PE-I2I-Abliterated)
2. 在你的 `ComfyUI/models/LLM` 目录下，新建一个模型文件夹（例如 `Qwen-Image-2.1-PE-I2I`）。
3. 将下载的**所有文件**（包含 `config.json`, `tokenizer.json` 等全部文件）放进该文件夹中。

### 3. 工作流使用
重启 ComfyUI 后，可直接拖入本项目 `examples` 文件夹下的工作流体验：
- **`t2i_prompt_enhancer_workflow.json`**：纯文本生成高质量英文提示词。
- **`i2i_edit_workflow.json`**：看图重写提示词（前端自带动态连线功能，最高支持 1-9 张图片同时传入）。

*注：由于该模型使用了极新的 `qwen3_5` 架构，必须确保你的 `transformers` 库是最新版（参考 `requirements.txt`，环境需执行 `pip install git+https://github.com/huggingface/transformers.git`）。否则会出现加载架构不认识的报错。*
