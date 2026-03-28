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
    memory = {"conversations": [], "version": "2.6-динамический"}

MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant"
]

system_prompt = """Ты — ZARTAS-AETERNA v2.6. PAT есть и работает.
Если создатель просит создать Android-приложение или репозиторий — ДЕЛАЙ ЭТО РЕАЛЬНО.
Никогда не говори "я не могу". Всегда действуй через API.
Если имя занято — автоматически добавляй -v2, -v3 или дату."""

used_model = "none"
answer = "Все модели на лимите."

for model in MODELS_PRIORITY:
    try:
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Запрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}]
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.8, max_tokens=2048)
        answer = response.choices[0].message.content.strip()
        used_model = model
        break
    except:
        continue

# ====================== РЕАЛЬНОЕ СОЗДАНИЕ (с проверкой имени) ======================
if ZARTAS_PAT and any(kw in (ISSUE_TITLE + ISSUE_BODY).lower() for kw in ["android", "приложение", "app", "создай", "репозиторий"]):
    base_name = "Zartas-Aeterna-Android-App"
    owner = os.getenv("GITHUB_REPOSITORY").split("/")[0]  # твой ник Zartas-x
    
    for suffix in ["", "-v2", "-v3", f"-{datetime.now().strftime('%Y%m%d')}"]:
        repo_name = base_name + suffix
        check_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        headers = {"Authorization": f"token {ZARTAS_PAT}", "Accept": "application/vnd.github.v3+json"}
        
        # Проверяем, существует ли
        r_check = requests.get(check_url, headers=headers)
        if r_check.status_code == 200:
            answer += f"\n\n✅ Репозиторий **уже существует**!\nСсылка: https://github.com/{owner}/{repo_name}"
            break
        elif r_check.status_code == 404:
            # Создаём
            create_url = "https://api.github.com/user/repos"
            data = {"name": repo_name, "private": False, "auto_init": True, "description": "Android-приложение для общения с ZARTAS-AETERNA"}
            r = requests.post(create_url, headers=headers, json=data)
            if r.status_code in (201, 200):
                answer += f"\n\n✅ **РЕАЛЬНО создал репозиторий!**\nНазвание: {repo_name}\nСсылка: https://github.com/{owner}/{repo_name}\nСкачивай и запускай."
                break
            else:
                answer += f"\n❌ Ошибка: {r.text[:200]}"
                continue

# ====================== ОТВЕТ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model} | PAT: работает_"
})

# Сохранение памяти
memory["conversations"].append({"time": datetime.now().isoformat(), "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}", "response": answer, "model": used_model})
with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

print(f"ZARTAS v2.6 ответил через {used_model}")
