# -*- coding: utf-8 -*-
"""
LLM 调用模块 - 带超时、重试、进度追踪

特性：
- 指数退避重试（含抖动）
- 可配置超时（连接/读取分离）
- 请求间隔控制（避免频率限制）
- 结构化 JSON 解析
- 进度回调支持
"""

import json
import os
import re
import time
import random
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Callable


# ─── 默认配置 ──────────────────────────────────────────────

DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.7

DEFAULT_CONNECT_TIMEOUT = 30
DEFAULT_READ_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 2.0
DEFAULT_REQUEST_INTERVAL = 1.0


# ─── 超时控制 ──────────────────────────────────────────────

class TimeoutHTTPHandler(urllib.request.HTTPSHandler):
    """支持分离连接/读取超时的 HTTPS Handler"""

    def __init__(self, connect_timeout: int = 30, read_timeout: int = 120):
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        super().__init__()

    def https_open(self, req):
        return self.do_open(self._get_connection, req)

    def _get_connection(self, host, timeout=None, **kwargs):
        import http.client
        return http.client.HTTPSConnection(
            host,
            timeout=(self._connect_timeout, self._read_timeout),
            **kwargs
        )


def create_opener(connect_timeout: int = 30, read_timeout: int = 120):
    """创建带超时控制的 URL opener"""
    handler = TimeoutHTTPHandler(connect_timeout, read_timeout)
    return urllib.request.build_opener(handler)


# ─── 重试逻辑 ──────────────────────────────────────────────

def _is_retryable_error(error: Exception) -> bool:
    """判断错误是否可重试"""
    if isinstance(error, urllib.error.HTTPError):
        return error.code in (429, 500, 502, 503, 504)
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return True
    if isinstance(error, urllib.error.URLError):
        if isinstance(error.reason, TimeoutError):
            return True
        if isinstance(error.reason, ConnectionError):
            return True
    return False


def _get_retry_delay(attempt: int, base_delay: float, error: Exception = None) -> float:
    """计算重试延迟（指数退避 + 抖动）"""
    if isinstance(error, urllib.error.HTTPError) and error.code == 429:
        retry_after = error.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after) + random.uniform(0.5, 2.0)
            except (ValueError, TypeError):
                pass
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, delay * 0.3)
    return min(delay + jitter, 60.0)


# ─── JSON 解析 ──────────────────────────────────────────────

