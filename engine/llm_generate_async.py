# -*- coding: utf-8 -*-
"""异步 LLM 调用模块。

为本地测试和并发 benchmark 提供 asyncio + aiohttp 版本。
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Any

import aiohttp


DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.7
DEFAULT_CONNECT_TIMEOUT = 30
DEFAULT_READ_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 2.0


@dataclass
class LLMTask:
    prompt: str
    system: str = ""
    task_id: str | None = None
    kwargs: dict[str, Any] | None = None


@dataclass
class LLMResult:
    success: bool
    content: str = ""
    json: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    elapsed: float = 0.0
    task_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "json": self.json,
            "usage": self.usage or {},
            "error": self.error,
            "attempts": self.attempts,
            "elapsed": self.elapsed,
            "task_id": self.task_id,
        }


class TokenBucket:
    """简单异步令牌桶限流器。"""

    def __init__(self, rate: float, capacity: float):
        self.rate = float(rate)
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.updated_at = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait_time = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)


class ProgressTracker:
    """进度追踪器。"""

    def __init__(self, total_steps: int, desc: str = ""):
        self.total = total_steps
        self.current = 0
        self.desc = desc
        self.start_time = time.time()

    def update(self, step: int | None = None, message: str = "") -> None:
        if step is not None:
            self.current = step
        else:
            self.current += 1
        if message:
            print(f"[{self.current}/{self.total}] {self.desc} {message}".strip())

    def finish(self, message: str = "") -> None:
        self.current = self.total
        suffix = f" {message}" if message else ""
        print(f"[{self.total}/{self.total}] {self.desc}{suffix}".strip())


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"(\{[\s\S]*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    return None


def _is_retryable_status(status: int) -> bool:
    return status in (429, 500, 502, 503, 504)


def _is_retryable_exception(error: Exception) -> bool:
    return isinstance(
        error,
        (
            asyncio.TimeoutError,
            TimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientPayloadError,
            aiohttp.ServerDisconnectedError,
        ),
    )


def _get_retry_delay(
    attempt: int,
    base_delay: float,
    *,
    status: int | None = None,
    retry_after: str | None = None,
) -> float:
    if status == 429 and retry_after:
        try:
            return float(retry_after) + random.uniform(0.0, 0.6)
        except (TypeError, ValueError):
            pass
    delay = base_delay * (2**attempt)
    return min(delay + random.uniform(0.0, delay * 0.3), 60.0)


async def call_llm_async(
    prompt: str,
    system: str = "",
    *,
    api_key: str | None = None,
    api_url: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    connect_timeout: int | None = None,
    read_timeout: int | None = None,
    max_retries: int | None = None,
    retry_base_delay: float | None = None,
    task_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return LLMResult(
            success=False,
            error="缺少 OPENROUTER_API_KEY 环境变量",
            attempts=0,
            task_id=task_id,
        ).to_dict()

    api_url = api_url or DEFAULT_API_URL
    model = model or DEFAULT_MODEL
    max_tokens = max_tokens or DEFAULT_MAX_TOKENS
    temperature = DEFAULT_TEMPERATURE if temperature is None else temperature
    connect_timeout = connect_timeout or DEFAULT_CONNECT_TIMEOUT
    read_timeout = read_timeout or DEFAULT_READ_TIMEOUT
    max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
    retry_base_delay = retry_base_delay or DEFAULT_RETRY_BASE_DELAY

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
    body.update(extra)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://roundtable-insight.local",
        "X-Title": "Roundtable Insight Generator",
    }
    timeout = aiohttp.ClientTimeout(total=connect_timeout + read_timeout, connect=connect_timeout)
    start = time.time()
    last_error = None

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(max_retries + 1):
            try:
                async with session.post(api_url, json=body, headers=headers) as response:
                    raw = await response.text()
                    if response.status >= 400:
                        if _is_retryable_status(response.status) and attempt < max_retries:
                            delay = _get_retry_delay(
                                attempt,
                                retry_base_delay,
                                status=response.status,
                                retry_after=response.headers.get("Retry-After"),
                            )
                            await asyncio.sleep(delay)
                            continue
                        return LLMResult(
                            success=False,
                            error=f"HTTP {response.status}: {raw[:500]}",
                            attempts=attempt + 1,
                            elapsed=time.time() - start,
                            task_id=task_id,
                        ).to_dict()
                    result = json.loads(raw)
                    content = result["choices"][0]["message"]["content"]
                    return LLMResult(
                        success=True,
                        content=content,
                        json=_extract_json(content),
                        usage=result.get("usage", {}),
                        attempts=attempt + 1,
                        elapsed=time.time() - start,
                        task_id=task_id,
                    ).to_dict()
            except Exception as error:
                last_error = error
                if not _is_retryable_exception(error) or attempt >= max_retries:
                    break
                await asyncio.sleep(_get_retry_delay(attempt, retry_base_delay))

    return LLMResult(
        success=False,
        error=str(last_error),
        attempts=max_retries + 1,
        elapsed=time.time() - start,
        task_id=task_id,
    ).to_dict()


async def batch_call_llm(tasks: list[LLMTask | dict[str, Any]], **default_kwargs: Any) -> list[dict[str, Any]]:
    if not tasks:
        return []

    async def run_one(task: LLMTask | dict[str, Any]) -> dict[str, Any]:
        if isinstance(task, LLMTask):
            kwargs = {**default_kwargs, **(task.kwargs or {})}
            return await call_llm_async(task.prompt, task.system, task_id=task.task_id, **kwargs)
        merged = {**default_kwargs, **task}
        prompt = merged.pop("prompt")
        system = merged.pop("system", "")
        return await call_llm_async(prompt, system, **merged)

    return await asyncio.gather(*(run_one(task) for task in tasks))


async def batch_call_llm_with_progress(
    tasks: list[LLMTask],
    *,
    desc: str = "asyncio",
    max_concurrency: int = 5,
    rate_limit_rps: float = 2.0,
    **default_kwargs: Any,
) -> list[LLMResult]:
    if not tasks:
        return []
    tracker = ProgressTracker(len(tasks), desc)
    semaphore = asyncio.Semaphore(max_concurrency)
    bucket = TokenBucket(rate_limit_rps, rate_limit_rps)

    async def run_one(index: int, task: LLMTask) -> LLMResult:
        async with semaphore:
            await bucket.acquire()
            result = await call_llm_async(
                task.prompt,
                task.system,
                task_id=task.task_id,
                **{**default_kwargs, **(task.kwargs or {})},
            )
            tracker.update(index + 1, task.task_id or "")
            return LLMResult(**result)

    results = await asyncio.gather(*(run_one(i, task) for i, task in enumerate(tasks)))
    tracker.finish("done")
    return results


async def close_all_connections() -> None:
    """兼容 benchmark 的清理入口。当前实现每次调用独立 session，无全局连接。"""
    return None
