# -*- coding: utf-8 -*-
"""
LLM 异步并发调用模块 - asyncio + aiohttp 实现

特性：
- 协程级高并发（单线程数千并发）
- 连接池复用（TCPConnector limit=100, per_host=10）
- 自适应限流（令牌桶算法，默认 10 req/s）
- 智能重试（指数退避 + 抖动，429读取Retry-After）
- 进度追踪（实时回调）
- 失败隔离（单个任务失败不影响其他任务）
- 同步兼容层（asyncio.run 包装）

API 兼容原系统 llm_generate.py：
- call_llm_async(prompt, system, **kwargs) -> Dict
- batch_call_llm(tasks, max_concurrency=20, **kwargs) -> List[Dict]
- call_llm_sync(prompt, system, **kwargs) -> Dict
- batch_call_llm_sync(tasks, **kwargs) -> List[Dict]
"""

import asyncio
import json
import os
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout, TCPConnector


# ─── 默认配置（与原系统保持一致）───────────────────────────

DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.7

DEFAULT_CONNECT_TIMEOUT = 30
DEFAULT_READ_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 2.0

DEFAULT_MAX_CONCURRENCY = 20
DEFAULT_RATE_LIMIT_RPS = 10.0
DEFAULT_PER_HOST_LIMIT = 10


# ─── 全局连接池（单例）─────────────────────────────────────

class _GlobalSession:
    """全局 aiohttp ClientSession 管理器（内部使用）"""

    _session: Optional[aiohttp.ClientSession] = None
    _connector: Optional[TCPConnector] = None
    _lock = asyncio.Lock()
    _ref_count = 0

    @classmethod
    async def get(
        cls,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: int = DEFAULT_READ_TIMEOUT,
        per_host_limit: int = DEFAULT_PER_HOST_LIMIT,
    ) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            async with cls._lock:
                if cls._session is None or cls._session.closed:
                    cls._connector = TCPConnector(
                        limit=100,
                        limit_per_host=per_host_limit,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        enable_cleanup_closed=True,
                        force_close=False,
                    )
                    timeout = ClientTimeout(
                        connect=connect_timeout,
                        sock_read=read_timeout,
                        total=connect_timeout + read_timeout + 30,
                    )
                    cls._session = aiohttp.ClientSession(
                        connector=cls._connector,
                        timeout=timeout,
                        headers={
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://roundtable-insight.local",
                            "X-Title": "Roundtable Insight Generator",
                        },
                    )
        cls._ref_count += 1
        return cls._session

    @classmethod
    async def release(cls):
        cls._ref_count = max(0, cls._ref_count - 1)
        if cls._ref_count == 0 and cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
            cls._connector = None

    @classmethod
    async def close(cls):
        if cls._session and not cls._session.closed:
            await cls._session.close()
        cls._session = None
        cls._connector = None
        cls._ref_count = 0


# ─── 令牌桶限流器 ──────────────────────────────────────────

