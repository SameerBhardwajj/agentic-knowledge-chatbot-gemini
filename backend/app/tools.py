
from sqlalchemy.orm import Session
from .models import User

GET_CURRENT_USER_PROFILE_TOOL = {
    "name": "get_current_user_profile",
    "description": (
        "Get the profile of the currently authenticated user. "
        "Use it for the user's own name, email, phone, department, job title, or location."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

def get_current_user_profile(db: Session, current_user_id: int) -> dict:
    user = db.get(User, current_user_id)
    if not user:
        return {"found": False}
    return {
        "found": True,
        "user": {
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "department": user.department,
            "job_title": user.job_title,
            "location": user.location,
        },
    }
