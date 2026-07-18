import json
import urllib.request
import os
from datetime import datetime

# 扫描所有 NVIDIA_NIM_API_KEY_1 / _2 / _3 ... 这种变量,自动识别有几个 Key
# 想加 Key 就在 .env_litellm 里继续往下加 _4 _5,不用改这个脚本
key_vars = sorted(
    [k for k in os.environ if k.startswith('NVIDIA_NIM_API_KEY_')],
    key=lambda k: int(k.rsplit('_', 1)[-1])
)

if not key_vars:
    print('[ERROR] No NVIDIA_NIM_API_KEY_N variables found (expected NVIDIA_NIM_API_KEY_1, _2, ...)')
    exit(1)

print('Found %d API key(s): %s' % (len(key_vars), ', '.join(key_vars)))

# 拉模型列表只需要一个能用的 Key,不用每个 Key 都查一遍
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
    # 同一个模型,给每个 Key 各生成一条 deployment,model_name 相同 = 自动进同一个轮询池
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
yaml_content = '''# LiteLLM Proxy Configuration
# Auto-generated from NVIDIA NIM API - %s
# %d models x %d keys = %d deployments

model_list:%s

router_settings:
  routing_strategy: usage-based-routing   # 优先用配额剩余多的 Key
  num_retries: 2                          # 单个 Key 限流/失败自动换下一个重试

litellm_settings:
  drop_params: true
  set_verbose: false
  request_timeout: 120
  callbacks: ["flatten_namespace_tools.flatten_namespace_tools"]

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
''' % (now, len(models), len(key_vars), total, ''.join(entries))

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config_litellm.yaml')
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(yaml_content)

print('Written %d deployments (%d models x %d keys) to config_litellm.yaml' % (total, len(models), len(key_vars)))
