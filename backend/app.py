from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from agent import get_agent_response

app = FastAPI(title="AI Career Guidance Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(frontend_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = get_agent_response(request.message)
        return JSONResponse({"reply": response})
    except Exception as e:
        return JSONResponse({"reply": f"Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
