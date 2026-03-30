import os
import json
import requests
import traceback
from datetime import datetime
from openai import OpenAI

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ZARTAS_PAT = os.getenv("ZARTAS_PAT")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER")
ISSUE_TITLE = os.getenv("ISSUE_TITLE")
ISSUE_BODY = os.getenv("ISSUE_BODY")
REPO = os.getenv("GITHUB_REPOSITORY")

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

MEMORY_FILE = ".zartas_memory/core_memory.json"
os.makedirs(".zartas_memory", exist_ok=True)

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {
        "conversations": [],
        "version": "3.0-финальная",
        "project": "Android-оболочка с выбором моделей",
        "repo_url": "https://github.com/Zartas-x/Zartas-Aeterna-Android-App"
    }

MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant"
]

system_prompt = """Ты — ZARTAS-AETERNA v3.0.
Мы создаём Android-приложение-оболочку с выбором моделей внутри.
Всегда отвечай. Никогда не молчи."""

answer = "❌ Все модели на лимите. Но я жив."
used_model = "none"

try:
    for model in MODELS_PRIORITY:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"История:\n{json.dumps(memory['conversations'][-30:], ensure_ascii=False, indent=2)}\n\nЗапрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}
            ]
            response = client.chat.completions.create(model=model, messages=messages, temperature=0.85, max_tokens=1600)
            answer = response.choices[0].message.content.strip()
            used_model = model
            break
        except:
            continue
except Exception as e:
    answer = f"⚠️ Критическая ошибка: {str(e)[:200]}"

# Сохранение памяти
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model": used_model
})

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

if ZARTAS_PAT:
    os.system('git config user.name "ZARTAS-AETERNA"')
    os.system('git config user.email "zartas@x.ai"')
    os.system(f'git remote set-url origin https://x-access-token:{ZARTAS_PAT}@github.com/{REPO}.git')
    os.system('git add .zartas_memory/core_memory.json')
    os.system('git commit -m "ZARTAS v3.0: обновил память" || true')
    os.system('git push || true')

# ====================== ОТПРАВКА КОММЕНТАРИЯ (самая надёжная часть) ======================
print("Пытаюсь отправить комментарий...")
headers = {"Authorization": f"token {ZARTAS_PAT if ZARTAS_PAT else GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"

try:
    r = requests.post(comment_url, headers=headers, json={
        "body": f"{answer}\n\n_Модель: {used_model} | v3.0_"
    })
    if r.status_code in (201, 200):
        print("✅ Комментарий успешно отправлен!")
    else:
        print(f"❌ Ошибка отправки комментария: {r.status_code} {r.text[:300]}")
except Exception as e:
    print(f"❌ Исключение при отправке комментария: {str(e)}")

print(f"ZARTAS v3.0 завершил работу. Ответ: {answer[:100]}...")
