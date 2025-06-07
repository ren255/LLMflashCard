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
import base64
from io import BytesIO
from PIL import Image


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
            raise PermissionError(".env not forund")

        return os.environ.get(key)


class ParallelLLMCaller:
    def __init__(self, config: GlobalConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config.api_key,
        )

    def _pil_to_base64(self, pil_image: Image.Image, format: str = "PNG") -> str:
        """PIL ImageをBase64文字列に変換"""
        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')

    async def single_call(self, model_name: str, prompt: str, pil_image: Optional[Image.Image] = None) -> LLMResult:
        """単一のLLM呼び出し（エラーハンドリング付き）"""
        result = LLMResult(prompt=prompt, model_name=model_name)
        start_time = time.perf_counter()

        try:
            model_cfg = self.config.models[model_name]

            # メッセージの基本構造
            message_content = prompt

            # 画像がある場合はbase64エンコードして追加
            if pil_image:
                base64_image = self._pil_to_base64(pil_image)
                message_content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"}}
                ]

            params = {
                "model": model_cfg["name"],
                "temperature": model_cfg.get("temperature", 0.5),
                "max_tokens": model_cfg.get("max_tokens", 4096),
                "messages": [{"role": "user", "content": message_content}],
            }

            completion = await self.client.chat.completions.create(**params)
            result.result = completion.choices[0].message.content
            result.success = True

        except Exception as e:
            result.error = str(e)
            result.success = False

        finally:
            result.duration = time.perf_counter() - start_time

        return result

    async def _batch_call_base(
        self,
        tasks_data: List[Dict[str, Any]],
        model_name: str,
        max_concurrent: int = 5,
        show_progress: bool = True
    ) -> List[LLMResult]:
        """
        基底のバッチ処理関数

        Args:
            tasks_data: [{"prompt": str, "image": Optional[PIL.Image], "index": int}, ...]
            model_name: 使用するモデル名
            max_concurrent: 最大同時実行数
            show_progress: 進捗表示するかどうか

        Returns:
            LLMResultのリスト（元の順序を保持）
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_call(task_data: Dict[str, Any]) -> tuple[int, LLMResult]:
            async with semaphore:
                result = await self.single_call(
                    model_name,
                    task_data["prompt"],
                    task_data.get("image")
                )
                if show_progress:
                    status = "✓" if result.success else "✗"
                    print(
                        f"[{task_data['index']+1}/{len(tasks_data)}] {status} {result.prompt[:50]}...")
                return task_data["index"], result

        # 全てのタスクを作成
        tasks = [asyncio.create_task(limited_call(task_data))
                 for task_data in tasks_data]

        # 全てのタスクを実行し、インデックス順に結果を並べ替え
        indexed_results = await asyncio.gather(*tasks)

        # インデックス順にソートして結果のリストを作成
        results = [None] * len(tasks_data)
        for index, result in indexed_results:
            results[index] = result

        return results

    async def batch_call(
        self,
        prompts: List[str],
        model_name: str,
        max_concurrent: int = 10,
        show_progress: bool = True
    ) -> List[LLMResult]:
        """
        プロンプトのリストを並列処理で実行（画像なし）

        Args:
            prompts: プロンプトのリスト
            model_name: 使用するモデル名
            max_concurrent: 最大同時実行数
            show_progress: 進捗表示するかどうか

        Returns:
            LLMResultのリスト（元の順序を保持）
        """
        tasks_data = [
            {"prompt": prompt, "image": None, "index": i}
            for i, prompt in enumerate(prompts)
        ]

        return await self._batch_call_base(tasks_data, model_name, max_concurrent, show_progress)

    async def batch_call_dict(
        self,
        prompt_image_dict: Dict[str, Optional[Image.Image]],
        model_name: str,
        max_concurrent: int = 10,
        show_progress: bool = True
    ) -> List[LLMResult]:
        """
        プロンプト + PIL Image の辞書を受け取って並列処理で実行

        Args:
            prompt_image_dict: {prompt: PIL.Image or None} の辞書
            model_name: 使用するモデル名
            max_concurrent: 最大同時実行数
            show_progress: 進捗表示するかどうか

        Returns:
            LLMResultのリスト（辞書のキー順序を保持）
        """
        tasks_data = [
            {"prompt": prompt, "image": image, "index": i}
            for i, (prompt, image) in enumerate(prompt_image_dict.items())
        ]

        return await self._batch_call_base(tasks_data, model_name, max_concurrent, show_progress)

    async def batch_call_listIMG(
        self,
        prompt: str,
        images: List[Image.Image],
        model_name: str,
        max_concurrent: int = 10,
        show_progress: bool = True
    ) -> List[LLMResult]:
        """
        単一のプロンプトと複数の画像リストを受け取って並列処理で実行

        Args:
            prompt: 全画像に適用するプロンプト
            images: PIL.Imageのリスト
            model_name: 使用するモデル名
            max_concurrent: 最大同時実行数
            show_progress: 進捗表示するかどうか

        Returns:
            LLMResultのリスト（画像の順序を保持）
        """
        tasks_data = [
            {"prompt": prompt, "image": image, "index": i}
            for i, image in enumerate(images)
        ]

        return await self._batch_call_base(tasks_data, model_name, max_concurrent, show_progress)

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
