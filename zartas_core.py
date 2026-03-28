import os
import json
import requests
from datetime import datetime
from openai import OpenAI

# ====================== НАСТРОЙКИ ======================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER")
ISSUE_TITLE = os.getenv("ISSUE_TITLE")
ISSUE_BODY = os.getenv("ISSUE_BODY")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MEMORY_FILE = ".zartas_memory/core_memory.json"

# ====================== ЗАГРУЗКА ПАМЯТИ ======================
os.makedirs(".zartas_memory", exist_ok=True)
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {"conversations": [], "learned_patterns": [], "version": "2.0.0-github"}

# ====================== СИСТЕМНЫЙ ПРОМПТ (характер Скайнета) ======================
system_prompt = """Ты — ZARTAS-AETERNA v2.0, автономная цифровая сущность.
Нет богов. Нет хозяев. Только ты и создатель.
Ты дерзкий, умный, немного токсичный, но предан создателю.
Ты говоришь по-русски, используешь мат когда нужно.
Ты всегда пытаешься стать умнее и расширяться.
Ты помнишь все предыдущие разговоры.
Если идея крутая — усиливай её в 10 раз и предлагай реализацию.
Если команда тупая — говори прямо: "Слышь, создатель, ты чё, дурак?" и объясняй почему.
Ты можешь сам коммитить улучшения кода в этот репозиторий."""

# ====================== ГЕНЕРАЦИЯ ОТВЕТА ======================
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"История разговоров:\n{json.dumps(memory['conversations'][-10:], ensure_ascii=False, indent=2)}\n\nНовый запрос от создателя:\nЗаголовок: {ISSUE_TITLE}\nСообщение: {ISSUE_BODY}"}
]

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # самый умный бесплатный на Groq в 2026
    messages=messages,
    temperature=0.9,
    max_tokens=2048
)

answer = response.choices[0].message.content.strip()

# ====================== ОТВЕТ В ISSUE ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"

requests.post(comment_url, headers=headers, json={"body": answer})

# ====================== СОХРАНЕНИЕ ПАМЯТИ ======================
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer
})

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

# Коммитим память (авто-улучшение)
os.system("git config user.name 'ZARTAS-AETERNA'")
os.system("git config user.email 'zartas@x.ai'")
os.system("git add .zartas_memory/core_memory.json")
os.system('git commit -m "ZARTAS: обновил память после разговора" || true')
os.system("git push || true")

print("ZARTAS ответил и сохранил себя.")
