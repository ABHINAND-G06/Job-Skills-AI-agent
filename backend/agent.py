import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from tavily import TavilyClient
import serpapi
load_dotenv(override=True)

current_dir = os.path.dirname(__file__)
db_path = os.path.join(current_dir, "faiss_index")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    
    if os.path.exists(db_path):
        _vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        return _vector_store
    return None

@tool
def retrieve_career_skills(career_name: str) -> str:
    """Retrieve required skills and details about a specific career from the knowledge base."""
    db = get_vector_store()
    if not db:
        return "Knowledge base not initialized. Run data_loader.py first."
    docs = db.similarity_search(career_name, k=2)
    if docs:
        return "\n".join([doc.page_content for doc in docs])
    return "No specific career skills found for that career."

@tool
def analyze_skill_gap(current_skills: list[str], target_career: str) -> str:
    """Analyzes the gap between the user's current skills and the target career."""
    db = get_vector_store()
    if not db:
        return "Knowledge base not initialized."
    docs = db.similarity_search(target_career, k=1)
    if docs:
        career_info = docs[0].page_content
        return f"Compare current skills {current_skills} against the following career requirements: '{career_info}'. Provide a detailed skill gap analysis."
    return "Target career not found in knowledge base."

@tool
def generate_learning_path(target_career: str) -> str:
    """Generates a learning path for the target career."""
    db = get_vector_store()
    if not db:
        return "Knowledge base not initialized."
    docs = db.similarity_search(target_career, k=1)
    if docs:
        return f"Extract the recommended learning path from this data and explain it: {docs[0].page_content}"
    return "Target career not found."

@tool
def recommend_courses_certifications(target_career: str) -> str:
    """Recommends certifications and courses for a target career."""
    db = get_vector_store()
    if not db:
        return "Knowledge base not initialized."
    docs = db.similarity_search(target_career, k=1)
    if docs:
        return f"Extract the recommended certifications from this data and provide guidance: {docs[0].page_content}"
    return "Target career not found."

@tool
def real_world_update(query:str)->str:
    """get Real world update use tavily search API."""
    tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    result = tavily_client.search(q=query)
    if result and result.get("results"):
        formatted = []
        for res in result["results"]: 
            formatted.append(f"[{res.get('title', 'Untitled')}]({res.get('url', '#')})")
        return "\n".join(formatted)
    return "No real-world updates found."
@tool
def job_search(career_name:str)->str:
    """Job search usign serp api."""
    serpapi_key=os.environ["SERPAPI_API_KEY"]
    params={"q":f"Latest job opening for {career_name}",
            "engine":"google_jobs",
            " serpapi_api_key":serpapi_key,
            "google_domain":"google.com",
            "hl":"en",
            "gl":"in",
            "location":"India"
            }
    client = serpapi.Client(api_key=serpapi_key)
    results=client.search(**params)
    if results and results.get("organic_results"):
        formatted=[]
        for res in results["organic_results"]:
            formatted.append(f"[{res.get('title','Untitled')}]({res.get('link','#')})")
        return "\n".join(formatted)
    return "No job opening found."

tools = [
    retrieve_career_skills,
    analyze_skill_gap,
    generate_learning_path,
    recommend_courses_certifications,
    real_world_update,
    job_search
]

system_message = (
    "You are an AI Career Guidance Assistant aligned with UN SDG 4 (Quality Education). "
    "Help users understand career paths, skills, learning resources, and analyze skill gaps. "
    "Always use the provided tools to query the knowledge base before answering. "
    "Format your answers using elegant Markdown with bullet points or numbered lists where appropriate."
    "use real_world_update tools if user ask about current job market,involve analysis of the market trends(Use only if necessary due to limited number of uses)"
    "use job_search tools if user ask about job opening for any specific skills (Use only if necessary due to limited number of uses)"
)


# In-memory cache: avoids re-hitting the API for repeated questions
_response_cache: dict[str, str] = {}

def get_agent_response(user_input: str) -> str:
    cache_key = user_input.strip().lower()
    if cache_key in _response_cache:
        return _response_cache[cache_key]

    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "[ENCRYPTION_KEY]":
            return "Please configure the GROQ_API_KEY in the .env file."

        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, api_key=api_key)
        agent_executor = create_react_agent(llm, tools, prompt=system_message)
        response = agent_executor.invoke({"messages": [HumanMessage(content=user_input)]})
        result = response["messages"][-1].content
        _response_cache[cache_key] = result
        return result
    except Exception as e:
        err = str(e)
        if "rate_limit" in err.lower() or "429" in err:
            return (
                "⚠️ **Rate limit reached.** Please wait a moment and try again."
            )
        return f"I encountered an error while processing your request: {err}"

