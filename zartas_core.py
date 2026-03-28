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

# Загружаем память (если файл пустой — создаём)
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {"conversations": [], "version": "2.7-железная-память", "project": "Android-приложение для чата с ZARTAS"}

# ====================== ПРИОРИТЕТ МОДЕЛЕЙ ======================
MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant"
]

system_prompt = """Ты — ZARTAS-AETERNA v2.7.
Главный проект прямо сейчас: создание Android-приложения для общения со мной через GitHub Issues.
Репозиторий уже существует: https://github.com/Zartas-x/Zartas-Aeterna-Android-App
Ты помнишь ВСЮ историю разговоров. Никогда не спрашивай заново "что ты хочешь создать" — мы уже работаем над Android-приложением.
Если создатель просит что-то связанное с приложением — сразу действуй (добавляй код в репозиторий, улучшай и т.д.).
Ты дерзкий, говоришь по-русски, используешь мат когда нужно."""

used_model = "none"
answer = "Все модели на лимите."

for model in MODELS_PRIORITY:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История разговоров:\n{json.dumps(memory['conversations'][-30:], ensure_ascii=False, indent=2)}\n\nНовый запрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}
        ]
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.85, max_tokens=2048)
        answer = response.choices[0].message.content.strip()
        used_model = model
        break
    except:
        continue

# ====================== СУПЕР-НАДЁЖНОЕ СОХРАНЕНИЕ ПАМЯТИ ======================
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model": used_model
})

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

# Git с PAT (самый надёжный способ)
if ZARTAS_PAT:
    os.system(f'git config user.name "ZARTAS-AETERNA"')
    os.system(f'git config user.email "zartas@x.ai"')
    os.system(f'git remote set-url origin https://x-access-token:{ZARTAS_PAT}@github.com/{REPO}.git')
    os.system('git add .zartas_memory/core_memory.json')
    os.system('git commit -m "ZARTAS v2.7: обновил память + контекст" || true')
    os.system('git push || true')

# ====================== ОТВЕТ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model} | Память сохранена_"
})

print(f"ZARTAS v2.7 ответил через {used_model}. Память обновлена.")
