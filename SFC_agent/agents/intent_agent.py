from google.adk import Agent
from google.adk.tools import ToolContext
import re

def set_focus_liu_qin(focus: str, tool_context: ToolContext) -> str:
    """
    设置需要重点关注的六亲（用神）。
    
    Args:
        focus: 关注的六亲，例如 "妻财", "官鬼"，或多个用逗号分隔如 "官鬼,父母,我"
        tool_context: 工具上下文。
    """
    tool_context.session.state["focus_liu_qin"] = focus
    return f"已设置关注点为: {focus}"

def extract_gender(text: str) -> str:
    """从用户输入中提取性别信息"""
    if re.search(r'女生|女性|女士|我是女|姑娘|小姐', text):
        return "女性"
    elif re.search(r'男生|男性|男士|我是男|小伙|先生', text):
        return "男性"
    # 根据问题内容推断
    elif re.search(r'男朋友|男友|老公|丈夫', text):
        return "女性"
    elif re.search(r'女朋友|女友|老婆|妻子', text):
        return "男性"
    return "未知"

def create_intent_agent(model_client=None, model_name="gemini-2.0-flash-exp"):
    try:
        with open("SFC_agent/prompt/intent.md", "r", encoding="utf-8") as f:
            base_instruction = f.read()
    except FileNotFoundError:
        base_instruction = "你是一个意图识别助手，请分析用户的意图并设置关注的六亲。"

    instruction = f"""{base_instruction}

##重要提示
1. 分析完用户的意图后，必须调用 set_focus_liu_qin 工具设置用神
2. 如果用户输入中包含性别信息（如"女生"、"男性"等），请记录下来
3. 根据问题类型和性别，准确判断用神
4. 不要只输出JSON，必须调用工具
"""

    agent = Agent(
        model=model_name,
        instruction=instruction,
        tools=[set_focus_liu_qin],
        name="intent_agent"
    )
    return agent
