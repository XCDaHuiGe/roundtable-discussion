# -*- coding: utf-8 -*-
"""llm_generate_async.py 本地单元测试（无需 API Key）"""

import asyncio
import json
from engine.llm_generate_async import (
    TokenBucket,
    _extract_json,
    _get_retry_delay,
    _is_retryable_status,
    _is_retryable_exception,
    ProgressTracker,
    call_llm_async,
    batch_call_llm,
)


async def test_token_bucket():
    """测试令牌桶限流器"""
    print("测试: TokenBucket 速率限制")
    bucket = TokenBucket(rate=10.0, capacity=10.0)
    start = asyncio.get_event_loop().time()
    for i in range(15):
        await bucket.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    print(f"  15个请求耗时 {elapsed:.2f}s (限制10req/s, 理论最小0.5s)")
    assert elapsed >= 0.4, "速率限制未生效"
    print("  ✓ 通过")


def test_extract_json():
    """测试 JSON 解析"""
    print("测试: _extract_json JSON解析")

    # 纯 JSON
    assert _extract_json('{"key": "value"}') == {"key": "value"}

    # markdown 代码块
    text = "```json\n{\"key\": \"value\"}\n```"
    assert _extract_json(text) == {"key": "value"}

    # 无标记代码块
    text = "```\n{\"a\": 1}\n```"
    assert _extract_json(text) == {"a": 1}

    # 嵌套在文本中
    text = "some text {\"nested\": true} more"
    assert _extract_json(text) == {"nested": True}

    print("  ✓ 通过")


def test_retry_delay():
    """测试重试延迟计算"""
    print("测试: _get_retry_delay 重试延迟")

    # 普通指数退避
    d0 = _get_retry_delay(0, 2.0)
    assert 2.0 <= d0 <= 2.6

    d1 = _get_retry_delay(1, 2.0)
    assert 4.0 <= d1 <= 5.2

    # 429 + Retry-After
    d429 = _get_retry_delay(0, 2.0, status=429, retry_after="5")
    assert d429 >= 5.0
    print(f"  429延迟: {d429:.2f}s")

    # 上限60s
    d_big = _get_retry_delay(10, 2.0)
    assert d_big <= 60.0

    print("  ✓ 通过")


def test_is_retryable():
    """测试错误可重试判断"""
    print("测试: 可重试状态码/异常判断")

    assert _is_retryable_status(429) is True
    assert _is_retryable_status(500) is True
    assert _is_retryable_status(502) is True
    assert _is_retryable_status(503) is True
    assert _is_retryable_status(504) is True
    assert _is_retryable_status(400) is False
    assert _is_retryable_status(404) is False

    import aiohttp
    assert _is_retryable_exception(asyncio.TimeoutError()) is True
    assert _is_retryable_exception(aiohttp.ClientConnectionError()) is True

    print("  ✓ 通过")


def test_progress_tracker():
    """测试进度追踪器"""
    print("测试: ProgressTracker")

    tracker = ProgressTracker(total_steps=10, desc="测试")
    tracker.update(1, "msg")
    assert tracker.current == 1
    tracker.update(message="msg2")
    assert tracker.current == 2
    tracker.finish("done")
    print("  ✓ 通过")


async def test_no_api_key():
    """测试无 API Key 时的错误处理"""
    print("测试: 无 API Key 错误处理")

    import os
    old_key = os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        result = await call_llm_async("test", "")
        assert result["success"] is False
        assert "缺少" in result["error"] or "OPENROUTER_API_KEY" in result["error"]
        assert result["attempts"] == 0
        print("  ✓ 通过")
    finally:
        if old_key:
            os.environ["OPENROUTER_API_KEY"] = old_key


async def test_batch_empty():
    """测试空任务列表"""
    print("测试: 空任务列表")

    results = await batch_call_llm([])
    assert results == []
    print("  ✓ 通过")


async def run_all_tests():
    print("=" * 50)
    print("llm_generate_async.py 本地单元测试")
    print("=" * 50 + "\n")

    await test_token_bucket()
    test_extract_json()
    test_retry_delay()
    test_is_retryable()
    test_progress_tracker()
    await test_no_api_key()
    await test_batch_empty()

    print("\n" + "=" * 50)
    print("所有测试通过!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
