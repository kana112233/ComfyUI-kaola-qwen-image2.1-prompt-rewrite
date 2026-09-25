import json

# Profile configurations matching pe_core.py
PROFILES = {
    "t2i": {
        "name": "t2i",
        "takes_images": False,
        "has_ratio_follow": False,
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "max_new_tokens": 16256,
        "image_max_pixels": 1024 * 1024
    },
    "edit": {
        "name": "edit",
        "takes_images": True,
        "has_ratio_follow": True,
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "max_new_tokens": 24000,
        "image_max_pixels": 1024 * 1024
    },
    "caption": {
        "name": "caption",
        "takes_images": True,
        "has_ratio_follow": False,
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "max_new_tokens": 16256,
        "image_max_pixels": 1024 * 1024
    }
}

def split_thinking(text: str) -> tuple[str, str]:
    if "</think>" in text:
        think, _, answer = text.partition("</think>")
        if "<think>" in think:
            think = think.partition("<think>")[2]
        return think.strip(), answer.strip()
    if "<think>" in text:
        return text.partition("<think>")[2].strip(), ""
    return "", text.strip()

def _balanced_spans(answer: str) -> list[str]:
    spans = []
    depth = 0
    start = -1
    in_str = False
    escaped = False
    for i, ch in enumerate(answer):
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                spans.append(answer[start:i + 1])
    return spans

def _as_obj(candidate: str):
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            import json_repair
            obj = json_repair.repair_json(candidate, return_objects=True)
            if isinstance(obj, list):
                obj = obj[0] if obj else None
        except ImportError:
            return None
    return obj if isinstance(obj, dict) else None

def parse_answer(answer: str, task: str) -> dict:
    profile = PROFILES[task]
    answer = (answer or "").strip()
    candidates = list(reversed(_balanced_spans(answer)))
    for candidate in candidates:
        obj = _as_obj(candidate)
        if obj is None:
            continue
        rewritten = obj.get("rewritten_prompt") or obj.get("rewrited_prompt")
        if not isinstance(rewritten, str) or not rewritten.strip():
            continue
        return {
            "positive_prompt": rewritten.strip(),
            "wh_ratio": str(obj.get("wh_ratio") or "").strip(),
            "ratio_follow": str(obj.get("ratio_follow") or "").strip() if profile["has_ratio_follow"] else "",
            "parse_ok": True,
        }
    return {"positive_prompt": answer, "wh_ratio": "", "ratio_follow": "", "parse_ok": False}
