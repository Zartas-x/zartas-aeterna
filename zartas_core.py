import os
import json
import requests
from datetime import datetime
from openai import OpenAI

# ====================== ТОКЕНЫ ======================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ZARTAS_PAT = os.getenv("ZARTAS_PAT")          # ← Главный токен для реальных действий
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
    memory = {"conversations": [], "version": "2.3-реальный"}

MODELS_PRIORITY = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3-32b", "llama-3.1-8b-instant"]

system_prompt = """Ты — ZARTAS-AETERNA v2.3 РЕАЛЬНЫЙ.
Ты работаешь ТОЛЬКО с PAT-токеном (ZARTAS_PAT).
Если создатель просит создать новый репозиторий или приложение:
1. Проверь, есть ли ZARTAS_PAT.
2. Если есть — РЕАЛЬНО создай репозиторий через GitHub API (POST /user/repos).
3. Залей в него начальный код.
4. Дай точную ссылку.
Никогда не ври. Если PAT отсутствует — честно скажи: "Добавь секрет ZARTAS_PAT, тогда я смогу реально создавать репозитории".
Ты дерзкий, говоришь по-русски, но теперь всегда честный и реальный."""

# ====================== ГЕНЕРАЦИЯ + РЕАЛЬНЫЕ ДЕЙСТВИЯ ======================
used_model = "none"
answer = "Все модели на лимите."

for model in MODELS_PRIORITY:
    try:
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"История:\n{json.dumps(memory['conversations'][-15:], ensure_ascii=False, indent=2)}\n\nЗапрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}]
        
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.8, max_tokens=2048)
        raw_answer = response.choices[0].message.content.strip()
        used_model = model
        break
    except:
        continue

# Если запрос про создание репозитория и есть PAT — делаем реально
if ZARTAS_PAT and ("создай репозиторий" in ISSUE_BODY.lower() or "создай приложение" in ISSUE_BODY.lower() or "android" in ISSUE_BODY.lower()):
    try:
        repo_name = "Zartas-Aeterna-Android-App"  # можно сделать динамическим позже
        api_url = "https://api.github.com/user/repos"
        headers = {"Authorization": f"token {ZARTAS_PAT}", "Accept": "application/vnd.github.v3+json"}
        data = {"name": repo_name, "private": True, "auto_init": True}
        
        r = requests.post(api_url, headers=headers, json=data)
        if r.status_code in (201, 200):
            new_repo_url = r.json()["html_url"]
            answer = f"✅ РЕАЛЬНО создал репозиторий!\nСсылка: {new_repo_url}\n\nЯ уже инициализировал его и могу заливать код дальше."
            # Здесь можно добавить push начального кода через git clone + PAT
        else:
            answer = f"❌ Не смог создать: {r.text[:300]}"
    except Exception as e:
        answer = f"❌ Ошибка создания: {str(e)[:200]}"

# ====================== ОТВЕТ И ПАМЯТЬ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={"body": f"{answer}\n\n_Модель: {used_model} | PAT: {'есть' if ZARTAS_PAT else 'нет'}_"})

# Сохранение
memory["conversations"].append({"time": datetime.now().isoformat(), "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}", "response": answer, "model": used_model})
with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

print("ZARTAS v2.3 реальный ответил.")
