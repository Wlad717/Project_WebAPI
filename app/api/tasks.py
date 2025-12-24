from fastapi import APIRouter, BackgroundTasks
from app.background import update_currency_rates
from app.schemas import TaskResponse  

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/run", response_model=TaskResponse)
async def run_currency_update(background_tasks: BackgroundTasks):
    """Принудительно запустить обновление курсов валют"""
    
    async def run_task():
        await update_currency_rates()
    
    background_tasks.add_task(run_task)
    
    return {
        "message": "Задача обновления курсов запущена",
        "status": "processing"
    }