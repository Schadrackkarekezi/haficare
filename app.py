from dotenv import load_dotenv
import asyncio


load_dotenv()

from interface.main_ui import run_app
from llm.agent import run_agent

if __name__ == "__main__":    
    # run_app()
    asyncio.run(run_agent())
