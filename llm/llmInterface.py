import time
from pathlib import Path
import yaml
import os
import asyncio
from pathlib import Path
from openai import AsyncOpenAI


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
        return os.environ.get(key)


class LLMCaller:
    def __init__(self, config: GlobalConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config.api_key,
        )

    async def call_llm(self, model_name, prompt, image_path=None):
        model_cfg = self.config.models[model_name]
        params = {
            "model": model_cfg["name"],
            "temperature": model_cfg.get("temperature", 0.5),
            "max_tokens": model_cfg.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}],
        }
        if image_path:
            # 画像ファイルをバイナリとして読み込み
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            # 画像をLLMに渡す場合の追加処理（API仕様に応じて調整）
            params["messages"][0]["image"] = img_bytes

        completion = await self.client.chat.completions.create(**params)
        return completion.choices[0].message.content


async def main():
    print("starting...")
    config = GlobalConfig(".\\llm\\model_configs.yaml", ".env")
    llm = LLMCaller(config)

    nums = ["移民", 300, "大臣", "LGBTQ", "神"]
    prompts = [
        f"{i} について日本での特別な意味、古代での意味などを答えて。話題に合わせて100文字から500文字で簡潔だが詳細に" for i in nums]
    model_name = "gem2f-chat-ja"

    async def run_one(prompt):
        start = time.perf_counter()
        result = await llm.call_llm(model_name, prompt)
        end = time.perf_counter()
        duration = end - start
        return prompt, result, duration

    tasks = [asyncio.create_task(run_one(p)) for p in prompts]
    for coro in asyncio.as_completed(tasks):
        prompt, result, duration = await coro
        print(
            f"Prompt: {prompt}\nResult: {result}\nDuration: {duration:.2f}秒\n")


if __name__ == "__main__":
    asyncio.run(main())
