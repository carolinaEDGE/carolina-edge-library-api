from pydantic import BaseModel, Field
from typing import Optional, Literal

class Edge5Input(BaseModel):
    drill_id: Optional[str] = None
    age: Optional[str] = None
    level: Optional[str] = None
    total_players: int = Field(ge=1)
    active_players: int = Field(ge=0)
    ice_space: Optional[str] = None
    goalies: Optional[int] = Field(default=None, ge=0)
    fun_challenging: bool
    age_appropriate: bool
    game_like_context: bool
    decisions: bool
    decision_cues: Optional[str] = None
    decision_options: Optional[str] = None
    coach_awareness: Optional[str] = None
    recommended_adjustment: Optional[str] = None
    context_notes: Optional[str] = None

class UserDrillCreate(BaseModel):
    owner_key: str
    title: str
    based_on_drill_id: Optional[str] = None
    game_problem: Optional[str] = None
    objective: Optional[str] = None
    age: Optional[str] = None
    level: Optional[str] = None
    players: Optional[int] = None
    goalies: Optional[int] = None
    ice: Optional[str] = None
    duration: Optional[int] = None
    setup: Optional[str] = None
    how_it_runs: Optional[str] = None
    constraints: Optional[str] = None
    coaching_cues: Optional[str] = None
    goalie_focus: Optional[str] = None
    safety_notes: Optional[str] = None
    decision_cues: Optional[str] = None
    decision_options: Optional[str] = None
    edge_evaluation_id: Optional[str] = None
    user_notes: Optional[str] = None

class PracticeSegmentCreate(BaseModel):
    segment_number: int = Field(ge=1)
    start_minute: Optional[int] = Field(default=None, ge=0)
    duration: Optional[int] = Field(default=None, ge=0)
    activity_source: Optional[str] = None
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None
    purpose: Optional[str] = None
    players_active: Optional[int] = Field(default=None, ge=0)
    players_total: Optional[int] = Field(default=None, ge=1)
    goalie_role: Optional[str] = None
    setup_notes: Optional[str] = None
    segment_notes: Optional[str] = None

class UserPracticeCreate(BaseModel):
    owner_key: str
    title: str
    primary_game_problem: Optional[str] = None
    age: Optional[str] = None
    level: Optional[str] = None
    players: Optional[int] = None
    goalies: Optional[int] = None
    coaches: Optional[int] = None
    ice: Optional[str] = None
    total_minutes: Optional[int] = None
    objective: Optional[str] = None
    edge_notes: Optional[str] = None
    user_notes: Optional[str] = None
    segments: list[PracticeSegmentCreate] = []

class ContributionCreate(BaseModel):
    owner_key: str
    content_type: Literal['drill','practice']
    user_content_id: str
    contribution_consent: bool
    notes: Optional[str] = None
