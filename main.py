import asyncio, os
import sys
from dotenv import load_dotenv

load_dotenv()

# ✅ Fix event loop issue on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    # ✅ THIS GUARD is required on Windows when using multiprocessing / reload
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(
        "resume_parser_agent:app", host=host, port=os.getenv("PORT", 8000), reload=True
    )
