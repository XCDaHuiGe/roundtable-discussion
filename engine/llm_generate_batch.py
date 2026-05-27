# -*- coding: utf-8 -*-
"""
LLM 批量 API 调用模块 - OpenAI Batch API 兼容层

特性：
- 单请求提交多个任务（最高 50,000 条/批次）
- 异步后台处理，无需保持连接
- 成本降低 50%（OpenAI Batch API 定价）
- 适合超大规模批量任务

支持的 API：
- OpenAI Batch API（官方）
- OpenRouter（部分支持）
- 自托管 vLLM / TGI（批量推理）

用法：
    # 提交批量任务
    batch_id = await submit_batch(tasks)

    # 轮询结果
    results = await poll_batch_results(batch_id)

    # 或一次性提交+等待
    results = await batch_call_llm_batch_api(tasks)

与 asyncio 方案对比：
- 优点：成本最低、适合万级任务、无需维持长连接
- 缺点：延迟较高（分钟级）、不支持实时进度、API 兼容性差
- 适用：夜间跑批、成本敏感、超大规模生成
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

from engine.llm_generate_async import LLMTask, LLMResult, ConnectionPool, TokenBucket


# ─── 默认配置 ──────────────────────────────────────────────

DEFAULT_BATCH_API_URL = "https://api.openai.com/v1/batches"
DEFAULT_BATCH_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_BATCH_MODEL = "gpt-4o-mini"  # Batch API 通常需要特定模型

# 批量限制
MAX_BATCH_SIZE = 50000       # OpenAI 单批次最大请求数
MAX_BATCH_FILE_SIZE = 100 * 1024 * 1024  # 100MB
BATCH_POLL_INTERVAL = 30     # 轮询间隔（秒）
BATCH_MAX_WAIT_TIME = 3600   # 最大等待时间（秒）


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class BatchJob:
    """批量任务定义"""
    custom_id: str
    task: LLMTask
    method: str = "POST"
    url: str = "/v1/chat/completions"

    def to_api_format(self) -> Dict:
        """转换为 OpenAI Batch API 格式"""
        body = {
            "model": self.task.model or DEFAULT_BATCH_MODEL,
            "messages": [],
            "max_tokens": self.task.max_tokens or 4000,
            "temperature": self.task.temperature if self.task.temperature is not None else 0.7,
        }
        if self.task.system:
            body["messages"].append({"role": "system", "content": self.task.system})
        body["messages"].append({"role": "user", "content": self.task.prompt})
        if self.task.response_format:
            body["response_format"] = self.task.response_format

        return {
            "custom_id": self.custom_id,
            "method": self.method,
            "url": self.url,
            "body": body,
        }


@dataclass
class BatchResult:
    """批量任务结果"""
    batch_id: str
    status: str  # "validating", "in_progress", "completed", "failed"
    results: List[LLMResult] = field(default_factory=list)
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed: float = 0.0


# ─── 文件上传 ──────────────────────────────────────────────

async def _upload_batch_file(
    jobs: List[BatchJob],
    api_key: str,
    api_url: str = "https://api.openai.com/v1/files",
) -> str:
    """
    上传批量任务文件到 OpenAI。

    Returns:
        file_id: 上传后的文件 ID
    """
    # 构建 JSONL 内容
    lines = []
    for job in jobs:
        lines.append(json.dumps(job.to_api_format(), ensure_ascii=False))
    content = "\n".join(lines).encode("utf-8")

    if len(content) > MAX_BATCH_FILE_SIZE:
        raise ValueError(f"批量文件过大: {len(content)} bytes > {MAX_BATCH_FILE_SIZE}")

    pool = await ConnectionPool.get_instance()
    session = await pool.get_session()

    # 构建 multipart form-data
    data = aiohttp.FormData()
    data.add_field("purpose", "batch")
    data.add_field("file", content, filename="batch.jsonl", content_type="application/jsonl")

    headers = {"Authorization": f"Bearer {api_key}"}

    async with session.post(api_url, data=data, headers=headers) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise RuntimeError(f"文件上传失败: HTTP {resp.status}: {error_text[:500]}")

        result = await resp.json()
        file_id = result.get("id")
        if not file_id:
            raise RuntimeError(f"文件上传响应异常: {result}")

        return file_id


# ─── 批量任务提交 ──────────────────────────────────────────

async def submit_batch(
    jobs: List[BatchJob],
    *,
    api_key: Optional[str] = None,
    api_url: str = DEFAULT_BATCH_API_URL,
    completion_window: str = "24h",
) -> str:
    """
    提交批量任务到 OpenAI Batch API。

    Args:
        jobs: 批量任务列表（最多 50,000 个）
        api_key: API 密钥
        api_url: Batch API 端点
        completion_window: 完成时间窗口（"24h"）

    Returns:
        batch_id: 批次 ID，用于后续查询
    """
    if len(jobs) > MAX_BATCH_SIZE:
        raise ValueError(f"任务数超过限制: {len(jobs)} > {MAX_BATCH_SIZE}")

    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY 环境变量")

    # 上传文件
    print(f"[Batch] 上传 {len(jobs)} 个任务...")
    file_id = await _upload_batch_file(jobs, api_key)
    print(f"[Batch] 文件上传成功: {file_id}")

    # 创建批次
    pool = await ConnectionPool.get_instance()
    session = await pool.get_session()

    body = {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": completion_window,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with session.post(api_url, json=body, headers=headers) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise RuntimeError(f"批次创建失败: HTTP {resp.status}: {error_text[:500]}")

        result = await resp.json()
        batch_id = result.get("id")
        if not batch_id:
            raise RuntimeError(f"批次创建响应异常: {result}")

        print(f"[Batch] 批次创建成功: {batch_id}")
        return batch_id


# ─── 批量任务状态查询 ──────────────────────────────────────

async def get_batch_status(
    batch_id: str,
    *,
    api_key: Optional[str] = None,
    api_url: str = DEFAULT_BATCH_API_URL,
) -> Dict[str, Any]:
    """查询批量任务状态"""
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    pool = await ConnectionPool.get_instance()
    session = await pool.get_session()

    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{api_url}/{batch_id}"

    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise RuntimeError(f"查询失败: HTTP {resp.status}: {error_text[:500]}")

        return await resp.json()


async def _download_results(
    output_file_id: str,
    *,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """下载批量任务结果文件"""
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    file_url = f"https://api.openai.com/v1/files/{output_file_id}/content"

    pool = await ConnectionPool.get_instance()
    session = await pool.get_session()

    headers = {"Authorization": f"Bearer {api_key}"}

    async with session.get(file_url, headers=headers) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise RuntimeError(f"结果下载失败: HTTP {resp.status}: {error_text[:500]}")

        text = await resp.text()
        results = []
        for line in text.strip().split("\n"):
            if line:
                results.append(json.loads(line))
        return results


async def poll_batch_results(
    batch_id: str,
    *,
    api_key: Optional[str] = None,
    poll_interval: int = BATCH_POLL_INTERVAL,
    max_wait: int = BATCH_MAX_WAIT_TIME,
    progress_callback: Optional[Callable] = None,
) -> BatchResult:
    """
    轮询批量任务直到完成。

    Args:
        batch_id: 批次 ID
        api_key: API 密钥
        poll_interval: 轮询间隔（秒）
        max_wait: 最大等待时间（秒）
        progress_callback: 进度回调 callback(status, message)

    Returns:
        BatchResult 结果对象
    """
    start_time = time.time()
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            return BatchResult(
                batch_id=batch_id,
                status="timeout",
                error=f"等待超时: {elapsed:.0f}s > {max_wait}s",
                elapsed=elapsed,
            )

        status_info = await get_batch_status(batch_id, api_key=api_key)
        status = status_info.get("status", "unknown")

        if progress_callback:
            progress_callback(status, f"已等待 {elapsed:.0f}s")

        print(f"[Batch] 状态: {status} | 已等待: {elapsed:.0f}s")

        if status == "completed":
            # 下载结果
            output_file_id = status_info.get("output_file_id")
            if not output_file_id:
                return BatchResult(
                    batch_id=batch_id,
                    status="failed",
                    error="completed 但无 output_file_id",
                    elapsed=elapsed,
                )

            print(f"[Batch] 下载结果文件: {output_file_id}")
            raw_results = await _download_results(output_file_id, api_key=api_key)

            # 解析结果
            results = []
            for raw in raw_results:
                custom_id = raw.get("custom_id", "")
                response = raw.get("response", {})
                body = response.get("body", {})

                if response.get("status_code") == 200:
                    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = body.get("usage", {})

                    results.append(LLMResult(
                        task_id=custom_id,
                        success=True,
                        content=content,
                        json_data=_extract_json(content),
                        usage=usage,
                        attempts=1,
                        elapsed=0.0,
                    ))
                else:
                    results.append(LLMResult(
                        task_id=custom_id,
                        success=False,
                        error=f"API 错误: {response.get('status_code')} - {body}",
                        attempts=1,
                        elapsed=0.0,
                    ))

            return BatchResult(
                batch_id=batch_id,
                status="completed",
                results=results,
                created_at=status_info.get("created_at"),
                completed_at=status_info.get("completed_at"),
                elapsed=elapsed,
            )

        elif status in ("failed", "expired", "cancelled"):
            return BatchResult(
                batch_id=batch_id,
                status=status,
                error=f"批次失败: {status_info.get('errors', '未知错误')}",
                elapsed=elapsed,
            )

        # 继续等待
        await asyncio.sleep(poll_interval)


def _extract_json(text: str) -> Optional[Dict]:
    """从 LLM 输出中提取 JSON"""
    import re
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


# ─── 高级接口：提交+等待 ───────────────────────────────────

async def batch_call_llm_batch_api(
    tasks: List[LLMTask],
    *,
    api_key: Optional[str] = None,
    max_batch_size: int = MAX_BATCH_SIZE,
    poll_interval: int = BATCH_POLL_INTERVAL,
    max_wait: int = BATCH_MAX_WAIT_TIME,
    progress_callback: Optional[Callable] = None,
) -> List[LLMResult]:
    """
    使用 Batch API 批量调用 LLM（提交+等待完整流程）。

    Args:
        tasks: 任务列表
        api_key: API 密钥
        max_batch_size: 单批次最大任务数（超过则自动分片）
        poll_interval: 轮询间隔
        max_wait: 最大等待时间
        progress_callback: 进度回调

    Returns:
        与 tasks 顺序对应的 LLMResult 列表
    """
    if not tasks:
        return []

    # 分片处理（如果任务数超过限制）
    batches = []
    for i in range(0, len(tasks), max_batch_size):
        batch_tasks = tasks[i:i + max_batch_size]
        jobs = [
            BatchJob(custom_id=task.task_id, task=task)
            for task in batch_tasks
        ]
        batches.append((i, jobs))

    all_results: Dict[str, LLMResult] = {}

    for batch_idx, (offset, jobs) in enumerate(batches):
        print(f"\n[Batch] 处理第 {batch_idx + 1}/{len(batches)} 个批次 ({len(jobs)} 个任务)")

        # 提交
        batch_id = await submit_batch(jobs, api_key=api_key)

        # 等待结果
        def _progress(status, message):
            if progress_callback:
                progress_callback(batch_idx, len(batches), status, message)

        result = await poll_batch_results(
            batch_id,
            api_key=api_key,
            poll_interval=poll_interval,
            max_wait=max_wait,
            progress_callback=_progress,
        )

        if result.status != "completed":
            print(f"[Batch] 批次失败: {result.error}")
            # 为失败的任务填充错误结果
            for job in jobs:
                if job.custom_id not in all_results:
                    all_results[job.custom_id] = LLMResult(
                        task_id=job.custom_id,
                        success=False,
                        error=f"批次失败: {result.error}",
                    )
        else:
            for r in result.results:
                all_results[r.task_id] = r

            print(f"[Batch] 批次完成: {sum(1 for r in result.results if r.success)}/{len(result.results)} 成功")

    # 按原始顺序返回
    return [all_results.get(task.task_id, LLMResult(
        task_id=task.task_id,
        success=False,
        error="未找到结果",
    )) for task in tasks]


# ─── 混合策略：小批量用 asyncio，大批量用 Batch API ─────────

async def smart_batch_call(
    tasks: List[LLMTask],
    *,
    batch_api_threshold: int = 100,   # 超过此数量使用 Batch API
    asyncio_concurrency: int = 20,
    rate_limit_rps: float = 10.0,
    **batch_api_kwargs,
) -> List[LLMResult]:
    """
    智能选择并发策略：
    - 小批量 (<100): 使用 asyncio 实时并发
    - 大批量 (>=100): 使用 Batch API 降低成本

    用法：
        results = await smart_batch_call(tasks, batch_api_threshold=100)
    """
    if len(tasks) >= batch_api_threshold:
        print(f"[Smart] 任务数 {len(tasks)} >= {batch_api_threshold}，使用 Batch API")
        return await batch_call_llm_batch_api(tasks, **batch_api_kwargs)
    else:
        print(f"[Smart] 任务数 {len(tasks)} < {batch_api_threshold}，使用 asyncio 并发")
        from engine.llm_generate_async import batch_call_llm_with_progress
        return await batch_call_llm_with_progress(
            tasks,
            max_concurrency=asyncio_concurrency,
            rate_limit_rps=rate_limit_rps,
        )


# ─── 同步包装器 ────────────────────────────────────────────

def batch_call_llm_batch_api_sync(*args, **kwargs) -> List[LLMResult]:
    """同步包装器"""
    return asyncio.run(batch_call_llm_batch_api(*args, **kwargs))


def smart_batch_call_sync(*args, **kwargs) -> List[LLMResult]:
    """同步包装器"""
    return asyncio.run(smart_batch_call(*args, **kwargs))


# ─── 主程序测试 ────────────────────────────────────────────

async def _test_batch_api():
    """测试 Batch API（需要 OPENAI_API_KEY）"""
    print("=" * 60)
    print("Batch API 测试")
    print("=" * 60)

    if not os.environ.get("OPENAI_API_KEY"):
        print("跳过测试：未设置 OPENAI_API_KEY")
        return

    tasks = [
        LLMTask(
            prompt=f"请用一句话回答：什么是批量处理？（测试 {i+1}）",
            system="你是一个简洁的助手。",
            task_id=f"batch_test_{i}",
        )
        for i in range(3)
    ]

    start = time.time()
    results = await batch_call_llm_batch_api(tasks)
    elapsed = time.time() - start

    print(f"\n总耗时: {elapsed:.1f}s")
    print(f"成功: {sum(1 for r in results if r.success)}/{len(results)}")
    for r in results:
        status = "✓" if r.success else "✗"
        print(f"  {status} {r.task_id}: {r.content[:50] if r.success else r.error}")


if __name__ == "__main__":
    asyncio.run(_test_batch_api())
