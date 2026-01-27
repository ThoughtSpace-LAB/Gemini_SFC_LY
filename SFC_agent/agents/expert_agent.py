import json
from google.adk import Agent
from google.genai import types

def create_expert_agent(model_client=None, model_name="gemini-3-flash-preview"):
    try:
        with open("SFC_agent/prompt/expert.md", "r", encoding="utf-8") as f:
            base_instruction = f.read()
    except FileNotFoundError:
        base_instruction = "你是一个小六壬解卦专家。"

    knowledge_str = ""
    rules_text = ""
    try:
        with open("SFC_agent/knowledge/expert_knowledge.md", "r", encoding="utf-8") as f:
            knowledge_str = f.read().strip()
    except FileNotFoundError:
        knowledge_str = ""

    try:
        with open("SFC_agent/knowledge/rules.py", "r", encoding="utf-8") as f:
            rules_text = f.read().strip()
    except FileNotFoundError:
        rules_text = ""

    if "{用神知识}" in base_instruction:
        base_instruction = base_instruction.replace("{用神知识}", "（详见静态知识库）")

    instruction = f"""{base_instruction}

## 任务说明
从 Session State 读取以下参数：
- hexagram_chart: 卦象排盘数据（字典结构），包含：
    - date_info: 起卦时间与日柱干支
    - main_hexagram: 本卦详情（卦名、所属宫位）
        - lines: 本卦六爻列表（包含：六神、伏神、飞神、世应位置、纳甲干支、六亲、动静状态）
    - changed_hexagram: 变卦详情（卦名）
        - lines: 变卦六爻列表（包含：纳甲干支、六亲）
- focus_liu_qin: 用户关注的用神（如"官鬼,父母,我"）

## 解卦步骤
1. 分析用户问题：理解用户真实关切
2. 整理用神信息：列出每个用神对应的问题
3. 详细解读：根据落宫+六神+用神，逐一分析（每个用神至少150字）
4. 实用建议：给出3-5条具体可行的建议
5. 正能量鼓励：引用历史典故或名言

## 输出要求
必须严格按照以下格式输出（不要省略任何字段）：
{{
"问题拆解":"详细分析用户问题，至少100字",
"用神信息":["用神1：XX代表XX，落XX宫配XX神","用神2：..."],
"解读":"详细解读，结合落宫和六神含义，至少300字，要口语化",
"建议":"具体建议，分点列出，至少150字",
"鼓励":"引用历史典故，至少80字"
}}

## 关键
- 解读要详细、深入、口语化
- 每个用神都要结合其落宫和六神进行分析
- 建议要具体、可操作
- 总字数不少于600字
"""

    static_instruction = None
    if knowledge_str or rules_text:
        static_parts = []
        if knowledge_str:
            static_parts.append(
                "以下为小六壬解卦相关静态知识库，"
                "用于解卦分析与用神判断参考：\n\n"
                f"{knowledge_str}"
            )
        if rules_text:
            static_parts.append(
                "\n\n以下为规则与术语补充（来自 knowledge/rules.py）：\n\n"
                f"{rules_text}"
            )
        static_instruction = types.Content(
            role="user",
            parts=[
                types.Part(
                    text="".join(static_parts)
                )
            ],
        )

    agent = Agent(
        model=model_name,
        instruction=instruction,
        static_instruction=static_instruction,
        name="expert_agent",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.4,  # 解读需要稳定准确，同时保持一定灵活性
        ),
    )
    return agent
