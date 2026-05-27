# -*- coding: utf-8 -*-
"""
LLM 线程池并发调用模块 - ThreadPoolExecutor 实现

特性：
- 兼容现有同步代码（无需 async/await）
- 线程级并发（适合 I/O 密集型）
- 复用现有 call_llm 函数
- 支持进度追踪和错误处理
- 适合不想引入 asyncio 的场景

用法：
    # 简单批量调用
    results = batch_call_llm_threaded(tasks, max_workers=10)

    # 带进度条
    results = batch_call_llm_threaded_with_progress(tasks, desc="生成中")

与 asyncio 方案对比：
- 优点：零改造成本，直接替换 generate_with_progress
- 缺点：并发上限受线程数限制，内存开销较大
- 适用：快速迁移、脚本工具、不想引入 async 的场景
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# 导入现有的同步调用函数
from engine.llm_generate import call_llm, ProgressTracker


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class ThreadedLLMTask:
    """线程池任务定义"""
    prompt: str
    system: str = ""
    task_id: str = ""
    # 透传给 call_llm 的参数
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    connect_timeout: Optional[int] = None
    read_timeout: Optional[int] = None
    max_retries: Optional[int] = None
    retry_base_delay: Optional[float] = None
    request_interval: Optional[float] = None
    response_format: Optional[Dict] = None
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"task_{id(self)}_{int(time.time()*1000)%10000}"

    def to_call_llm_kwargs(self) -> Dict[str, Any]:
        """转换为 call_llm 的参数"""
        kwargs = {}
        for key in [
            'api_key', 'api_url', 'model', 'max_tokens', 'temperature',
            'connect_timeout', 'read_timeout', 'max_retries',
            'retry_base_delay', 'request_interval', 'response_format'
        ]:
            val = getattr(self, key)
            if val is not None:
                kwargs[key] = val
        return kwargs


@dataclass
class ThreadedLLMResult:
    """线程池调用结果"""
    task_id: str
    success: bool
    content: str = ""
    json_data: Optional[Dict] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    attempts: int = 0
    elapsed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── 核心线程池调用 ────────────────────────────────────────

def _call_llm_wrapper(task: ThreadedLLMTask) -> ThreadedLLMResult:
    """
    在线程中执行单个 LLM 调用。
    这个函数会被 ThreadPoolExecutor 调度到工作线程执行。
    """
    kwargs = task.to_call_llm_kwargs()

    # 调用现有的同步 call_llm
    result = call_llm(task.prompt, task.system, **kwargs)

    return ThreadedLLMResult(
        task_id=task.task_id,
        success=result["success"],
        content=result.get("content", ""),
        json_data=result.get("json"),
        usage=result.get("usage", {}),
        error=result.get("error"),
        attempts=result.get("attempts", 1),
        elapsed=result.get("elapsed", 0.0),
        metadata=task.metadata,
    )


def batch_call_llm_threaded(
    tasks: List[ThreadedLLMTask],
    *,
    max_workers: int = 10,
    progress_callback: Optional[Callable] = None,
    fail_fast: bool = False,
) -> List[ThreadedLLMResult]:
    """
    使用线程池批量调用 LLM。

    Args:
        tasks: 任务列表
        max_workers: 最大工作线程数
        progress_callback: 进度回调 callback(completed, total, task_id, result)
        fail_fast: 是否遇到第一个错误就终止（注意：线程池模式下难以真正中断）

    Returns:
        与 tasks 顺序对应的 ThreadedLLMResult 列表
    """
    if not tasks:
        return []

    total = len(tasks)
    results_map: Dict[str, ThreadedLLMResult] = {}
    completed = 0

    # 使用线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务，保留 future -> task_id 映射
        future_to_task = {
            executor.submit(_call_llm_wrapper, task): task
            for task in tasks
        }

        # 按完成顺序处理结果
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
            except Exception as e:
                result = ThreadedLLMResult(
                    task_id=task.task_id,
                    success=False,
                    error=f"线程执行异常: {str(e)}",
                    metadata=task.metadata,
                )

            results_map[task.task_id] = result
            completed += 1

            if progress_callback:
                progress_callback(completed, total, task.task_id, result)

            if fail_fast and not result.success:
                # 取消剩余任务
                for f in future_to_task:
                    if not f.done():
                        f.cancel()
                break

    # 按原始顺序返回
    return [results_map[task.task_id] for task in tasks]


def batch_call_llm_threaded_with_progress(
    tasks: List[ThreadedLLMTask],
    *,
    desc: str = "生成中",
    max_workers: int = 10,
    **kwargs,
) -> List[ThreadedLLMResult]:
    """
    线程池批量调用 LLM 并显示进度条。

    这是 generate_with_progress 的直接替代品。

    用法：
        # 旧代码（串行）：
        results = generate_with_progress(tasks, desc="生成话题")

        # 新代码（并发）：
        results = batch_call_llm_threaded_with_progress(tasks, desc="生成话题", max_workers=10)
    """
    tracker = ProgressTracker(len(tasks), desc)
    tracker.update(0, "启动线程池...")

    def progress_callback(completed, total, task_id, result):
        status = "✓" if result.success else "✗"
        msg = f"{status} {task_id[:30]}"
        if not result.success and result.error:
            msg += f" | 错误: {result.error[:40]}"
        tracker.update(completed, msg)

    results = batch_call_llm_threaded(
        tasks,
        max_workers=max_workers,
        progress_callback=progress_callback,
        **kwargs,
    )

    success_count = sum(1 for r in results if r.success)
    tracker.finish(f"完成 {success_count}/{len(tasks)} 成功")
    return results


# ─── 与现有代码的适配器 ────────────────────────────────────

def generate_with_progress_concurrent(
    tasks: List[Dict],
    desc: str = "生成中",
    max_workers: int = 10,
    **default_kwargs,
) -> List[Dict]:
    """
    完全兼容现有 generate_with_progress 接口的并发版本。

    参数和返回值与原始函数完全一致，可以直接替换：

        # 旧调用：
        from engine.llm_generate import generate_with_progress
        results = generate_with_progress(tasks, desc="生成中")

        # 新调用（只需改导入）：
        from engine.llm_generate_threaded import generate_with_progress_concurrent
        results = generate_with_progress_concurrent(tasks, desc="生成中", max_workers=10)

    返回的列表元素格式与 call_llm 返回值一致：
        [{"success": bool, "content": str, "json": dict, "usage": dict, ...}, ...]
    """
    # 将字典任务转换为 ThreadedLLMTask
    threaded_tasks = []
    for i, task in enumerate(tasks):
        merged = {**default_kwargs, **task}
        prompt = merged.pop("prompt")
        system = merged.pop("system", "")

        threaded_tasks.append(ThreadedLLMTask(
            prompt=prompt,
            system=system,
            task_id=merged.pop("task_id", f"task_{i}"),
            **{k: v for k, v in merged.items()
               if k in ['api_key', 'api_url', 'model', 'max_tokens', 'temperature',
                        'connect_timeout', 'read_timeout', 'max_retries',
                        'retry_base_delay', 'request_interval', 'response_format']},
        ))

    # 执行并发调用
    results = batch_call_llm_threaded_with_progress(
        threaded_tasks,
        desc=desc,
        max_workers=max_workers,
    )

    # 转换回原始格式
    return [
        {
            "success": r.success,
            "content": r.content,
            "json": r.json_data,
            "usage": r.usage,
            "error": r.error,
            "attempts": r.attempts,
            "elapsed": r.elapsed,
        }
        for r in results
    ]


# ─── 性能对比工具 ──────────────────────────────────────────

def benchmark(
    tasks: List[Dict],
    max_workers_list: List[int] = [1, 5, 10, 20],
    **default_kwargs,
) -> Dict[str, Any]:
    """
    对比不同并发度下的性能。

    用法：
        results = benchmark(tasks, max_workers_list=[1, 5, 10, 20])
        for r in results["results"]:
            print(f"workers={r['workers']}: {r['elapsed']:.1f}s")
    """
    from engine.llm_generate import generate_with_progress  # 原始串行版本

    benchmarks = []

    # 基准：串行
    print("=" * 60)
    print("基准测试：串行执行")
    print("=" * 60)
    start = time.time()
    serial_results = generate_with_progress(tasks, desc="串行基准", **default_kwargs)
    serial_elapsed = time.time() - start
    benchmarks.append({
        "workers": 1,
        "mode": "serial",
        "elapsed": serial_elapsed,
        "success_rate": sum(1 for r in serial_results if r["success"]) / len(tasks),
    })
    print(f"串行耗时: {serial_elapsed:.1f}s\n")

    # 并发测试
    for workers in max_workers_list:
        if workers == 1:
            continue  # 已测试

        print(f"测试并发度: {workers}")
        start = time.time()
        concurrent_results = generate_with_progress_concurrent(
            tasks, desc=f"并发{workers}", max_workers=workers, **default_kwargs
        )
        elapsed = time.time() - start
        speedup = serial_elapsed / elapsed if elapsed > 0 else float('inf')

        benchmarks.append({
            "workers": workers,
            "mode": "threaded",
            "elapsed": elapsed,
            "success_rate": sum(1 for r in concurrent_results if r["success"]) / len(tasks),
            "speedup": speedup,
        })
        print(f"  耗时: {elapsed:.1f}s | 加速比: {speedup:.1f}x\n")

    return {
        "task_count": len(tasks),
        "benchmarks": benchmarks,
        "best_config": max(benchmarks, key=lambda x: x.get("speedup", 0)),
    }


# ─── 主程序测试 ────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("ThreadPoolExecutor 并发 LLM 调用测试")
    print("=" * 60)

    # 构造测试任务
    test_tasks = [
        {
            "prompt": f"请用一句话解释什么是并发编程？（测试 {i+1}）",
            "system": "你是一个简洁的技术专家。",
        }
        for i in range(5)
    ]

    print(f"\n测试任务数: {len(test_tasks)}")
    print(f"并发度: 5\n")

    start = time.time()
    results = generate_with_progress_concurrent(
        test_tasks,
        desc="线程池测试",
        max_workers=5,
    )
    elapsed = time.time() - start

    print(f"\n总耗时: {elapsed:.1f}s")
    print(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['content'][:50] if r['success'] else r['error']}")
