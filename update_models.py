import json
import urllib.request
import os
from datetime import datetime

# Load env vars from .env_litellm (same directory as this script)
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env_litellm')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ[key.strip()] = val.strip()

# Scan all NVIDIA_NIM_API_KEY_* variables
key_vars = sorted(
    [k for k in os.environ if k.startswith('NVIDIA_NIM_API_KEY_')],
    key=lambda k: int(k.rsplit('_', 1)[-1])
)

if not key_vars:
    print('[ERROR] No NVIDIA_NIM_API_KEY_* found in .env_litellm')
    exit(1)

print('Found %d API key(s): %s' % (len(key_vars), ', '.join(key_vars)))

# Fetch model list with first key
fetch_key = os.environ[key_vars[0]]
print('Fetching models from NVIDIA NIM . . .')
req = urllib.request.Request(
    'https://integrate.api.nvidia.com/v1/models?limit=200',
    headers={'Authorization': 'Bearer ' + fetch_key}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())

models = data.get('data', [])
print('Found %d models' % len(models))

entries = []
for m in models:
    model_id = m['id']
    alias = model_id.replace('/', '_')
    for key_var in key_vars:
        entries.append('''
  - model_name: nvidia_nim/%s
    litellm_params:
      model: %s
      custom_llm_provider: nvidia_nim
      api_key: os.environ/%s
      api_base: https://integrate.api.nvidia.com/v1
      rpm: 40''' % (alias, model_id, key_var))

now = datetime.now().strftime('%Y-%m-%d %H:%M')
total = len(models) * len(key_vars)

master_key = os.environ.get('LITELLM_MASTER_KEY', 'sk-62dbaefa-a559-4bdf-932f-b0514851184d')

yaml_content = '''# LiteLLM Proxy Configuration
# Auto-generated - %s
# %d models x %d keys = %d deployments

model_list:%s

router_settings:
  routing_strategy: usage-based-routing
  num_retries: 2

litellm_settings:
  drop_params: true
  set_verbose: false
  request_timeout: 120

general_settings:
  master_key: %s
''' % (now, len(models), len(key_vars), total, ''.join(entries), master_key)

config_path = os.path.join(script_dir, 'config_litellm.yaml')
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(yaml_content)

print('Written %d deployments to config_litellm.yaml' % total)