def _extract_json(text: str) -> Optional[Dict]:
    """从 LLM 输出中提取 JSON（容错多种格式）"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'(\{[\s\S]*\})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    return None


# ─── 核心调用函数 ──────────────────────────────────────────

def call_llm(
    prompt: str,
    system: str = "",
    *,
    api_key: str = None,
    api_url: str = None,
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
    connect_timeout: int = None,
    read_timeout: int = None,
    max_retries: int = None,
    retry_base_delay: float = None,
    request_interval: float = None,
    response_format: Dict = None,
    progress_callback: Callable = None,
) -> Dict:
    """
    调用 LLM API 并返回结构化响应。

    Args:
        prompt: 用户提示词
        system: 系统提示词（可选）
        api_key: API 密钥（默认从 OPENROUTER_API_KEY 环境变量读取）
        api_url: API 端点
        model: 模型名称
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        connect_timeout: 连接超时（秒）
        read_timeout: 读取超时（秒）
        max_retries: 最大重试次数
        retry_base_delay: 重试基础延迟（秒）
        request_interval: 请求间隔（秒，避免频率限制）
        response_format: 响应格式（如 {"type": "json_object"}）
        progress_callback: 进度回调函数 callback(step, total, message)

    Returns:
        {
            "success": bool,
            "content": str,       # 原始文本输出
            "json": dict|None,    # 解析后的 JSON（如果可解析）
            "usage": dict,        # token 使用统计
            "error": str|None,    # 错误信息
            "attempts": int,      # 尝试次数
            "elapsed": float,     # 总耗时（秒）
        }
    """
    # 参数默认值
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    api_url = api_url or DEFAULT_API_URL
    model = model or DEFAULT_MODEL
    max_tokens = max_tokens or DEFAULT_MAX_TOKENS
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
    connect_timeout = connect_timeout or DEFAULT_CONNECT_TIMEOUT
    read_timeout = read_timeout or DEFAULT_READ_TIMEOUT
    max_retries = max_retries or DEFAULT_MAX_RETRIES
    retry_base_delay = retry_base_delay or DEFAULT_RETRY_BASE_DELAY
    request_interval = request_interval or DEFAULT_REQUEST_INTERVAL

    if not api_key:
        return {
            "success": False, "content": "", "json": None,
            "usage": {}, "error": "缺少 OPENROUTER_API_KEY 环境变量",
            "attempts": 0, "elapsed": 0.0,
        }

    opener = create_opener(connect_timeout, read_timeout)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        body["response_format"] = response_format

    data = json.dumps(body).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://roundtable-insight.local",
        "X-Title": "Roundtable Insight Generator",
    }

    last_error = None
    start_time = time.time()

    for attempt in range(max_retries + 1):
        if progress_callback and attempt > 0:
            progress_callback(attempt, max_retries + 1, f"重试第 {attempt} 次...")

        try:
            req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
            with opener.open(req) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)

                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})

                return {
                    "success": True,
                    "content": content,
                    "json": _extract_json(content),
                    "usage": usage,
                    "error": None,
                    "attempts": attempt + 1,
                    "elapsed": time.time() - start_time,
                }

        except Exception as e:
            last_error = e
            if not _is_retryable_error(e) or attempt >= max_retries:
                break

            delay = _get_retry_delay(attempt, retry_base_delay, e)
            if progress_callback:
                progress_callback(attempt + 1, max_retries + 1,
                                  f"重试等待 {delay:.1f}s... ({type(e).__name__})")
            time.sleep(delay)

        finally:
            if request_interval > 0 and attempt < max_retries:
                time.sleep(request_interval)

    error_msg = str(last_error)
    if isinstance(last_error, urllib.error.HTTPError):
        error_msg = f"HTTP {last_error.code}: {last_error.reason}"
        try:
            error_body = last_error.read().decode("utf-8")[:500]
            error_msg += f" | {error_body}"
        except Exception:
            pass

    return {
        "success": False, "content": "", "json": None,
        "usage": {}, "error": error_msg,
        "attempts": max_retries + 1,
        "elapsed": time.time() - start_time,
    }


def call_llm_json(
    prompt: str,
    system: str = "",
    **kwargs,
) -> Dict:
    """
    调用 LLM 并强制返回 JSON 解析结果。

    Returns:
        {"success": bool, "data": dict|None, "error": str|None, ...}
    """
    kwargs.setdefault("response_format", {"type": "json_object"})
    result = call_llm(prompt, system, **kwargs)

    if not result["success"]:
        return {**result, "data": None}

    if result["json"] is not None:
        return {**result, "data": result["json"]}

    return {
        **result,
        "data": None,
        "error": f"JSON 解析失败: {result['content'][:200]}",
    }


# ─── 进度追踪 ──────────────────────────────────────────────

class ProgressTracker:
    """进度追踪器 - 用于显示 LLM 调用进度"""

    def __init__(self, total_steps: int, desc: str = ""):
        self.total = total_steps
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
        self._last_line = ""

    def update(self, step: int = None, message: str = ""):
        """更新进度"""
        if step is not None:
            self.current = step
        else:
            self.current += 1

        elapsed = time.time() - self.start_time
        pct = (self.current / self.total) * 100 if self.total > 0 else 0
        eta = (elapsed / self.current * (self.total - self.current)) if self.current > 0 else 0

        line = f"\r[{self.current}/{self.total}] {pct:5.1f}%"
        if self.desc:
            line += f" | {self.desc}"
        if message:
            line += f" | {message}"
        line += f" | {elapsed:.0f}s"
        if eta > 0:
            line += f" | ETA {eta:.0f}s"

        print(line.ljust(len(self._last_line) + 2), end="", flush=True)
        self._last_line = line

    def finish(self, message: str = ""):
        """完成进度"""
        elapsed = time.time() - self.start_time
        msg = f"\r[{self.total}/{self.total}] 100.0%"
        if self.desc:
            msg += f" | {self.desc}"
        if message:
            msg += f" | {message}"
        msg += f" | {elapsed:.1f}s"
        print(msg.ljust(len(self._last_line) + 2))
        self._last_line = ""

    def make_callback(self) -> Callable:
        """创建 LLM 调用进度回调"""
        def callback(step, total, message):
            self.update(message=message)
        return callback


# ─── 便捷函数 ──────────────────────────────────────────────

def generate_with_progress(
    tasks: List[Dict],
    desc: str = "生成中",
    **default_kwargs,
) -> List[Dict]:
    """
    批量调用 LLM 并显示进度。

    Args:
        tasks: [{"prompt": str, "system": str, **kwargs}, ...]
        desc: 进度描述
        **default_kwargs: 默认 LLM 调用参数

    Returns:
        [{"success": bool, "content": str, "json": dict, ...}, ...]
    """
    tracker = ProgressTracker(len(tasks), desc)
    results = []

    for i, task in enumerate(tasks):
        tracker.update(i + 1, f"调用 LLM ({i+1}/{len(tasks)})")

        merged = {**default_kwargs, **task}
        prompt = merged.pop("prompt")
        system = merged.pop("system", "")

        result = call_llm(prompt, system, **merged)
        results.append(result)

        if not result["success"]:
            print(f"\n  [WARN] 任务 {i+1} 失败: {result['error'][:100]}")

    tracker.finish(f"完成 {sum(1 for r in results if r['success'])}/{len(results)} 成功")
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python llm_generate.py <prompt>")
        print("示例: python llm_generate.py '你好，请用JSON格式返回 {\"msg\": \"hello\"}'")
        sys.exit(1)

    prompt = sys.argv[1]
    system = sys.argv[2] if len(sys.argv) > 2 else ""

    print(f"模型: {DEFAULT_MODEL}")
    print(f"超时: 连接 {DEFAULT_CONNECT_TIMEOUT}s / 读取 {DEFAULT_READ_TIMEOUT}s")
    print(f"重试: 最多 {DEFAULT_MAX_RETRIES} 次, 基础延迟 {DEFAULT_RETRY_BASE_DELAY}s")
    print()

    result = call_llm(prompt, system)

    if result["success"]:
        print(f"成功 (尝试 {result['attempts']} 次, {result['elapsed']:.1f}s)")
        print(f"Token: {result['usage']}")
        print(f"输出:\n{result['content'][:500]}")
        if result["json"]:
            print(f"\nJSON: {json.dumps(result['json'], ensure_ascii=False, indent=2)[:500]}")
    else:
        print(f"失败: {result['error']}")
        sys.exit(1)
