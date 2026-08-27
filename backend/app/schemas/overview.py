from pydantic import BaseModel, Field


class RecentCommitSummary(BaseModel):
    id: str
    message: str
    sha: str


class RecentDeploymentSummary(BaseModel):
    id: str
    service_name: str
    status: str


class RecentEventSummary(BaseModel):
    id: str
    message: str
    severity: str


class OverviewResponse(BaseModel):
    repositories: int
    commits: int
    deployments: int
    events: int
    active_incidents: int = 0
    anomalies: int = 0
    high_risk_deployments: int = 0
    recent_commits: list[RecentCommitSummary] = Field(default_factory=list)
    recent_deployments: list[RecentDeploymentSummary] = Field(default_factory=list)
    recent_events: list[RecentEventSummary] = Field(default_factory=list)
