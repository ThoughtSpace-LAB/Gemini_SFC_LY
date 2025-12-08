import os
import sys
import asyncio
import warnings
from google.genai import types
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# 过滤 app name mismatch 警告
warnings.filterwarnings("ignore", message=".*App name mismatch.*")

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from SFC_agent.agents.team_lead import create_team_lead_agent

# 使用固定的 app_name
APP_NAME = "Gemini_SFC"

async def run_agent_async(runner, user_id, session_id, user_input):
    """异步运行 agent"""
    new_message = types.Content(role="user", parts=[types.Part(text=user_input)])
    
    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message
    ):
        # 只处理最终的文本响应，忽略 function_call 等中间事件
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    if event.author != "user":
                        final_response = part.text  # 保留最后一个文本响应
    
    return final_response

async def main_async():
    print("初始化小六壬排盘系统...")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("错误: GOOGLE_API_KEY 未设置。")
        print("请设置环境变量: export GOOGLE_API_KEY='your_api_key'")
        return
    
    try:
        # Create the agent team
        team_lead = create_team_lead_agent(None)
        
        # Initialize Session Service
        session_service = InMemorySessionService()
        
        # Create session using async method
        await session_service.create_session(
            app_name=APP_NAME,
            user_id="user_1",
            session_id="session_1"
        )
        
        # Initialize Runner
        runner = Runner(
            agent=team_lead,
            app_name=APP_NAME,
            session_service=session_service
        )
        
        print("\n六爻排盘解卦系统已就绪。")
        print("示例输入: 我想测一下明天的面试，数字是 3, 7, 6")
        
        user_id = "user_1"
        session_id = "session_1"
        
        while True:
            try:
                user_input = input("\n请输入 (输入 'exit' 退出): ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if not user_input.strip():
                    continue
                    
                print("\n正在思考...")
                
                response = await run_agent_async(runner, user_id, session_id, user_input)
                
                print("\n回答:")
                if response:
                    print(response)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_msg = str(e)
                if "User location is not supported" in error_msg:
                    print("\n⚠️  地区限制错误：当前地理位置不支持 Gemini API")
                    print("\n解决方案：")
                    print("1. 使用 VPN 切换到支持的地区（美国、欧洲、日本等）")
                    print("2. 或者使用 Google Cloud Vertex AI")
                    print("3. 检查 API Key 是否正确")
                    break
                else:
                    print(f"\n发生错误: {e}")
                    import traceback
                    traceback.print_exc()
                
    except Exception as e:
        print(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
