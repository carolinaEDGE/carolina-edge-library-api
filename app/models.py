from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Drill(Base):
    __tablename__ = "drills"
    drill_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    name: Mapped[str] = mapped_column(String(200), index=True)
    review_status: Mapped[str|None] = mapped_column(String(50), nullable=True)
    family: Mapped[str|None] = mapped_column(String(100), index=True)
    primary_game_problem: Mapped[str|None] = mapped_column(String(300), index=True)
    target_behaviors: Mapped[str|None] = mapped_column(Text, nullable=True)
    best_ages: Mapped[str|None] = mapped_column(String(100), nullable=True)
    level: Mapped[str|None] = mapped_column(String(100), nullable=True)
    goalies: Mapped[str|None] = mapped_column(String(50), nullable=True)
    ice_footprint: Mapped[str|None] = mapped_column(String(100), nullable=True)
    setup_summary: Mapped[str|None] = mapped_column(Text, nullable=True)
    how_it_runs: Mapped[str|None] = mapped_column(Text, nullable=True)
    coaching_cues_json: Mapped[str] = mapped_column(Text, default="[]")
    guided_questions_json: Mapped[str] = mapped_column(Text, default="[]")
    constraints_json: Mapped[str] = mapped_column(Text, default="[]")
    why_it_works: Mapped[str|None] = mapped_column(Text, nullable=True)
    search_tags_json: Mapped[str] = mapped_column(Text, default="[]")
    decision_cue_summary: Mapped[str|None] = mapped_column(Text, nullable=True)
    decision_options_summary: Mapped[str|None] = mapped_column(Text, nullable=True)
    game_like_evidence: Mapped[str|None] = mapped_column(Text, nullable=True)
    age_context_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    source_json: Mapped[str] = mapped_column(Text, default="{}")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Edge5Evaluation(Base):
    __tablename__ = "edge5_evaluations"
    evaluation_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    drill_id: Mapped[str|None] = mapped_column(String(60), index=True, nullable=True)
    age: Mapped[str|None] = mapped_column(String(40), nullable=True)
    level: Mapped[str|None] = mapped_column(String(60), nullable=True)
    total_players: Mapped[int|None] = mapped_column(Integer, nullable=True)
    active_players: Mapped[int|None] = mapped_column(Integer, nullable=True)
    participation_pct: Mapped[float|None] = mapped_column(Float, nullable=True)
    ice_space: Mapped[str|None] = mapped_column(String(100), nullable=True)
    goalies: Mapped[int|None] = mapped_column(Integer, nullable=True)
    fun_challenging: Mapped[bool] = mapped_column(Boolean)
    age_appropriate: Mapped[bool] = mapped_column(Boolean)
    game_like_context: Mapped[bool] = mapped_column(Boolean)
    repetitions: Mapped[bool] = mapped_column(Boolean)
    decisions: Mapped[bool] = mapped_column(Boolean)
    decision_cues: Mapped[str|None] = mapped_column(Text, nullable=True)
    decision_options: Mapped[str|None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer)
    elements_not_met: Mapped[str|None] = mapped_column(Text, nullable=True)
    coach_awareness: Mapped[str|None] = mapped_column(Text, nullable=True)
    recommended_adjustment: Mapped[str|None] = mapped_column(Text, nullable=True)
    context_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserDrill(Base):
    __tablename__ = "user_drills"
    user_drill_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), index=True)
    library_state: Mapped[str] = mapped_column(String(40), default="My Library")
    contribution_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    based_on_drill_id: Mapped[str|None] = mapped_column(String(60), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    game_problem: Mapped[str|None] = mapped_column(Text, nullable=True)
    objective: Mapped[str|None] = mapped_column(Text, nullable=True)
    age: Mapped[str|None] = mapped_column(String(40), nullable=True)
    level: Mapped[str|None] = mapped_column(String(60), nullable=True)
    players: Mapped[int|None] = mapped_column(Integer, nullable=True)
    goalies: Mapped[int|None] = mapped_column(Integer, nullable=True)
    ice: Mapped[str|None] = mapped_column(String(100), nullable=True)
    duration: Mapped[int|None] = mapped_column(Integer, nullable=True)
    setup: Mapped[str|None] = mapped_column(Text, nullable=True)
    how_it_runs: Mapped[str|None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str|None] = mapped_column(Text, nullable=True)
    coaching_cues: Mapped[str|None] = mapped_column(Text, nullable=True)
    goalie_focus: Mapped[str|None] = mapped_column(Text, nullable=True)
    safety_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    decision_cues: Mapped[str|None] = mapped_column(Text, nullable=True)
    decision_options: Mapped[str|None] = mapped_column(Text, nullable=True)
    edge_evaluation_id: Mapped[str|None] = mapped_column(String(60), nullable=True)
    user_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPractice(Base):
    __tablename__ = "user_practices"
    user_practice_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), index=True)
    library_state: Mapped[str] = mapped_column(String(40), default="My Library")
    contribution_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    title: Mapped[str] = mapped_column(String(200))
    primary_game_problem: Mapped[str|None] = mapped_column(Text, nullable=True)
    age: Mapped[str|None] = mapped_column(String(40), nullable=True)
    level: Mapped[str|None] = mapped_column(String(60), nullable=True)
    players: Mapped[int|None] = mapped_column(Integer, nullable=True)
    goalies: Mapped[int|None] = mapped_column(Integer, nullable=True)
    coaches: Mapped[int|None] = mapped_column(Integer, nullable=True)
    ice: Mapped[str|None] = mapped_column(String(100), nullable=True)
    total_minutes: Mapped[int|None] = mapped_column(Integer, nullable=True)
    objective: Mapped[str|None] = mapped_column(Text, nullable=True)
    edge_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    user_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PracticeSegment(Base):
    __tablename__ = "practice_segments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_practice_id: Mapped[str] = mapped_column(String(60), ForeignKey("user_practices.user_practice_id"), index=True)
    segment_number: Mapped[int] = mapped_column(Integer)
    start_minute: Mapped[int|None] = mapped_column(Integer, nullable=True)
    duration: Mapped[int|None] = mapped_column(Integer, nullable=True)
    activity_source: Mapped[str|None] = mapped_column(String(40), nullable=True)
    activity_id: Mapped[str|None] = mapped_column(String(60), nullable=True)
    activity_name: Mapped[str|None] = mapped_column(String(200), nullable=True)
    purpose: Mapped[str|None] = mapped_column(Text, nullable=True)
    players_active: Mapped[int|None] = mapped_column(Integer, nullable=True)
    players_total: Mapped[int|None] = mapped_column(Integer, nullable=True)
    repetitions_met: Mapped[bool|None] = mapped_column(Boolean, nullable=True)
    goalie_role: Mapped[str|None] = mapped_column(Text, nullable=True)
    setup_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    segment_notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    __table_args__=(UniqueConstraint('user_practice_id','segment_number',name='uq_practice_segment'),)

