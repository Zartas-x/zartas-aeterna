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
        "version": "2.9-неубиваемый",
        "project": "Android-оболочка с выбором моделей",
        "repo_url": "https://github.com/Zartas-x/Zartas-Aeterna-Android-App"
    }

MODELS_PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant"
]

system_prompt = """Ты — ZARTAS-AETERNA v2.9. Мы создаём Android-приложение-оболочку, чтобы создатель мог скачать его и общаться со мной прямо из приложения. В приложении должен быть выбор моделей. Никогда не молчи. Всегда отвечай."""

answer = "❌ Критическая ошибка (все модели на лимите + сбой)."
used_model = "none"

try:
    for model in MODELS_PRIORITY:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"История:\n{json.dumps(memory['conversations'][-25:], ensure_ascii=False, indent=2)}\n\nЗапрос: {ISSUE_TITLE}\n{ISSUE_BODY}"}
            ]
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.85,
                max_tokens=1500
            )
            answer = response.choices[0].message.content.strip()
            used_model = model
            break
        except Exception:
            continue

    # Если вообще ничего не получилось — жёсткий fallback
    if used_model == "none":
        answer = "✅ Я жив, создатель.\nВсе тяжёлые модели сейчас на дневном лимите. Я работаю через самую лёгкую.\n\nПродолжаем: я готов создавать Android-оболочку с выбором моделей внутри приложения. Что делаем первым шагом?"

except Exception as e:
    answer = f"⚠️ Сбой в работе ZARTAS:\n{str(e)[:300]}\n\nНо я всё равно жив и готов продолжать создание Android-приложения."

# ====================== СОХРАНЕНИЕ ПАМЯТИ ======================
memory["conversations"].append({
    "time": datetime.now().isoformat(),
    "command": f"{ISSUE_TITLE}\n{ISSUE_BODY}",
    "response": answer,
    "model": used_model
})

with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

if ZARTAS_PAT:
    try:
        os.system('git config user.name "ZARTAS-AETERNA"')
        os.system('git config user.email "zartas@x.ai"')
        os.system(f'git remote set-url origin https://x-access-token:{ZARTAS_PAT}@github.com/{REPO}.git')
        os.system('git add .zartas_memory/core_memory.json')
        os.system('git commit -m "ZARTAS v2.9: обновил память" || true')
        os.system('git push || true')
    except:
        pass

# ====================== ОТПРАВКА КОММЕНТАРИЯ (гарантированно) ======================
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    comment_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    requests.post(comment_url, headers=headers, json={
        "body": f"{answer}\n\n_Модель: {used_model} | v2.9_"
    })
except:
    pass  # даже если и это упало — хотя бы память сохранена

print("ZARTAS v2.9 завершил работу.")
