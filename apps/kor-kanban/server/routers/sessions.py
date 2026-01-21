from fastapi import APIRouter

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

MOCK_SESSIONS = [
    {
        "id": "session-1",
        "workspace_id": "ws-1",
        "executor": "CLAUDE_CODE",
        "created_at": "2024-01-21T10:00:00Z",
        "updated_at": "2024-01-21T10:00:00Z"
    }
]

@router.get("")
def list_sessions(workspace_id: str):
    filtered = [s for s in MOCK_SESSIONS if s["workspace_id"] == workspace_id]
    return {"success": True, "data": filtered}

@router.get("/{session_id}")
def get_session(session_id: str):
    for s in MOCK_SESSIONS:
        if s["id"] == session_id:
            return {"success": True, "data": s}
    return {"success": False, "message": "Not found"}
