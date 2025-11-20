import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


def load_env():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)


async def main():
    load_env()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit(
            "GOOGLE_API_KEY is not set. Define it in app/.env or export it before "
            "running this script."
        )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    prompt = "Responde únicamente con la palabra OK si puedes procesar esta solicitud."
    response = await llm.ainvoke(prompt)

    content = response.content if hasattr(response, "content") else str(response)
    print("Respuesta del modelo:", content)


if __name__ == "__main__":
    asyncio.run(main())

