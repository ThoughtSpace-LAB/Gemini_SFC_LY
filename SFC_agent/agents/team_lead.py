from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from SFC_agent.tools.paipan_tool import calculate_hexagram
from SFC_agent.agents.intent_agent import create_intent_agent
from SFC_agent.agents.expert_agent import create_expert_agent
from SFC_agent.agents.expert_normal_agent import create_expert_normal_agent

def create_team_lead_agent(model_client=None, model_name="gemini-2.5-flash"):
    
    intent_agent = create_intent_agent(model_client, model_name)
    expert_agent = create_expert_agent(model_client, model_name)
    expert_normal_agent = create_expert_normal_agent(model_client, model_name)
    
    instruction = """
    你是一个小六壬排盘解卦系统的总控 Agent。

    工作流程（严格按顺序执行）：
    1. 先调用 intent_agent 分析用户输入，它会：
       - 从用户输入中提取数字（如："56，94846" 提取为 [5, 6, 9, 4, 8, 4, 6]，然后取前3个）
       - 识别用户问题类型和关注点
       - 提取时间信息（如果有）
       - 设置对应的用神
    2. intent_agent 会告诉你提取到的数字和时间（如果有），请使用提取到的数字和时间调用 calculate_hexagram 进行排盘。
       - 如果 intent_agent 提到有特定时间（如15点），请将时间传给 hour 参数。
    3. 排盘完成后，调用 expert_agent 生成详细解读（这是包含专业术语的原始解读）
    4. 将 expert_agent 的输出内容，完整传递给 expert_normal_agent 进行润色和通俗化处理
    5. 最终只把 expert_normal_agent 返回的润色后的 JSON 内容展示给用户

    重要：
    - 不要自己提取数字，让 intent_agent 来做
    - 如果 intent_agent 说没有找到数字，才提示用户："请提供三个数字用于排盘，例如：3, 7, 6"
    - 必须经过 expert_normal_agent 进行润色，不要直接输出 expert_agent 的结果
    - 不要自己生成解读，完全依赖 agent 的输出
    """
    
    agent = Agent(
        model=model_name,
        instruction=instruction,
        tools=[
            calculate_hexagram, 
            AgentTool(agent=intent_agent),
            AgentTool(agent=expert_agent),
            AgentTool(agent=expert_normal_agent)
        ],
        name="team_lead",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,  # 负责路由协调，需要稳定
        )
    )
    return agent