class TokenBucket:
    """异步令牌桶限流器"""

    def __init__(self, rate: float, capacity: Optional[float] = None):
        self.rate = max(rate, 0.001)
        self.capacity = capacity or rate
        self.tokens = self.capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0):
        """获取指定数量的令牌，不足时等待"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < tokens:
                need = tokens - self.tokens
                wait_time = need / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.monotonic()
            else:
                self.tokens -= tokens


# ─── JSON 解析（与原系统一致）──────────────────────────────

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


# ─── 错误判断与重试延迟（与原系统一致）─────────────────────

def _is_retryable_status(status: int) -> bool:
    """判断 HTTP 状态码是否可重试"""
    return status in (429, 500, 502, 503, 504)


def _is_retryable_exception(exc: Exception) -> bool:
    """判断异常是否可重试"""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return True
    if isinstance(exc, aiohttp.ClientConnectionError):
        return True
    if isinstance(exc, aiohttp.ClientResponseError):
        return _is_retryable_status(exc.status)
    return False


def _get_retry_delay(
    attempt: int,
    base_delay: float,
    status: Optional[int] = None,
    retry_after: Optional[str] = None,
) -> float:
    """计算重试延迟（指数退避 + 抖动），兼容原系统逻辑"""
    if status == 429 and retry_after:
        try:
            return float(retry_after) + random.uniform(0.5, 2.0)
        except (ValueError, TypeError):
            pass
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, delay * 0.3)
    return min(delay + jitter, 60.0)


# ─── 核心异步调用（API 兼容原系统）──────────────────────────

async def call_llm_async(
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
    rate_limit_rps: float = 10.0,
    response_format: Dict = None,
    progress_callback: Callable = None,
    **kwargs,
) -> Dict:
    """
    异步调用 LLM API，返回与原系统 call_llm 完全相同的 Dict 结构。

    Returns:
        {
            "success": bool,
            "content": str,
            "json": dict|None,
            "usage": dict,
            "error": str|None,
            "attempts": int,
            "elapsed": float,
        }
    """
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    api_url = api_url or DEFAULT_API_URL
    model = model or DEFAULT_MODEL
    max_tokens = max_tokens or DEFAULT_MAX_TOKENS
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
    connect_timeout = connect_timeout or DEFAULT_CONNECT_TIMEOUT
    read_timeout = read_timeout or DEFAULT_READ_TIMEOUT
    max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
    retry_base_delay = retry_base_delay if retry_base_delay is not None else DEFAULT_RETRY_BASE_DELAY

    if not api_key:
        return {
            "success": False,
            "content": "",
            "json": None,
            "usage": {},
            "error": "缺少 OPENROUTER_API_KEY 环境变量",
            "attempts": 0,
            "elapsed": 0.0,
        }

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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    session = await _GlobalSession.get(connect_timeout, read_timeout)
    last_error = None
    start_time = time.time()

    try:
        for attempt in range(max_retries + 1):
            if progress_callback and attempt > 0:
                progress_callback(attempt, max_retries + 1, f"重试第 {attempt} 次...")

            try:
                async with session.post(api_url, json=body, headers=headers) as resp:
                    raw = await resp.text()

                    if resp.status != 200:
                        if _is_retryable_status(resp.status) and attempt < max_retries:
                            delay = _get_retry_delay(
                                attempt,
                                retry_base_delay,
                                status=resp.status,
                                retry_after=resp.headers.get("Retry-After"),
                            )
                            if progress_callback:
                                progress_callback(
                                    attempt + 1,
                                    max_retries + 1,
                                    f"重试等待 {delay:.1f}s... (HTTP {resp.status})",
                                )
                            await asyncio.sleep(delay)
                            continue

                        error_msg = f"HTTP {resp.status}: {raw[:500]}"
                        return {
                            "success": False,
                            "content": "",
                            "json": None,
                            "usage": {},
                            "error": error_msg,
                            "attempts": attempt + 1,
                            "elapsed": time.time() - start_time,
                        }

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

            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt >= max_retries:
                    break

                delay = _get_retry_delay(attempt, retry_base_delay)
                if progress_callback:
                    progress_callback(
                        attempt + 1,
                        max_retries + 1,
                        f"重试等待 {delay:.1f}s... ({type(e).__name__})",
                    )
                await asyncio.sleep(delay)

            except json.JSONDecodeError as e:
                last_error = e
                break

            except aiohttp.ClientResponseError as e:
                last_error = e
                if not _is_retryable_exception(e) or attempt >= max_retries:
                    break
                delay = _get_retry_delay(attempt, retry_base_delay, status=e.status)
                if progress_callback:
                    progress_callback(
                        attempt + 1,
                        max_retries + 1,
                        f"重试等待 {delay:.1f}s... ({type(e).__name__})",
                    )
                await asyncio.sleep(delay)

        error_msg = str(last_error)
        if isinstance(last_error, aiohttp.ClientResponseError):
            error_msg = f"HTTP {last_error.status}: {last_error.message[:500]}"

        return {
            "success": False,
            "content": "",
            "json": None,
            "usage": {},
            "error": error_msg,
            "attempts": max_retries + 1,
            "elapsed": time.time() - start_time,
        }

    finally:
        await _GlobalSession.release()


# ─── 批量并发调用（API 兼容原系统）──────────────────────────

async def batch_call_llm(
    tasks: List[Dict],
    *,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS,
    progress_callback: Callable = None,
    **default_kwargs,
) -> List[Dict]:
    """
    批量异步调用 LLM，带并发控制和速率限制。

    Args:
        tasks: [{"prompt": str, "system": str, **kwargs}, ...]
        max_concurrency: 最大并发数（asyncio.Semaphore）
        rate_limit_rps: 每秒请求数限制（TokenBucket）
        progress_callback: 进度回调 callback(completed, total, message)
        **default_kwargs: 默认 LLM 调用参数

    Returns:
        与原系统 generate_with_progress 相同的 Dict 列表
    """
    if not tasks:
        return []

    total = len(tasks)
    completed = 0
    results: List[Optional[Dict]] = [None] * total
    semaphore = asyncio.Semaphore(max_concurrency)
    rate_limiter = TokenBucket(rate_limit_rps)

    async def _execute_one(index: int, task: Dict):
        nonlocal completed
        async with semaphore:
            await rate_limiter.acquire()

            prompt = task["prompt"]
            system = task.get("system", "")
            merged = {**default_kwargs, **{k: v for k, v in task.items() if k not in ("prompt", "system")}}

            def _inner_progress(step, total_steps, message):
                if progress_callback:
                    progress_callback(completed, total, message)

            result = await call_llm_async(
                prompt,
                system,
                progress_callback=_inner_progress,
                **merged,
            )

            results[index] = result
            completed += 1
            if progress_callback:
                progress_callback(completed, total, f"完成 {completed}/{total}")

    await asyncio.gather(*[_execute_one(i, task) for i, task in enumerate(tasks)])
    return results


# ─── 同步兼容层 ────────────────────────────────────────────

def call_llm_sync(
    prompt: str,
    system: str = "",
    **kwargs,
) -> Dict:
    """
    同步调用 LLM（内部使用 asyncio.run 包装异步调用）。
    API 与原系统 call_llm 完全一致。
    """
    return asyncio.run(call_llm_async(prompt, system, **kwargs))


def batch_call_llm_sync(
    tasks: List[Dict],
    **kwargs,
) -> List[Dict]:
    """
    同步批量调用 LLM（内部使用 asyncio.run 包装异步调用）。
    API 与原系统 generate_with_progress 的批量模式一致。
    """
    return asyncio.run(batch_call_llm(tasks, **kwargs))


# ─── JSON 强制模式（兼容原系统 call_llm_json）───────────────

async def call_llm_json_async(
    prompt: str,
    system: str = "",
    **kwargs,
) -> Dict:
    """
    异步调用 LLM 并强制返回 JSON 解析结果。
    兼容原系统 call_llm_json。
    """
    kwargs.setdefault("response_format", {"type": "json_object"})
    result = await call_llm_async(prompt, system, **kwargs)

    if not result["success"]:
        return {**result, "data": None}

    if result["json"] is not None:
        return {**result, "data": result["json"]}

    return {
        **result,
        "data": None,
        "error": f"JSON 解析失败: {result['content'][:200]}",
    }


def call_llm_json_sync(
    prompt: str,
    system: str = "",
    **kwargs,
) -> Dict:
    """同步包装器：调用 LLM 并强制返回 JSON"""
    kwargs.setdefault("response_format", {"type": "json_object"})
    return asyncio.run(call_llm_json_async(prompt, system, **kwargs))


# ─── 进度追踪器（兼容原系统 ProgressTracker）───────────────

class ProgressTracker:
    """进度追踪器 - 用于显示 LLM 调用进度（与原系统兼容）"""

    def __init__(self, total_steps: int, desc: str = ""):
        self.total = total_steps
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
        self._last_line = ""

    def update(self, step: int = None, message: str = ""):
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
        def callback(step, total, message):
            self.update(message=message)
        return callback


# ─── 带进度条的批量调用（兼容原系统 generate_with_progress）─

async def generate_with_progress_async(
    tasks: List[Dict],
    desc: str = "生成中",
    **default_kwargs,
) -> List[Dict]:
    """
    批量调用 LLM 并显示进度（异步版本）。
    兼容原系统 generate_with_progress。
    """
    tracker = ProgressTracker(len(tasks), desc)
    tracker.update(0, "启动中...")

    def progress_callback(completed, total, message):
        tracker.update(completed, message)

    results = await batch_call_llm(
        tasks,
        progress_callback=progress_callback,
        **default_kwargs,
    )

    success_count = sum(1 for r in results if r["success"])
    tracker.finish(f"完成 {success_count}/{len(tasks)} 成功")
    return results


def generate_with_progress(
    tasks: List[Dict],
    desc: str = "生成中",
    **default_kwargs,
) -> List[Dict]:
    """
    批量调用 LLM 并显示进度（同步版本，与原系统完全兼容）。
    """
    return asyncio.run(generate_with_progress_async(tasks, desc, **default_kwargs))


# ─── 连接池管理 ────────────────────────────────────────────

async def close_all_connections():
    """关闭所有连接池连接（应在程序退出时调用）"""
    await _GlobalSession.close()


# ─── 测试代码 ──────────────────────────────────────────────

async def _test_single_async():
    """测试单任务异步调用"""
    print("=" * 60)
    print("测试 1: 单任务异步调用 call_llm_async")
    print("=" * 60)

    result = await call_llm_async(
        "请用一句话解释什么是异步编程。",
        "你是一个简洁的技术专家。",
        rate_limit_rps=5.0,
    )

    print(f"success: {result['success']}")
    print(f"attempts: {result['attempts']}")
    print(f"elapsed: {result['elapsed']:.2f}s")
    if result['success']:
        print(f"content: {result['content'][:100]}...")
    else:
        print(f"error: {result['error']}")
    print()


async def _test_batch_async():
    """测试批量异步调用"""
    print("=" * 60)
    print("测试 2: 批量异步调用 batch_call_llm")
    print("=" * 60)

    tasks = [
        {
            "prompt": f"请用一句话回答：什么是并发编程？（任务 {i+1}）",
            "system": "你是一个简洁的助手。",
        }
        for i in range(5)
    ]

    start = time.time()
    results = await batch_call_llm(
        tasks,
        max_concurrency=5,
        rate_limit_rps=5.0,
    )
    elapsed = time.time() - start

    print(f"总耗时: {elapsed:.1f}s")
    print(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")
    for i, r in enumerate(results):
        status = "✓" if r["success"] else "✗"
        content = r["content"][:50] if r["success"] else r["error"]
        print(f"  {status} 任务 {i+1}: {content}")
    print()


async def _test_batch_with_progress():
    """测试带进度条的批量调用"""
    print("=" * 60)
    print("测试 3: 带进度条的批量调用 generate_with_progress_async")
    print("=" * 60)

    tasks = [
        {
            "prompt": f"请用一句话回答：什么是Python？（任务 {i+1}）",
            "system": "你是一个简洁的助手。",
        }
        for i in range(5)
    ]

    start = time.time()
    results = await generate_with_progress_async(
        tasks,
        desc="测试并发",
        max_concurrency=5,
        rate_limit_rps=5.0,
    )
    elapsed = time.time() - start

    print(f"\n总耗时: {elapsed:.1f}s")
    print(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")
    print()


def _test_sync_wrapper():
    """测试同步包装器"""
    print("=" * 60)
    print("测试 4: 同步包装器 call_llm_sync")
    print("=" * 60)

    result = call_llm_sync(
        "请用一句话解释什么是同步调用。",
        "你是一个简洁的技术专家。",
        rate_limit_rps=5.0,
    )

    print(f"success: {result['success']}")
    print(f"elapsed: {result['elapsed']:.2f}s")
    if result['success']:
        print(f"content: {result['content'][:100]}...")
    else:
        print(f"error: {result['error']}")
    print()


async def _test_rate_limit():
    """测试速率限制"""
    print("=" * 60)
    print("测试 5: 令牌桶速率限制")
    print("=" * 60)

    bucket = TokenBucket(rate=5.0, capacity=5.0)

    start = time.time()
    for i in range(10):
        await bucket.acquire()
        print(f"  请求 {i+1} 通过，时间: {time.time() - start:.2f}s")
    elapsed = time.time() - start

    print(f"10 个请求在 {elapsed:.1f}s 内完成（限制 5 req/s）")
    print(f"理论最小时间: {(10 - 5) / 5:.1f}s")
    print()


async def _test_json_mode():
    """测试 JSON 强制模式"""
    print("=" * 60)
    print("测试 6: JSON 强制模式 call_llm_json_async")
    print("=" * 60)

    result = await call_llm_json_async(
        '请返回一个 JSON 对象，格式为 {"answer": "异步编程的定义"}',
        "你是一个JSON生成器。",
        rate_limit_rps=5.0,
    )

    print(f"success: {result['success']}")
    print(f"data: {result.get('data')}")
    print(f"error: {result.get('error')}")
    print()


async def _run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LLM 异步调用引擎测试")
    print("=" * 60 + "\n")

    await _test_single_async()
    await _test_batch_async()
    await _test_batch_with_progress()
    _test_sync_wrapper()
    await _test_rate_limit()
    await _test_json_mode()

    await close_all_connections()

    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(_run_all_tests())
    elif len(sys.argv) < 2:
        print("用法:")
        print("  python llm_generate_async.py --test       运行全部测试")
        print("  python llm_generate_async.py <prompt>     单条同步调用")
        sys.exit(1)
    else:
        prompt = sys.argv[1]
        system = sys.argv[2] if len(sys.argv) > 2 else ""

        print(f"模型: {DEFAULT_MODEL}")
        print(f"超时: 连接 {DEFAULT_CONNECT_TIMEOUT}s / 读取 {DEFAULT_READ_TIMEOUT}s")
        print(f"重试: 最多 {DEFAULT_MAX_RETRIES} 次, 基础延迟 {DEFAULT_RETRY_BASE_DELAY}s")
        print()

        result = call_llm_sync(prompt, system)

        if result["success"]:
            print(f"成功 (尝试 {result['attempts']} 次, {result['elapsed']:.1f}s)")
            print(f"Token: {result['usage']}")
            print(f"输出:\n{result['content'][:500]}")
            if result["json"]:
                print(f"\nJSON: {json.dumps(result['json'], ensure_ascii=False, indent=2)[:500]}")
        else:
            print(f"失败: {result['error']}")
            sys.exit(1)
