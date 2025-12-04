import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Load environment variables
load_dotenv()

# Agent configuration
APP_NAME = "luca"
MODEL_ID = "gemini-2.0-flash"

# Create the Gemini agent
agent = Agent(
    name=APP_NAME,
    model=MODEL_ID,
    instruction="You are a helpful AI assistant named Luca. Be concise and friendly in your responses.",
)

# Session service to manage conversation state
session_service = InMemorySessionService()

# Runner to execute the agent
runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: verify API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not set in environment variables")
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="Luca - AI Assistant",
    description="A simple FastAPI app using Google ADK with Gemini",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: str = "default_session"


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str


@app.get("/")
async def root():
    return {"message": "Welcome to Luca AI Assistant!", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the Gemini agent and get a response."""

    # Create or get session
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=request.user_id,
        session_id=request.session_id,
    )

    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=request.user_id,
            session_id=request.session_id,
        )

    # Run the agent
    from google.genai import types

    content = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=request.session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text or ""

    return ChatResponse(
        response=response_text,
        user_id=request.user_id,
        session_id=request.session_id,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
