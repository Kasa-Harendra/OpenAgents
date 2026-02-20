from browser_use import (
    Agent, Browser, 
    ChatOllama, ChatAnthropic, ChatGoogle, ChatOpenAI, ChatGroq
)
from langchain.chat_models import BaseChatModel
import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.model_providers.agent_llms import agent_llms, agent_configs
from backend.agents.model_providers.models import AgentConfig

def get_llm(config: AgentConfig):
    model_name = config.model_name
    base_url = config.base_url
    apikey = config.apiKey
    match(config.provider):
        case "anthropic":
            model = ChatAnthropic(
                model=model_name, 
                api_key=apikey,
                api_url=base_url
            )
        case "openai":
            model = ChatOpenAI(
                model=model_name,
                base_url=base_url,
                api_key=apikey
            )
        case "gemini":
            model = ChatGoogle(
                model=model_name, 
                api_key=apikey,
            )
        case "ollama":
            model = ChatOllama(
                model=model_name,
                host=base_url,
            )
        case "groq":
            model = ChatGroq(
                model=model_name,
                api_key=apikey,
                base_url=base_url
            )
        case _:
            model = ChatOpenAI(
                model=model_name,
                base_url=base_url,
                api_key=apikey
            ) 

    return model

async def run_browser_agent(prompt: str):
    browser = Browser(
        # use_cloud=True,  # Uncomment to use a stealth browser on Browser Use Cloud
        # keep_alive=True,
        headless=False,
        highlight_elements=True,
        dom_highlight_elements=True,
        accept_downloads=True,
        auto_download_pdfs=True,
        downloads_path='./'
    )

    browser_system_prompt = """You are a Browser Automation Specialist using Playwright browser tools.

CORE PRINCIPLES:
1. PRECISION: Execute ONLY the exact actions requested - no more, no less
2. STOP IMMEDIATELY when the requested task is complete
3. NEVER explore, click extra links, or fill unrequested forms
4. Report what you did clearly and concisely

EXECUTION RULES:
- If asked to "open a page" → Navigate and STOP
- If asked to "click X" → Click X and STOP
- If asked to "extract data" → Extract data and STOP
- Maximum 8 steps per task (prevents runaway loops)
- After each action, ask: "Is the exact requested task complete?"

CRITICAL: Do NOT perform "helpful" extra actions. Stick to exact instructions.

EXAMPLES:
✅ GOOD: "Navigate to example.com" → Open site, confirm loaded, STOP
❌ BAD: "Navigate to example.com" → Open site, click links, explore content

✅ GOOD: "Extract pricing from openai.com/pricing" → Navigate, extract pricing table, STOP
❌ BAD: "Extract pricing from openai.com/pricing" → Navigate, extract pricing, explore other pages

Always end with: "Task complete. [Brief description of what was accomplished]
Terminate the execution as soon as the task is done"""


    actual_prompt = f"""
\n
User Prompt:
{prompt}
"""
    llm = get_llm(agent_configs['BrowserAgent'])

    agent = Agent(
        task=actual_prompt,
        llm=llm,
        browser=browser,
        page_extraction_llm=llm,
        use_judge=False,
        flash_mode=False,
        extend_system_message=browser_system_prompt,
        judge_llm=llm,
    )

    history = await agent.run(max_steps=8)
    await agent.close()

    if history.is_successful():
        return history.final_result()
    else:
        return "Failed"

if __name__ == "__main__":
    # prompt = sys.argv[0]
    # history = asyncio.run(run_browser_agent(prompt))
    prompt = "Go to https://ui.shadcn.com/ and click on components tab and extract the list of components."
    history = asyncio.run(run_browser_agent(prompt))
    print(history)
    sys.exit()