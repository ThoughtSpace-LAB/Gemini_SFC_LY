"""
SFC Agent - 小六壬排盘解卦系统
这是 ADK 的入口文件，定义 root_agent
"""

import os
from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from SFC_agent.agents.team_lead import create_team_lead_agent

# 从环境变量读取模型配置
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")

# ADK 会寻找名为 root_agent 的变量
root_agent = create_team_lead_agent(model_client=None, model_name=AGENT_MODEL)

# 启用 Context Caching，缓存静态知识上下文以减少 token 和提升响应
app = App(
	name="SFC_agent",
	root_agent=root_agent,
	context_cache_config=ContextCacheConfig(
		cache_intervals=20,
		ttl_seconds=3600,
		min_tokens=0,
	),
)
