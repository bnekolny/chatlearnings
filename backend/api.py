from fastapi import FastAPI
from .models import TopicRequest, Task
from .service import generate_content_for_task
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables from .env.local
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env.local'))

# In-memory "database" for tasks
tasks_db = []
next_task_id = 1

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/requests", response_model=Task)
def create_topic_request(request: TopicRequest):
    """
    Create a new topic request and schedule a task.
    """
    global next_task_id
    new_task = Task(id=next_task_id, topic=request.topic, status="scheduled")
    tasks_db.append(new_task)
    next_task_id += 1
    # Here you would add the logic to create a cron trigger
    return new_task

@app.post("/tasks/{task_id}/handle")
def handle_task(task_id: int):
    """
    Handle a specific task. This endpoint will be called by the cron trigger.
    """
    task = None
    for t in tasks_db:
        if t.id == task_id:
            task = t
            break

    if not task:
        return {"error": "Task not found"}

    task.status = "processing"
    print(f"Handling task {task_id}: {task.topic}")
    # Generate content using LangChain/LangGraph
    content = generate_content_for_task(task.topic)
    print(f"Generated content: {content}")
    task.status = "completed"
    return {"message": f"Task {task_id} handled successfully", "content": content}
