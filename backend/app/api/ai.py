from fastapi import APIRouter, Depends, Response

from ..agent import run_agent
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..image_gen import generate
from ..llm import parse_requirement
from ..models import User
from ..ratelimit import limiter
from ..schemas import AgentIn, ImageIn, ParseIn

router = APIRouter(tags=["ai"])


@router.post("/ai/parse", dependencies=[Depends(limiter("ai-parse", 30, 60))])
def parse(body: ParseIn, user: User = Depends(get_current_user)):
    spec, source = parse_requirement(body.text)
    return {"spec": spec, "source": source}


@router.post("/ai/image", dependencies=[Depends(limiter("ai-image", 10, 60))])
def image(body: ImageIn, user: User = Depends(get_current_user)):
    content, mode = generate(body.prompt, body.width, body.height, body.negative_prompt, body.seed)
    return Response(
        content=content,
        media_type="image/png",
        headers={"X-Image-Mode": mode, "Content-Disposition": "inline; filename=image.png"},
    )


@router.post("/ai/agent", dependencies=[Depends(limiter("ai-agent", 10, 60))])
def agent(
    body: AgentIn,
    db=Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    return run_agent(db, user, body.message)
