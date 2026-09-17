from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.db_models import PendingAction

router = APIRouter(prefix="/actions", tags=["actions"])

@router.get("/pending")
async def list_pending_actions(db: AsyncSession = Depends(get_db)):
    stmt = select(PendingAction).where(PendingAction.status == "pending").order_by(PendingAction.id.desc())
    res = await db.execute(stmt)
    actions = res.scalars().all()
    return actions

@router.get("/all")
async def list_all_actions(db: AsyncSession = Depends(get_db)):
    stmt = select(PendingAction).order_by(PendingAction.id.desc()).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/simulate")
async def simulate_risky_action(payload: dict = None, db: AsyncSession = Depends(get_db)):
    desc = (payload or {}).get("action_description", "Archive Notion database: 'Q3 Product Roadmap'")
    action = PendingAction(
        session_id="demo_session",
        action_description=desc,
        status="pending"
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action

@router.get("/{action_id}/approve")
async def approve_action(action_id: int, db: AsyncSession = Depends(get_db)):
    action = await db.get(PendingAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "approved"
    await db.commit()
    return {"status": "success", "message": f"Action #{action_id} approved.", "action": action.action_description}

@router.get("/{action_id}/deny")
async def deny_action(action_id: int, db: AsyncSession = Depends(get_db)):
    action = await db.get(PendingAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "denied"
    await db.commit()
    return {"status": "success", "message": f"Action #{action_id} denied.", "action": action.action_description}
