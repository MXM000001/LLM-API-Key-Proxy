# flatten_namespace_tools.py
#
# 问题:Codex 新版会把工具打包成 {"type": "namespace", "tools": [...]} 这种分组格式,
#      但 NVIDIA NIM 后端(vLLM 引擎)只认平铺的 {"type": "function", "function": {...}}。
#
# 解法:在请求转发给 NVIDIA 之前,拦截 tools 列表,把每个 namespace 分组里
#      嵌套的 function 工具展开成平铺列表,vLLM 就能正常识别了。
#
# 用法:把这个文件放到和 config_litellm.yaml 同一个目录下,
#      然后在 config_litellm.yaml 里加:
#
#      litellm_settings:
#        callbacks: ["flatten_namespace_tools.flatten_namespace_tools"]
#
# 会在每次请求发出前自动生效,不用改任何客户端代码。

from litellm.integrations.custom_logger import CustomLogger

# NVIDIA NIM (vLLM 后端) 不认识、但 drop_params 也拦不住的自定义字段——
# 因为它们不是 LiteLLM 认识的"标准 OpenAI 参数"，drop_params 只对标准参数生效。
# Codex 更新时可能还会冒出新的同类字段，遇到报错就把参数名加进这个列表即可。
STRIP_PARAMS = [
    "client_metadata",
    "reasoning_split",
]


class FlattenNamespaceTools(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        # 清理已知会被 NIM 拒绝、但 drop_params 处理不了的自定义字段
        for key in STRIP_PARAMS:
            data.pop(key, None)

        tools = data.get("tools")
        if not tools:
            return data

        flattened = []
        changed = False

        for tool in tools:
            if isinstance(tool, dict) and tool.get("type") == "namespace":
                # namespace 分组:把里面每个 function 工具原样展开到顶层
                changed = True
                for sub_tool in tool.get("tools", []):
                    if isinstance(sub_tool, dict) and sub_tool.get("type") == "function":
                        flattened.append(sub_tool)
                    elif isinstance(sub_tool, dict) and "function" in sub_tool:
                        flattened.append(sub_tool)
                    # 其他嵌套类型（如果以后出现）先跳过，不强行塞进去报错
            else:
                flattened.append(tool)

        if changed:
            data["tools"] = flattened

        return data


flatten_namespace_tools = FlattenNamespaceTools()
