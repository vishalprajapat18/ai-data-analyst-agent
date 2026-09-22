from langchain_groq import ChatGroq
from app.core.config import GROQ_API_KEY, GROQ_MODEL

def get_llm(temperature: float = 0.0) -> ChatGroq:
    """One place to change the model or provider later."""
    return ChatGroq(model=GROQ_MODEL,
                     api_key=GROQ_API_KEY, 
                     temperature=temperature)