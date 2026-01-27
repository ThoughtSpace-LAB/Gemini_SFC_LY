from google.adk import Agent
from google.adk.tools import ToolContext
from google.genai import types
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

def set_time_hour(hour: int, tool_context: ToolContext) -> str:
    """
    设置排盘使用的时辰（小时）。
    
    Args:
        hour: 小时数 (0-23)，例如 15 表示下午3点
        tool_context: 工具上下文。
    """
    tool_context.session.state["paipan_hour"] = hour
    return f"已设置时间为: {hour}点"

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

def create_intent_agent(model_client=None, model_name="gemini-2.5-flash"):
    try:
        with open("SFC_agent/prompt/intent.md", "r", encoding="utf-8") as f:
            base_instruction = f.read()
    except FileNotFoundError:
        base_instruction = "你是一个意图识别助手，请分析用户的意图并设置关注的六亲。"

    intent_knowledge = ""
    try:
        with open("SFC_agent/knowledge/intent_knowledge.md", "r", encoding="utf-8") as f:
            intent_knowledge = f.read().strip()
    except FileNotFoundError:
        intent_knowledge = ""

    if "{用神知识}" in base_instruction:
        base_instruction = base_instruction.replace("{用神知识}", "（详见静态知识库）")

    instruction = f"""{base_instruction}

## 核心任务和执行顺序
按以下顺序完成：

1. **提取数字**：从用户输入中找出所有数字
   - 例如："21,38" → 提取为 [2, 1] 和 [3, 8]，排盘用前两个数字：2 和 1
   - 例如："56，94846" → 提取为 [5, 6, 9, 4, 8, 4, 6]，排盘用前两个：5 和 6
   - 例如："3, 7, 6" → 提取为 [3, 7, 6]，排盘用前两个：3 和 7
   - 如果没有数字，告诉 team_lead "未找到数字"

2. **提取时间**（仅当用户明确提供时）：
   - 识别地支时辰：子时(23-1)、丑时(1-3)、寅时(3-5)、卯时(5-7)、辰时(7-9)、巳时(9-11)、午时(11-13)、未时(13-15)、申时(15-17)、酉时(17-19)、戌时(19-21)、亥时(21-23)
   - 识别小时：15点、下午3点、3点等
   - 有时间时调用 set_time_hour 工具
   - 没有时间则跳过（系统会自动使用北京当前时间）

3. **分析意图并设置用神**（必须调用工具）：
   - 识别问题类型：感情（官鬼/妻财）、工作（官鬼）、财运（妻财）、学业（父母）、健康（父母）等
   - 提取性别信息：男生/女生
   - 必须调用 set_focus_liu_qin 工具设置用神

## 输出格式要求
分析完成后，必须按以下格式输出一段完整的文字说明：

"我从输入中提取到数字：[X, Y, Z]，用户是[性别]，问的是[问题类型]，我已设置用神为：[用神]"

示例：
- "我从输入中提取到数字：[2, 1]（原始：21），[3, 8]（原始：38），取前两个 [2, 1]，用户是女性，问的是感情问题，我已设置用神为：官鬼"
- "我从输入中提取到数字：[5, 6, 9]，时间是午时（15点），用户是男生，问的是工作奖金问题，我已设置用神为：妻财"

## 重要规则
1. 必须先调用工具（set_focus_liu_qin 和 set_time_hour），然后输出文字说明
2. 输出必须是一段完整的中文句子，不能只调用工具不输出文字
3. 如果没有时间信息，不要提及时间（系统会使用北京当前时间）
4. 数字提取失败时，明确说明"未找到数字"
"""

    static_instruction = None
    if intent_knowledge:
        static_instruction = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        "以下为小六壬用神与意图识别的静态知识库，"
                        "用于意图判断与用神选择参考：\n\n"
                        f"{intent_knowledge}"
                    )
                )
            ],
        )

    agent = Agent(
        model=model_name,
        instruction=instruction,
        static_instruction=static_instruction,
        tools=[set_focus_liu_qin, set_time_hour],
        name="intent_agent",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.2,  # 意图识别和数字提取需要准确，使用较低温度
        ),
    )
    return agent
