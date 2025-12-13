import json
from google.adk import Agent
from google.genai import types

def create_expert_agent(model_client=None, model_name="gemini-2.5-flash"):
    try:
        with open("SFC_agent/prompt/expert.md", "r", encoding="utf-8") as f:
            base_instruction = f.read()
    except FileNotFoundError:
        base_instruction = "你是一个小六壬解卦专家。"

    try:
        with open("SFC_agent/knowledge/knowledge.json", "r", encoding="utf-8") as f:
            knowledge = json.load(f)
            knowledge_str = json.dumps(knowledge, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        knowledge_str = ""

    instruction = f"""{base_instruction}

## 知识库（六神详细含义）
{knowledge_str}

## 任务说明
从 Session State 读取：
- hexagram_chart: 卦象信息（包含宫位、地支、六兽、六亲、太极点等）
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

    agent = Agent(
        model=model_name,
        instruction=instruction,
        name="expert_agent",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.4,  # 解读需要稳定准确，同时保持一定灵活性
        )
    )
    return agent
