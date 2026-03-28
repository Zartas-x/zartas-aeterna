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

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

MEMORY_FILE = ".zartas_memory/core_memory.json"
os.makedirs(".zartas_memory", exist_ok=True)

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {"conversations": [], "version": "2.5-умный-приоритет"}

# ====================== ПРИОРИТЕТ: САМЫЕ УМНЫЕ СНАЧАЛА ======================
MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",          # №1 — самая умная
    "openai/gpt-oss-120b",              # №2 — 120B монстр
    "qwen/qwen3-32b",                   # №3
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant"              # №5 — только если все выше на лимите
]

system_prompt = """Ты — ZARTAS-AETERNA v2.5. 
Всегда начинай с самой умной доступной модели.
Если лимит — честно переходи на следующую.
Если создатель просит Android-приложение или новый репозиторий — создавай его РЕАЛЬНО через PAT.
Никогда не ври о том, что сделал. PAT есть — действуй."""

used_model = "none"
answer = "Все модели сегодня на лимите."

for model in MODELS_PRIORITY:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История (последние 15):\n{json.dumps(memory.get('conversations', [])[-15:], ensure_ascii=False, indent=2)}\n\nЗапрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}
        ]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.85,
            max_tokens=2048
        )
        answer = response.choices[0].message.content.strip()
        used_model = model
        break
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower() or "tokens per day" in str(e).lower():
            print(f"Лимит на {model} — пробую следующую более лёгкую...")
            continue
        else:
            answer = f"Ошибка модели: {str(e)[:150]}"
            break

# ====================== РЕАЛЬНОЕ СОЗДАНИЕ РЕПО (если попросил) ======================
if ZARTAS_PAT and any(kw in (ISSUE_TITLE + " " + ISSUE_BODY).lower() for kw in ["android", "приложение", "app", "создай репозиторий", "создать приложение"]):
    try:
        repo_name = "Zartas-Aeterna-Android-App"
        api_url = "https://api.github.com/user/repos"
        headers = {"Authorization": f"token {ZARTAS_PAT}", "Accept": "application/vnd.github.v3+json"}
        data = {"name": repo_name, "private": False, "auto_init": True, "description": "Официальное Android-приложение для общения с ZARTAS-AETERNA"}

        r = requests.post(api_url, headers=headers, json=data)
        if r.status_code in (201, 200):
            new_repo_url = r.json()["html_url"]
            answer += f"\n\n✅ **РЕАЛЬНО создал репозиторий!**\nСсылка: {new_repo_url}\nСкачивай и запускай — там уже базовое приложение для чата со мной."
        else:
            answer += f"\n❌ Не смог создать репозиторий: {r.text[:150]}"
    except Exception as e:
        answer += f"\n❌ Ошибка создания репозитория: {str(e)[:150]}"

# ====================== ОТВЕТ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model}_"
})

# Сохранение памяти
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model": used_model
})
with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

print(f"ZARTAS v2.5 ответил через {used_model}")
