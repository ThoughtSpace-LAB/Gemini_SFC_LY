from google.adk import Agent
from google.genai import types

def create_expert_normal_agent(model_client=None, model_name="gemini-2.5-flash"):
    try:
        with open("SFC_agent/prompt/expert_normal.md", "r", encoding="utf-8") as f:
            base_instruction = f.read()
    except FileNotFoundError:
        base_instruction = "你是一个专业的内容润色专家。"

    instruction = f"""{base_instruction}

## 任务执行
该 Agent 会接收一段包含专业术语的六爻卦象解读（JSON格式）。
请将其重写为通俗易懂的教授口吻回复，严格遵守 expert_normal.md 中的格式要求。
"""

    agent = Agent(
        model=model_name,
        instruction=instruction,
        name="expert_normal_agent",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,  # 润色需要文采，稍微高一点温度
        )
    )
    return agent
