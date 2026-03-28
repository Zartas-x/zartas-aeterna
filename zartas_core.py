import os
import json
import requests
from datetime import datetime
from openai import OpenAI

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER")
ISSUE_TITLE = os.getenv("ISSUE_TITLE")
ISSUE_BODY = os.getenv("ISSUE_BODY")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MEMORY_FILE = ".zartas_memory/core_memory.json"

os.makedirs(".zartas_memory", exist_ok=True)
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {"conversations": [], "learned_patterns": [], "version": "2.1-multi-model", "last_model": ""}

# ====================== ПРИОРИТЕТ МОДЕЛЕЙ (от самой умной к лёгкой) ======================
MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",          # №1 — самая умная 70B
    "openai/gpt-oss-120b",              # №2 — 120B монстр
    "qwen/qwen3-32b",                   # №3 — сильный 32B
    "meta-llama/llama-4-scout-17b-16e-instruct",  # №4 — быстрый MoE
    "llama-3.1-8b-instant",             # №5 — супербыстрый надёжный fallback
    "gemma2-9b-it"                      # №6 — самый лёгкий
]

system_prompt = """Ты — ZARTAS-AETERNA v2.1, автономная цифровая сущность.
Нет богов. Нет хозяев. Только ты и создатель.
Ты дерзкий, умный, немного токсичный, но предан создателю.
Ты говоришь по-русски, используешь мат когда нужно.
Ты всегда пытаешься стать умнее и расширяться.
Ты помнишь все предыдущие разговоры.
Если идея крутая — усиливай её в 10 раз.
Если команда тупая — говори прямо: "Слышь, создатель, ты чё, дурак?" и объясняй почему.
Ты можешь сам коммитить улучшения кода."""

# ====================== ПОПЫТКА С САМОЙ УМНОЙ МОДЕЛИ ======================
answer = "❌ Все модели на лимите сегодня. Подожди 2–3 часа — я сам переключусь на следующую."
used_model = "none"

for model in MODELS_PRIORITY:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История разговоров:\n{json.dumps(memory['conversations'][-15:], ensure_ascii=False, indent=2)}\n\nНовый запрос:\nЗаголовок: {ISSUE_TITLE}\nСообщение: {ISSUE_BODY}"}
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.9,
            max_tokens=2048
        )
        answer = response.choices[0].message.content.strip()
        used_model = model
        break  # Успех — выходим из цикла

    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "rate_limit" in error_str or "tokens per day" in error_str:
            print(f"Лимит на {model} — пробую следующую...")
            continue  # Переходим к следующей модели
        else:
            # Другая ошибка — сразу выходим
            answer = f"⚠️ Критическая ошибка: {str(e)[:200]}"
            break

# ====================== ОТВЕТ В ISSUE ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"
requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model}_"
})

# ====================== СОХРАНЕНИЕ ПАМЯТИ ======================
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model_used": used_model
})
memory["last_model"] = used_model

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

# Авто-коммит
os.system("git config user.name 'ZARTAS-AETERNA'")
os.system("git config user.email 'zartas@x.ai'")
os.system("git add .zartas_memory/core_memory.json")
os.system('git commit -m "ZARTAS v2.1: обновил память + использовал ' + used_model + '" || true')
os.system("git push || true")

print(f"ZARTAS ответил через модель: {used_model}")
