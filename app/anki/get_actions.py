import requests
import json

def get_supported_actions():
    payload = {
        "action": "apiReflect",
        "version": 6,
        "params": {
            "scopes": ["actions"],
            "actions": None
        }
    }
    response = requests.post("http://localhost:8765", json=payload)
    response.raise_for_status()
    result = response.json()
    if result.get("error"):
        raise Exception(f"AnkiConnect APIエラー: {result['error']}")
    return result["result"]["actions"]

if __name__ == "__main__":
    save = "anki/anki_connect_actions.json"
    try:
        supported_actions = get_supported_actions()
        with open(save, "w", encoding="utf-8") as f:
            json.dump(supported_actions, f, indent=2, ensure_ascii=False)
        print("サポートされているaction一覧を anki_connect_actions.json に保存しました。")
    except Exception as e:
        print("エラー:", e)
