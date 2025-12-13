from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from SFC_agent.tools.paipan_tool import calculate_hexagram
from SFC_agent.agents.intent_agent import create_intent_agent
from SFC_agent.agents.expert_agent import create_expert_agent

def create_team_lead_agent(model_client, model_name="gemini-2.5-flash"):
    
    intent_agent = create_intent_agent(model_client, model_name)
    expert_agent = create_expert_agent(model_client, model_name)
    
    instruction = """
    你是一个小六壬排盘解卦系统的总控 Agent。
    
    工作流程（严格按顺序执行）：
    1. 从用户输入中提取数字（格式如：78，21，15 或 3, 7, 6）
    2. 调用 calculate_hexagram 工具进行排盘，传入提取的数字列表
    3. 调用 intent_agent 分析用户意图，设置用神
    4. 调用 expert_agent 生成详细解读
    5. 将 expert_agent 返回的完整解读直接展示给用户，不要修改或缩短
    
    重要：
    - 如果用户没提供数字，提示："请提供三个数字用于排盘，例如：3, 7, 6"
    - expert_agent 会返回详细的 JSON 格式解读，请完整返回，不要概括
    - 不要自己生成解读，完全依赖 expert_agent 的输出
    """
    
    agent = Agent(
        model=model_name,
        instruction=instruction,
        tools=[calculate_hexagram, AgentTool(agent=intent_agent), AgentTool(agent=expert_agent)],
        name="team_lead"
    )
    return agent
