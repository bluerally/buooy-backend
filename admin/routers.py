# routes/admin.py
from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional, Dict, Any

from fastapi.routing import APIRoute
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from feedback.models import Feedback
from common.dependencies import get_admin
from tortoise.expressions import Q

from parties.models import PartyParticipant, Party
from users.models import User
from tortoise.functions import Count

admin_router: APIRouter = APIRouter(
    prefix="/admin", dependencies=[Depends(get_admin)], route_class=APIRoute
)

templates = Jinja2Templates(directory="templates")


@admin_router.get("/feedback")
async def list_feedback(
    request: Request, page: int = 1, search: Optional[str] = None, page_size: int = 20
) -> HTMLResponse:
    query = Feedback.all()

    if search:
        query = query.filter(content__icontains=search)

    total_count = await query.count()
    total_pages = (total_count + page_size - 1) // page_size

    feedbacks = await query.offset((page - 1) * page_size).limit(page_size)

    return templates.TemplateResponse(
        "admin/feedback_list.html",
        {
            "request": request,
            "feedbacks": feedbacks,
            "current_page": page,
            "total_pages": total_pages,
            "search": search or "",
        },
    )


@admin_router.get("/feedback/{feedback_id}")
async def view_feedback(request: Request, feedback_id: int) -> HTMLResponse:
    feedback = await Feedback.get_or_none(id=feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return templates.TemplateResponse(
        "admin/feedback_detail.html",
        {
            "request": request,
            "feedback": feedback,
        },
    )


@admin_router.post("/feedback/{feedback_id}/delete")
async def delete_feedback(feedback_id: int) -> Dict[str, bool]:
    feedback = await Feedback.get(id=feedback_id)
    await feedback.delete()
    return {"success": True}


@admin_router.get("/users")
async def list_users(
    request: Request, page: int = 1, search: Optional[str] = None, page_size: int = 20
) -> HTMLResponse:
    query = User.all()

    if search:
        query = query.filter(
            Q(name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    total_count = await query.count()
    total_pages = (total_count + page_size - 1) // page_size

    # Get users with related counts
    users = (
        await query.annotate(
            organized_parties_count=Count("parties"),
            participated_parties_count=Count("participated_parties"),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return templates.TemplateResponse(
        "admin/user_list.html",
        {
            "request": request,
            "users": users,
            "current_page": page,
            "total_pages": total_pages,
            "search": search or "",
        },
    )


@admin_router.get("/users/{user_id}")
async def view_user(request: Request, user_id: int) -> HTMLResponse:
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get organized parties
    organized_parties = await Party.filter(organizer_user=user).count()

    # Get participated parties
    participated_parties = await PartyParticipant.filter(
        participant_user=user,
        status=1,  # APPROVED status
    ).count()

    # Get certificates
    certificate_levels = await user.certificate_levels.all().prefetch_related(
        "certificate"
    )

    # Get interested sports
    interested_sports = await user.user_interested_sportss.all()

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": user,
            "organized_parties": organized_parties,
            "participated_parties": participated_parties,
            "certificate_levels": certificate_levels,
            "interested_sports": interested_sports,
        },
    )


@admin_router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: int) -> Dict[str, Any]:
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await user.save()
    return {"success": True, "is_active": user.is_active}
