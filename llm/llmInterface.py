import time
from pathlib import Path
import yaml
import os
import asyncio
from pathlib import Path
from openai import AsyncOpenAI
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging


@dataclass
class LLMResult:
    """LLM呼び出し結果を格納するデータクラス"""
    prompt: str
    result: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    model_name: str = ""
    success: bool = False


class GlobalConfig:
    def __init__(self, config_path, env_path):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)
        self.models = self._load_yaml(self.config_path)
        self.api_key = self._load_env("OPENROUTER_API_KEY")

    def _load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)["models"]

    def _load_env(self, key):
        env_file = self.env_path
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        return line.strip().split("=", 1)[1]
        else:
            raise PermissionError(f".env not forund \n{env_file}")

        return os.environ.get(key)


class ParallelLLMCaller:
    def __init__(self, config: GlobalConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config.api_key,
        )

    async def _single_call(self, model_name: str, prompt: str, image_path: Optional[str] = None) -> LLMResult:
        """単一のLLM呼び出し（エラーハンドリング付き）"""
        result = LLMResult(prompt=prompt, model_name=model_name)
        start_time = time.perf_counter()

        try:
            model_cfg = self.config.models[model_name]
            params = {
                "model": model_cfg["name"],
                "temperature": model_cfg.get("temperature", 0.5),
                "max_tokens": model_cfg.get("max_tokens", 4096),
                "messages": [{"role": "user", "content": prompt}],
            }

            if image_path:
                with open(image_path, "rb") as f:
                    img_bytes = f.read()
                params["messages"][0]["image"] = img_bytes

            completion = await self.client.chat.completions.create(**params)
            result.result = completion.choices[0].message.content
            result.success = True

        except Exception as e:
            result.error = str(e)
            result.success = False

        finally:
            result.duration = time.perf_counter() - start_time

        return result

    async def batch_call(
        self,
        prompts: List[str],
        model_name: str,
        max_concurrent: int = 5,
        show_progress: bool = True
    ) -> List[LLMResult]:
        """
        プロンプトのリストを並列処理で実行

        Args:
            prompts: プロンプトのリスト
            model_name: 使用するモデル名
            max_concurrent: 最大同時実行数
            show_progress: 進捗表示するかどうか

        Returns:
            LLMResultのリスト（元の順序を保持）
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_call(prompt: str, index: int) -> tuple[int, LLMResult]:
            async with semaphore:
                result = await self._single_call(model_name, prompt)
                if show_progress:
                    status = "✓" if result.success else "✗"
                    print(
                        f"[{index+1}/{len(prompts)}] {status} {result.prompt[:50]}...")
                return index, result

        # 全てのタスクを作成（インデックス付き）
        tasks = [asyncio.create_task(limited_call(prompt, i))
                 for i, prompt in enumerate(prompts)]

        # 全てのタスクを実行し、インデックス順に結果を並べ替え
        indexed_results = await asyncio.gather(*tasks)

        # インデックス順にソートして結果のリストを作成
        results = [None] * len(prompts)
        for index, result in indexed_results:
            results[index] = result

        return results

    async def _run_with_progress(self, tasks: List[asyncio.Task], prompts: List[str]) -> List[LLMResult]:
        """この関数は不要になったので削除予定"""
        pass

    async def multi_model_call(
        self,
        prompts: List[str],
        model_names: List[str],
        max_concurrent: int = 5
    ) -> Dict[str, List[LLMResult]]:
        """
        複数のモデルで同じプロンプトセットを実行

        Args:
            prompts: プロンプトのリスト
            model_names: モデル名のリスト
            max_concurrent: 最大同時実行数

        Returns:
            {model_name: [LLMResult, ...]} の辞書
        """
        results = {}

        # 各モデルで並列実行
        model_tasks = []
        for model_name in model_names:
            task = asyncio.create_task(
                self.batch_call(prompts, model_name,
                                max_concurrent, show_progress=False)
            )
            model_tasks.append((model_name, task))

        # 全モデルの結果を待機
        for model_name, task in model_tasks:
            results[model_name] = await task
            print(f"モデル {model_name} の処理完了")

        return results

    def print_results(self, results: List[LLMResult], show_errors: bool = True):
        """結果を見やすく表示"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"\n=== 実行結果 ===")
        print(f"成功: {len(successful)}/{len(results)}")
        print(
            f"平均実行時間: {sum(r.duration for r in successful)/len(successful) if successful else 1:.2f}秒")

        print(f"\n=== 成功した結果 ===")
        for i, result in enumerate(successful, 1):
            print(f"\n[{i}] プロンプト: {result.prompt}")
            print(f"結果: {result.result}")
            print(f"実行時間: {result.duration:.2f}秒")

        if failed and show_errors:
            print(f"\n=== エラー ({len(failed)}件) ===")
            for result in failed:
                print(f"プロンプト: {result.prompt}")
                print(f"エラー: {result.error}")
