from datetime import date
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import Optional
from pydantic import BaseModel
from backend.storage_service import GCSFactStorage

# Pydantic state schema
class LLMState(BaseModel):
    email_hash: str
    topic_hash: str
    date: str  # ISO 8601 string
    facts: Optional[list] = None
    content: Optional[str] = None
    generated: Optional[bool] = False
    bucket_name: Optional[str] = None

# Define the GCS storage node as a function
def read_facts_node(state):
    storage = GCSFactStorage(state.bucket_name)
    facts = storage.list_facts(state.email_hash, state.topic_hash)
    return {**state.dict(), "facts": facts}

# Define the LLM node as a function
def generate_node(state):
    # Check if a fact for this date already exists
    for fact in (state.facts or []):
        if fact.get("date") == state.date:
            return {**state.dict(), "content": fact["content"], "generated": False}
    # Generate new content
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a polymath, an expert tour guide, historian, and someone with boundless interesting facts."),
        ("human", "Give me a concise (~500 words, only basic formatting) interesting fact about {topic} for a daily read.")
    ])
    chain = prompt | llm
    result = chain.invoke({"topic": state.topic_hash})
    return {**state.dict(), "content": result.content if hasattr(result, "content") else str(result), "generated": True}

def write_fact_node(state):
    if state.generated:
        storage = GCSFactStorage(state.bucket_name)
        storage.write_fact(state.email_hash, state.topic_hash, date.fromisoformat(state.date), state.content)
    return state.dict()

# Build the LangGraph workflow
graph = StateGraph(LLMState)
graph.add_node("read_facts", read_facts_node)
graph.add_node("generate", generate_node)
graph.add_node("write_fact", write_fact_node)
graph.set_entry_point("read_facts")
graph.add_edge("read_facts", "generate")
graph.add_edge("generate", "write_fact")
graph.add_edge("write_fact", END)
workflow = graph.compile()

def generate_content_for_task(email: str, topic: str, date_str: str, bucket_name: str) -> str:
    """
    Orchestrate fact retrieval/generation/storage for a user/topic/date using LangGraph and GCS.
    """
    email_hash = GCSFactStorage.hash_string(email)
    topic_hash = GCSFactStorage.hash_string(topic)
    state = {
        "email_hash": email_hash,
        "topic_hash": topic_hash,
        "date": date_str,
        "bucket_name": bucket_name
    }
    result = workflow.invoke(state)
    return result["content"] if "content" in result else str(result)
