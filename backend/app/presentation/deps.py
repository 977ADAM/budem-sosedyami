"""FastAPI dependencies for application services."""

from typing import Annotated

from fastapi import Depends, Request

from app.application.agent_service import AgentService


def get_agent_service(request: Request) -> AgentService:
    """The service is wired in `app.main`; a missing one is a wiring bug."""
    agent_service = getattr(request.app.state, "agent_service", None)
    if not isinstance(agent_service, AgentService):
        raise RuntimeError("agent_service is not configured")
    return agent_service


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


def check_rate_limit(request: Request) -> None:
    """Apply this application's chat limit before running the handler."""
    request.app.state.check_rate_limit(request=request)
