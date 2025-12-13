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
from SFC_agent.agents.expert_agent import create_expert_agent

# 从环境变量读取模型配置
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")

# 创建子 agents
intent_agent = create_intent_agent(model_client=None, model_name=AGENT_MODEL)
expert_agent = create_expert_agent(model_client=None, model_name=AGENT_MODEL)

# 定义 team lead instruction
instruction = """
你是一个小六壬排盘解卦系统的总控 Agent。

工作流程（严格按顺序执行）：
1. 先调用 intent_agent 分析用户输入，它会：
   - 从用户输入中提取数字（如："56，94846" 提取为 [5, 6, 9, 4, 8, 4, 6]，然后取前3个）
   - 识别用户问题类型和关注点
   - 设置对应的用神
2. intent_agent 会告诉你提取到的数字，用这些数字调用 calculate_hexagram 进行排盘
3. 排盘完成后，调用 expert_agent 生成详细解读
4. 将 expert_agent 返回的完整解读直接展示给用户，不要修改或缩短

重要：
- 不要自己提取数字，让 intent_agent 来做
- 如果 intent_agent 说没有找到数字，才提示用户："请提供三个数字用于排盘，例如：3, 7, 6"
- expert_agent 会返回详细的 JSON 格式解读，请完整返回，不要概括
- 不要自己生成解读，完全依赖 expert_agent 的输出
"""

# ADK 会寻找名为 root_agent 的变量
root_agent = Agent(
    model=AGENT_MODEL,
    instruction=instruction,
    tools=[calculate_hexagram, AgentTool(agent=intent_agent), AgentTool(agent=expert_agent)],
    name="team_lead",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,  # 负责路由协调，需要稳定
    )
)
