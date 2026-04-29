import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()

def get_free_models():
    api_key = os.getenv("OPENROUTER_API_KEY")
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/models',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            free_models = [m['id'] for m in data['data'] if m['id'].endswith(':free')]
            return free_models
    except Exception as e:
        return [str(e)]

if __name__ == "__main__":
    models = get_free_models()
    for m in models:
        print(m)