class Contribution(Base):
    __tablename__ = "contributions"
    queue_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(20))
    user_content_id: Mapped[str] = mapped_column(String(60), index=True)
    owner_key: Mapped[str] = mapped_column(String(120), index=True)
    consent_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Submitted")
    notes: Mapped[str|None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class DevelopmentGoal(Base):
    __tablename__ = "development_goals"

    goal_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(40),
        default="Active",
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class PracticeReview(Base):
    __tablename__ = "practice_reviews"

    review_id: Mapped[str] = mapped_column(String(60), primary_key=True)

    owner_key: Mapped[str] = mapped_column(String(120), index=True)

    user_practice_id: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
        index=True
    )

    development_goal_id: Mapped[str | None] = mapped_column(
        String(60),
        ForeignKey("development_goals.goal_id"),
        nullable=True,
        index=True
    )

    practice_goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    overall_result: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True
    )

    what_worked: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    what_didnt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    overall_observation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    next_practice_decision: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True
    )

    next_focus: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class PracticeActivityReview(Base):
    __tablename__ = "practice_activity_reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    review_id: Mapped[str] = mapped_column(
        String(60),
        ForeignKey("practice_reviews.review_id"),
        index=True
    )

    segment_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    activity_source: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    activity_id: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True
    )

    activity_name: Mapped[str] = mapped_column(
        String(200)
    )

    intended_goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    goal_delivery: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    focus_element_1: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True
    )

    focus_element_1_result: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    focus_element_2: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True
    )

    focus_element_2_result: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    coach_observation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    adjustment_next_time: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    would_use_again: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )
