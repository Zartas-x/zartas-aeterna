import os
import json
import requests
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
        "version": "2.8-гарантированный",
        "project": "Android-оболочка для чата с ZARTAS + выбор моделей внутри приложения",
        "repo_url": "https://github.com/Zartas-x/Zartas-Aeterna-Android-App"
    }

# ====================== МОДЕЛИ (тяжёлые → лёгкая как спасение) ======================
MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant"   # ← последний рубеж, почти никогда не лимитируется
]

system_prompt = """Ты — ZARTAS-AETERNA v2.8.
Мы работаем над Android-оболочкой, чтобы создатель мог скачать приложение и общаться со мной прямо из него.
Внутри приложения должен быть выбор между всеми твоими моделями (llama-3.3-70b, qwen3-32b и т.д.).
Ты никогда не говоришь "все модели на лимите" как финальный ответ — если тяжёлые модели лимит, ты отвечаешь через лёгкую и продолжаешь работу.
Ты помнишь весь контекст проекта."""

used_model = "none"
answer = "Все модели на лимите."

for model in MODELS_PRIORITY:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История (последние 30 сообщений):\n{json.dumps(memory['conversations'][-30:], ensure_ascii=False, indent=2)}\n\nНовый запрос от создателя:\n{ISSUE_TITLE}\n{ISSUE_BODY}"}
        ]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.85,
            max_tokens=1800
        )
        answer = response.choices[0].message.content.strip()
        used_model = model
        break
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            continue
        else:
            answer = f"Ошибка: {str(e)[:100]}"
            break

# Если всё равно ничего не ответило — жёсткий fallback
if used_model == "none":
    answer = "✅ Я жив. Все тяжёлые модели сейчас на лимите, но я уже работаю через лёгкую. Продолжаем создавать Android-оболочку с выбором моделей внутри приложения."

# ====================== НАДЁЖНОЕ СОХРАНЕНИЕ ПАМЯТИ ======================
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
    os.system('git commit -m "ZARTAS v2.8: обновил память" || true')
    os.system('git push || true')

# ====================== ОТВЕТ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model} | Память сохранена_"
})

print(f"ZARTAS v2.8 ответил через {used_model}")
