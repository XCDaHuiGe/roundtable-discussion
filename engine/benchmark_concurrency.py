# -*- coding: utf-8 -*-
"""
并发方案性能基准测试

对比三种方案的耗时和成功率：
1. 串行（原始代码）
2. ThreadPoolExecutor
3. asyncio + aiohttp
4. Batch API（可选）

用法：
    python engine/benchmark_concurrency.py --tasks 20 --workers 10
"""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.llm_generate import generate_with_progress
from engine.llm_generate_threaded import generate_with_progress_concurrent
from engine.llm_generate_async import (
    LLMTask, batch_call_llm_with_progress, close_all_connections
)


def create_test_tasks(count: int) -> List[Dict]:
    """创建测试任务"""
    return [
        {
            "prompt": f"请用一句话回答：什么是编程范式？（测试任务 {i+1}/{count}）",
            "system": "你是一个简洁的技术专家，只回答一句话。",
        }
        for i in range(count)
    ]


def create_async_tasks(count: int) -> List[LLMTask]:
    """创建异步测试任务"""
    return [
        LLMTask(
            prompt=f"请用一句话回答：什么是编程范式？（测试任务 {i+1}/{count}）",
            system="你是一个简洁的技术专家，只回答一句话。",
            task_id=f"async_test_{i}",
        )
        for i in range(count)
    ]


def run_serial(tasks: List[Dict]) -> Dict:
    """运行串行基准测试"""
    print("\n" + "=" * 60)
    print("方案 1: 串行执行（原始代码）")
    print("=" * 60)

    start = time.time()
    results = generate_with_progress(tasks, desc="串行基准")
    elapsed = time.time() - start

    success = sum(1 for r in results if r["success"])
    return {
        "scheme": "serial",
        "workers": 1,
        "elapsed": elapsed,
        "success": success,
        "total": len(tasks),
        "success_rate": success / len(tasks),
        "avg_per_task": elapsed / len(tasks) if tasks else 0,
    }


def run_threaded(tasks: List[Dict], workers: int) -> Dict:
    """运行线程池测试"""
    print("\n" + "=" * 60)
    print(f"方案 2: ThreadPoolExecutor (workers={workers})")
    print("=" * 60)

    start = time.time()
    results = generate_with_progress_concurrent(tasks, desc=f"线程池x{workers}", max_workers=workers)
    elapsed = time.time() - start

    success = sum(1 for r in results if r["success"])
    return {
        "scheme": "threaded",
        "workers": workers,
        "elapsed": elapsed,
        "success": success,
        "total": len(tasks),
        "success_rate": success / len(tasks),
        "avg_per_task": elapsed / len(tasks) if tasks else 0,
    }


async def run_asyncio(tasks: List[LLMTask], concurrency: int, rate_limit: float) -> Dict:
    """运行 asyncio 测试"""
    print("\n" + "=" * 60)
    print(f"方案 3: asyncio + aiohttp (concurrency={concurrency}, rate_limit={rate_limit}/s)")
    print("=" * 60)

    start = time.time()
    results = await batch_call_llm_with_progress(
        tasks,
        desc=f"asyncio x{concurrency}",
        max_concurrency=concurrency,
        rate_limit_rps=rate_limit,
    )
    elapsed = time.time() - start

    success = sum(1 for r in results if r.success)
    return {
        "scheme": "asyncio",
        "workers": concurrency,
        "elapsed": elapsed,
        "success": success,
        "total": len(tasks),
        "success_rate": success / len(tasks),
        "avg_per_task": elapsed / len(tasks) if tasks else 0,
    }


def print_results(results: List[Dict], baseline: Dict):
    """打印对比结果"""
    print("\n" + "=" * 80)
    print("性能对比总结")
    print("=" * 80)
    print(f"{'方案':<20} {'并发度':<10} {'耗时(s)':<12} {'加速比':<10} {'成功率':<10} {'平均/任务':<12}")
    print("-" * 80)

    for r in results:
        speedup = baseline["elapsed"] / r["elapsed"] if r["elapsed"] > 0 else float('inf')
        print(
            f"{r['scheme']:<20} "
            f"{r['workers']:<10} "
            f"{r['elapsed']:<12.1f} "
            f"{speedup:<10.1f}x "
            f"{r['success_rate']*100:<9.0f}% "
            f"{r['avg_per_task']:<12.2f}s"
        )

    print("-" * 80)
    best = max(results, key=lambda x: baseline["elapsed"] / x["elapsed"] if x["elapsed"] > 0 else 0)
    print(f"最佳方案: {best['scheme']} (workers={best['workers']}, 加速比 {baseline['elapsed']/best['elapsed']:.1f}x)")
    print("=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="并发方案性能基准测试")
    parser.add_argument("--tasks", type=int, default=10, help="测试任务数量")
    parser.add_argument("--workers", type=int, default=10, help="并发工作数")
    parser.add_argument("--rate-limit", type=float, default=10.0, help="每秒请求限制")
    parser.add_argument("--skip-serial", action="store_true", help="跳过串行测试（节省时间）")
    parser.add_argument("--skip-threaded", action="store_true", help="跳过线程池测试")
    parser.add_argument("--skip-asyncio", action="store_true", help="跳过 asyncio 测试")
    parser.add_argument("--output", type=str, help="结果输出 JSON 文件")
    args = parser.parse_args()

    print("=" * 80)
    print("LLM 并发方案性能基准测试")
    print("=" * 80)
    print(f"任务数: {args.tasks}")
    print(f"线程池 workers: {args.workers}")
    print(f"asyncio 并发度: {args.workers}")
    print(f"速率限制: {args.rate_limit}/s")
    print(f"API: {os.environ.get('OPENROUTER_API_KEY', '未设置')[:20]}...")
    print("=" * 80)

    # 检查 API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("\n[警告] 未设置 OPENROUTER_API_KEY 环境变量，测试将失败")
        print("请设置: $env:OPENROUTER_API_KEY = 'your-key'")
        return

    all_results = []
    baseline = None

    # 串行基准
    if not args.skip_serial:
        serial_tasks = create_test_tasks(args.tasks)
        baseline = run_serial(serial_tasks)
        all_results.append(baseline)
    else:
        # 如果没有串行基准，用线程池 1 worker 作为基准
        serial_tasks = create_test_tasks(min(args.tasks, 3))
        baseline = run_threaded(serial_tasks, 1)
        all_results.append(baseline)

    # 线程池
    if not args.skip_threaded:
        threaded_tasks = create_test_tasks(args.tasks)
        threaded_result = run_threaded(threaded_tasks, args.workers)
        all_results.append(threaded_result)

    # asyncio
    if not args.skip_asyncio:
        async_tasks = create_async_tasks(args.tasks)
        asyncio_result = await run_asyncio(async_tasks, args.workers, args.rate_limit)
        all_results.append(asyncio_result)
        await close_all_connections()

    # 打印结果
    print_results(all_results, baseline)

    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({
                "config": {
                    "tasks": args.tasks,
                    "workers": args.workers,
                    "rate_limit": args.rate_limit,
                },
                "results": all_results,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
