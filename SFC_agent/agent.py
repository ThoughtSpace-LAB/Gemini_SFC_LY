"""
SFC Agent - 小六壬排盘解卦系统
这是 ADK 的入口文件，定义 root_agent
"""

import os
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from SFC_agent.tools.paipan_tool import calculate_hexagram
from SFC_agent.agents.intent_agent import create_intent_agent
from SFC_agent.agents.team_lead import create_team_lead_agent

# 从环境变量读取模型配置
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")

# ADK 会寻找名为 root_agent 的变量
root_agent = create_team_lead_agent(model_client=None, model_name=AGENT_MODEL)
