import asyncio
from typing import Any, Dict, List, Coroutine
from litellm import completion, acompletion


class LLMWrapper:
    REQUIRED_KEYS = ["model", "temperature", "api_key"]

    @staticmethod
    def _check_required_keys(config: Dict[str, Any]):
        """必要なキーが設定に含まれているかチェックする"""
        for key in LLMWrapper.REQUIRED_KEYS:
            if key not in config:
                raise ValueError(f"必須キーが不足しています: {key}")

    # ==== 同期処理 ====
    @staticmethod
    def llmcall(config: Dict[str, Any]) -> Any:
        """
        同期処理での単一呼び出し
        """
        LLMWrapper._check_required_keys(config)
        return completion(**config)

    @staticmethod
    def llmcall_batch(configs: List[Dict[str, Any]]) -> List[Any]:
        """
        同期処理でのバッチ呼び出し
        """
        results = []
        for cfg in configs:
            LLMWrapper._check_required_keys(cfg)
            results.append(completion(**cfg))
        return results

    # ==== 非同期処理（タスクを返す） ====
    @staticmethod
    async def allmcall(config: Dict[str, Any]) -> asyncio.Task:
        """
        非同期処理での単一呼び出し - 作成されたタスクを返す（awaitされていない）
        """
        LLMWrapper._check_required_keys(config)
        return asyncio.create_task(acompletion(**config))

    @staticmethod
    async def allmcall_batch(configs: List[Dict[str, Any]]) -> List[asyncio.Task]:
        """
        非同期処理でのバッチ呼び出し - タスクのリストを返す（awaitされていない）
        """
        tasks = []
        for cfg in configs:
            LLMWrapper._check_required_keys(cfg)
            tasks.append(asyncio.create_task(acompletion(**cfg)))
        return tasks

    @staticmethod
    def run_coroutines(coros: List[Coroutine]) -> List[Any]:
        """
        引数にコルーチンを取り、非同期でまとめて実行して結果を返す
        ※コルーチンは未スケジューリング状態（まだ実行されていない）
        """
        async def runner():
            return await asyncio.gather(*coros)
        return asyncio.run(runner())

    @staticmethod
    def run_tasks(tasks: List[asyncio.Task]) -> List[Any]:
        """
        引数に create_task() 等でスケジュールされた Task を受け取り、
        すでに進行中の非同期処理の完了を待って結果を返す。
        """
        async def runner():
            return await asyncio.gather(*tasks)
        return asyncio.run(runner())
