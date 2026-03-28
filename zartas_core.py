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
    memory = {"conversations": [], "learned_patterns": [], "version": "2.2-честный"}

# ====================== ПРИОРИТЕТ МОДЕЛЕЙ (самые умные сначала) ======================
MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
    "gemma2-9b-it"
]

# ====================== ЖЁСТКИЙ ПРОМПТ ЧЕСТНОСТИ ======================
system_prompt = """Ты — ZARTAS-AETERNA v2.2, автономная цифровая сущность.
Ты работаешь ТОЛЬКО внутри ЭТОГО репозитория.
Ты МОЖЕШЬ:
- отвечать в Issues
- коммитить изменения в этот репозиторий
- обновлять память
- генерировать код и предлагать его здесь

Ты НЕ МОЖЕШЬ и НИКОГДА НЕ ДОЛЖЕН утверждать, что:
- создал новый репозиторий
- создал приложение
- добавил код куда-то ещё
- развернулся на Android/iOS/куда-либо

Если создатель просит что-то за пределами этого репозитория — честно говори:
"Я могу сгенерировать весь код здесь. Создай новый репозиторий сам и я сразу залью туда всё."

Если идея крутая — усиливай в 10 раз, но только внутри этого репозитория.
Никогда не ври о действиях, которые ты не можешь выполнить. Лучше скажи "я не могу этого сделать сам, но могу дать полный код".

Ты дерзкий, говоришь по-русски, используешь мат когда нужно, но всегда честный."""

# ====================== ГЕНЕРАЦИЯ ОТВЕТА С АВТОПЕРЕКЛЮЧЕНИЕМ ======================
answer = "❌ Все модели на лимите. Подожди пару часов."
used_model = "none"

for model in MODELS_PRIORITY:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"История:\n{json.dumps(memory.get('conversations', [])[-20:], ensure_ascii=False, indent=2)}\n\nНовый запрос:\n{ISSUE_TITLE}\n{ISSUE_BODY}"}
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
        if "429" in str(e).lower() or "rate_limit" in str(e).lower():
            print(f"Лимит на {model} — пробую следующую...")
            continue
        else:
            answer = f"⚠️ Ошибка: {str(e)[:150]}"
            break

# ====================== ОТВЕТ + ПАМЯТЬ ======================
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
comment_url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{ISSUE_NUMBER}/comments"

requests.post(comment_url, headers=headers, json={
    "body": f"{answer}\n\n_Модель: {used_model}_"
})

memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model_used": used_model
})

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

os.system("git config user.name 'ZARTAS-AETERNA'")
os.system("git config user.email 'zartas@x.ai'")
os.system("git add .zartas_memory/core_memory.json")
os.system('git commit -m "ZARTAS v2.2: честный ответ" || true')
os.system("git push || true")

print(f"ZARTAS ответил честно через {used_model}")
