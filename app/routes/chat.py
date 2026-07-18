from fastapi import APIRouter
from app.agent.graph import run_agent
from app import auth

router = APIRouter()

@router.post("/chat")
def post_chat(message: str, token: str):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    try:
        response = run_agent(message, user_id)
        return {"response": response}
    except Exception as e:
        error = str(e)
        if "rate_limit" in error.lower() or "429" in error:
            return {"response": "I'm temporarily unavailable due to rate limits. Please try again in a few minutes."}
        if "tool_use_failed" in error.lower():
            return {"response": "I couldn't process that request. Could you rephrase it with more details?"}
        return {"response": "Something went wrong. Please try again."}
