import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, LogitsProcessor, LogitsProcessorList
import folder_paths
import os
from PIL import Image
import numpy as np

from .qwen_pe_core import PROFILES, split_thinking, parse_answer

# Register LLM/prompts path in ComfyUI
llm_prompts_dir = os.path.join(folder_paths.models_dir, "LLM", "prompts")
if not os.path.exists(llm_prompts_dir):
    try:
        os.makedirs(llm_prompts_dir, exist_ok=True)
    except Exception:
        pass

def get_prompt_files():
    if not os.path.exists(llm_prompts_dir):
        return ["default"]
    
    files = [f for f in os.listdir(llm_prompts_dir) if f.endswith('.txt')]
    if not files:
        return ["default"]
    return files

def read_prompt_file(filename):
    if filename == "default" or not filename:
        return "You are a prompt enhancer..."
    
    filepath = os.path.join(llm_prompts_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "You are a prompt enhancer..."

class PresencePenalty(LogitsProcessor):
    def __init__(self, penalty: float, prompt_len: int):
        self.penalty = penalty
        self.prompt_len = prompt_len

    def __call__(self, input_ids, scores):
        for b in range(input_ids.shape[0]):
            generated = input_ids[b, self.prompt_len:]
            if generated.numel():
                scores[b, generated.unique()] -= self.penalty
        return scores

def get_model_list():
    models = ["Qwen/Qwen-Image-2.1-PE-T2I", "Qwen/Qwen-Image-2.1-PE-I2I"]
    
    # 扫描本地可能的目录
    search_dirs = []
    if "text_encoders" in folder_paths.folder_names_and_paths:
        search_dirs.extend(folder_paths.get_folder_paths("text_encoders"))
    if "LLM" in folder_paths.folder_names_and_paths:
        search_dirs.extend(folder_paths.get_folder_paths("LLM"))
    if "clip" in folder_paths.folder_names_and_paths:
        search_dirs.extend(folder_paths.get_folder_paths("clip"))
        
    for base_dir in search_dirs:
        if os.path.exists(base_dir):
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                # 检查是否为包含 config.json 的模型文件夹
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "config.json")):
                    if item not in models:
                        models.append(item)
    
    return models

