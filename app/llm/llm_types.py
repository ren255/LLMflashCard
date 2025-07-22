from dataclasses import dataclass
import yaml
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


@dataclass
class LLMLiteConfig:
    model: str
    temperature: float
    max_tokens: int

def build_Config(model: str, temperature: float = 0, max_tokens: int = 0) -> LLMLiteConfig:
    config_path = Path("app/llm/model_configs.yaml")
    with open(config_path, "r", encoding="utf-8") as config_file:
        models = yaml.safe_load(config_file)["models"]
        model_conf = models[model]
        return LLMLiteConfig(
            model="openrouter/" + model_conf["name"],
            temperature=temperature if temperature != 0 else model_conf["temperature"],
            max_tokens=max_tokens if max_tokens != 0 else model_conf["max_tokens"],
        )


if __name__ == "__main__":
    print(build_Config("kimi2"))
