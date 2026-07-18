# LiteLLM NVIDIA NIM Proxy

本地代理服务，聚合多个 NVIDIA NIM API Key 实现自动轮换，基于 [LiteLLM](https://github.com/BerriAI/litellm) 构建。

Local proxy that pools multiple NVIDIA NIM API keys with automatic rotation, built on [LiteLLM](https://github.com/BerriAI/litellm).

---

## 目录结构 / Directory Structure

```
LLM-API-Key-Proxy/
├── config_litellm.yaml       # 自动生成，勿手动编辑
├── .env_litellm.example      # Key 模板 确保填入API后修改成.env_litellm
├── .gitignore                # 忽略 .env_litellm 和 config_litellm.yaml
├── update_models.py          # 拉取模型 + 生成 yaml 的核心脚本
├── update_models.bat         # 调用 update_models.py
├── start_litellm.bat         # 启动代理
├── stop_litellm.bat          # 停止代理并释放端口
├── free_port.ps1             # 端口卡住时强制释放
└── config.toml               # Codex CLI 配置
```

---

## 前置要求 / Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/) 下载安装
- **NVIDIA NIM API Key** — 从 [build.nvidia.com](https://build.nvidia.com) 获取，建议申请多个
- **Git** — 版本管理

---

## 安装 / Installation

### 1. 安装依赖 / Install dependencies

```bash
# 将 X:\miniconda3 换成你自己的 Python 路径
# Replace X:\miniconda3 with your own Python path
X:\miniconda3\Scripts\pip install litellm pyyaml
```

### 2. 配置 Key / Configure your keys

```bash
copy .env_litellm.example .env_litellm
```

编辑 `.env_litellm`，填入你的 Key：

```env
NVIDIA_NIM_API_KEY_1=nvapi-your-first-key
NVIDIA_NIM_API_KEY_2=nvapi-your-second-key
LITELLM_MASTER_KEY=sk-your-random-key
```

> **生成 `LITELLM_MASTER_KEY`：**
> ```bash
> python -c "import secrets; print('sk-' + secrets.token_hex(16))"
> ```

### 3. 拉取模型列表 / Fetch model list

```bash
update_models.bat
```

### 4. 启动 / Start

```bash
start_litellm.bat
```

服务运行在 `http://127.0.0.1:5000`，按 `Ctrl+C` 停止。

---

## 工作原理 / How It Works

### 调用链 / Call chain

```
start_litellm.bat
  → litellm.exe
  → Python 解释器
  → litellm 库
  → 加载 config_litellm.yaml
  → 启动 uvicorn，监听 127.0.0.1:5000
```

`litellm.exe` 是 pip 安装时生成的入口脚本，会找到同目录下的 Python 并运行 litellm 库代码。

### Key 轮换 / Key rotation

`config_litellm.yaml` 里每个模型对应 N 条 deployment，每条用不同的 Key：

```
nvidia_nim/01-ai_yi-large   → NVIDIA_NIM_API_KEY_1
nvidia_nim/01-ai_yi-large   → NVIDIA_NIM_API_KEY_2
nvidia_nim/deepseek-v4-pro  → NVIDIA_NIM_API_KEY_1
nvidia_nim/deepseek-v4-pro  → NVIDIA_NIM_API_KEY_2
```

`model_name` 相同的条目会被 LiteLLM 自动归入同一个轮询池：优先用配额剩余多的 Key（usage-based-routing），某个 Key 报错或限流时自动切换到下一个。

### 调用示例 / Example request

```bash
curl http://127.0.0.1:5000/v1/chat/completions \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia_nim/meta_llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 脚本说明 / Scripts

| 文件 | 说明 |
|---|---|
| `start_litellm.bat` | 启动代理服务 |
| `stop_litellm.bat` | 停止服务并释放端口 |
| `update_models.bat` | 拉取最新模型列表，重新生成 `config_litellm.yaml` |
| `free_port.ps1` | 强制释放端口（被 `stop_litellm.bat` 调用） |

---

## 修改端口 / Change Port

如果 `5000` 端口被占用，改这两处：

1. `start_litellm.bat` 里的 `--port 5000`
2. `config.toml` 里的 `base_url = "http://127.0.0.1:5000"`

---

## 版本控制 / Git

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin master
```

`.gitignore` 已排除 `.env_litellm`（真实 Key）和 `config_litellm.yaml`（自动生成，含 Key 引用）。

---

## 备注 / Notes

- **加 Key**：在 `.env_litellm` 里继续加 `_3`、`_4`...，重新跑一次 `update_models.bat` 即可生效


关于添加新的API KEY
方案一：全新启动（推荐）
1. 修改 .env_litellm（加 key）
2. 执行 update_models.bat（生成新 config）
3. 启动 start_litellm.bat

方案二：运行中更新
1. 修改 .env_litellm
2. 执行 stop_litellm.bat（停止服务）
3. 执行 update_models.bat（生成新 config）
4. 启动 start_litellm.bat

- **同步模型**：定期跑 `update_models.bat`，保持模型列表和 NVIDIA NIM 最新状态一致