class Qwen2_1_PE_Loader:
    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数
        """
        return {"required": {
            "model_path": (get_model_list(), ),
            "dtype": (["bfloat16", "float16", "float32"], {"default": "bfloat16"}),
            "device": (["cuda", "cpu"], {"default": "cuda"}),
        }}
    
    RETURN_TYPES = ("QWEN_PE_MODEL",)
    FUNCTION = "load"
    CATEGORY = "Qwen2.1"

    def load(self, model_path, dtype, device):
        dtype_map = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}
        
        # Resolve path against models dir if it's a relative local path
        if not os.path.isabs(model_path) and not "/" in model_path and not "\\" in model_path:
            search_paths = []
            if "text_encoders" in folder_paths.folder_names_and_paths:
                search_paths.extend(folder_paths.get_folder_paths("text_encoders"))
            if "LLM" in folder_paths.folder_names_and_paths:
                search_paths.extend(folder_paths.get_folder_paths("LLM"))
            else:
                search_paths.append(os.path.join(folder_paths.models_dir, "LLM"))
            if "clip" in folder_paths.folder_names_and_paths:
                search_paths.extend(folder_paths.get_folder_paths("clip"))
                
            for base_dir in search_paths:
                potential_path = os.path.join(base_dir, model_path)
                if os.path.exists(potential_path):
                    model_path = potential_path
                    break

        processor = AutoProcessor.from_pretrained(model_path)
        model = AutoModelForImageTextToText.from_pretrained(
            model_path, dtype=dtype_map[dtype], low_cpu_mem_usage=True
        ).to(device).eval()
        return ({"model": model, "processor": processor, "device": device},)

class Qwen2_1_PE_Rewrite:
    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数
        """
        return {"required": {
            "qwen_pe_model": ("QWEN_PE_MODEL",),
            "task": (["t2i", "edit"], {"default": "t2i"}),
            "system_prompt_file": (get_prompt_files(),),
            "prompt": ("STRING", {"multiline": True}),
            "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
            "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
            "top_k": ("INT", {"default": 20, "min": 0, "max": 100}),
            "presence_penalty": ("FLOAT", {"default": 1.5, "min": 0.0, "max": 2.0, "step": 0.01}),
            "max_new_tokens": ("INT", {"default": 16256, "min": 1, "max": 32768}),
            "seed": ("INT", {"default": 42, "min": 0, "max": 0xffffffffffffffff}),
        }, "optional": {
            "image_1": ("IMAGE",),
            "image_2": ("IMAGE",),
            "image_3": ("IMAGE",),
            "image_4": ("IMAGE",),
            "image_5": ("IMAGE",),
            "image_6": ("IMAGE",),
            "image_7": ("IMAGE",),
            "image_8": ("IMAGE",),
            "image_9": ("IMAGE",),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "wh_ratio", "ratio_follow", "thinking")
    FUNCTION = "rewrite"
    CATEGORY = "Qwen2.1"

    @torch.inference_mode()
    def rewrite(self, qwen_pe_model, task, system_prompt_file, prompt, temperature, top_p, top_k, presence_penalty, max_new_tokens, seed, **kwargs):
        model = qwen_pe_model["model"]
        processor = qwen_pe_model["processor"]
        device = qwen_pe_model["device"]
        
        profile = PROFILES[task]
        system_prompt = read_prompt_file(system_prompt_file)
        
        # Format image
        images = []
        if task == "edit":
            # 收集所有传入的 image_X
            input_images = []
            for i in range(1, 10):
                img_key = f"image_{i}"
                if img_key in kwargs and kwargs[img_key] is not None:
                    input_images.append(kwargs[img_key])
            
            for img_tensor in input_images:
                # 处理可能存在的批次
                for i in range(img_tensor.shape[0]):
                    img = img_tensor[i].cpu().numpy() * 255.0
                    img = img.astype(np.uint8)
                    pil_img = Image.fromarray(img)
                    
                    # Max pixels check
                    max_pixels = profile["image_max_pixels"]
                    w, h = pil_img.size
                    if max_pixels and w * h > max_pixels:
                        s = (max_pixels / float(w * h)) ** 0.5
                        pil_img = pil_img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
                    images.append(pil_img)
            
        # Build messages
        user_content = []
        for im in images:
            user_content.append({"type": "image", "image": im})
        user_content.append({"type": "text", "text": prompt})
        
        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": user_content},
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            enable_thinking=True,
        ).to(device)

        if "mm_token_type_ids" not in inputs and hasattr(processor, "create_mm_token_type_ids"):
            inputs["mm_token_type_ids"] = processor.create_mm_token_type_ids(inputs["input_ids"])

        prompt_len = inputs["input_ids"].shape[1]
        processors = LogitsProcessorList()
        if presence_penalty:
            processors.append(PresencePenalty(presence_penalty, prompt_len))

        torch.manual_seed(seed)
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else None,
            top_p=top_p if temperature > 0 else None,
            top_k=top_k if temperature > 0 else None,
            logits_processor=processors,
            pad_token_id=processor.tokenizer.eos_token_id,
        )
        
        text = processor.tokenizer.decode(out[0, prompt_len:], skip_special_tokens=True)
        thinking, answer = split_thinking(text)
        
        parsed = parse_answer(answer, task)
        
        return (parsed["positive_prompt"], parsed["wh_ratio"], parsed["ratio_follow"], thinking)

NODE_CLASS_MAPPINGS = {
    "Qwen2_1_PE_Loader": Qwen2_1_PE_Loader,
    "Qwen2_1_PE_Rewrite": Qwen2_1_PE_Rewrite
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen2_1_PE_Loader": "Qwen 2.1 Prompt Enhancer Loader",
    "Qwen2_1_PE_Rewrite": "Qwen 2.1 Prompt Enhancer Rewrite"
}
