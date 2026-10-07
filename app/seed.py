import json
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Drill

LEGACY_SEED = Path(__file__).resolve().parents[1] / "data" / "drills.json"
EDGE_PUBLISH_SEED = Path(__file__).resolve().parents[1] / "data" / "edge_seed_publish_v1.jsonl"
EDGE_ADAPT_CANDIDATE_SEED = Path(__file__).resolve().parents[1] / "data" / "edge_manual_b_verified_candidates_v1.jsonl"
EDGE_GAP_FILL_SEED = Path(__file__).resolve().parents[1] / "data" / "edge_gap_fill_verified_v1.jsonl"
EDGE_GAP_FILL_SEED_V2 = Path(__file__).resolve().parents[1] / "data" / "edge_gap_fill_verified_v2.jsonl"
EDGE_GAP_FILL_SEED_V3 = Path(__file__).resolve().parents[1] / "data" / "edge_gap_fill_verified_v3.jsonl"
EDGE_GAP_FILL_SEED_V4 = Path(__file__).resolve().parents[1] / "data" / "edge_gap_fill_verified_v4.jsonl"
EDGE_AGE_READINESS = Path(__file__).resolve().parents[1] / "data" / "edge_age_readiness_v1.jsonl"
EDGE_CAPACITY = Path(__file__).resolve().parents[1] / "data" / "edge_capacity_v1.jsonl"

def _legacy_rows():
    return json.loads(LEGACY_SEED.read_text(encoding="utf-8"))

def _jsonl_rows(path: Path):
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

def _edge_rows():
    return (
        _jsonl_rows(EDGE_PUBLISH_SEED)
        + _jsonl_rows(EDGE_ADAPT_CANDIDATE_SEED)
        + _jsonl_rows(EDGE_GAP_FILL_SEED)
        + _jsonl_rows(EDGE_GAP_FILL_SEED_V2)
        + _jsonl_rows(EDGE_GAP_FILL_SEED_V3)
        + _jsonl_rows(EDGE_GAP_FILL_SEED_V4)
    )

def _readiness_rows():
    return _jsonl_rows(EDGE_AGE_READINESS)

def _capacity_rows():
    return _jsonl_rows(EDGE_CAPACITY)

def _normalize_goalies(value):
    text = (value or "").strip().upper()
    if text.startswith("NO"):
        return "NO"
    if text.startswith("YES") or "GOALIE" in text or "NET SHOWN" in text:
        return "YES"
    return "UNKNOWN"

def _ice_footprint(value):
    text = (value or "").strip()
    upper = text.upper()
    if "FULL ICE" in upper:
        return "FULL ICE"
    if "HALF-ICE" in upper or "HALF ICE" in upper:
        return "HALF ICE"
    if "END-ZONE" in upper or "END ZONE" in upper:
        return "END ZONE"
    if "SMALL-AREA" in upper or "SMALL AREA" in upper:
        return "SMALL AREA"
    return None

def seed_drills(db: Session):
    created = 0

    # Existing pre-v0.2 production drills must remain preserved but not searchable.
    db.query(Drill).filter(~Drill.drill_id.like("EDGE-A%")).update(
        {
            Drill.publication_status: "LEGACY_HOLD",
            Drill.surface_policy: "REFERENCE_ONLY",
            Drill.is_searchable: False,
        },
        synchronize_session=False,
    )
    if db.query(Drill).count() == 0:
        for d in _legacy_rows():
            db.add(Drill(
                drill_id=d["drill_id"], version=str(d.get("version") or "1.0"), name=d["name"], review_status=d.get("review_status"),
                family=d.get("family"), primary_game_problem=d.get("primary_game_problem"), target_behaviors=d.get("target_behaviors"),
                best_ages=d.get("best_ages"), level=d.get("level"), goalies=str(d.get("goalies")) if d.get("goalies") is not None else None,
                ice_footprint=d.get("ice_footprint"), setup_summary=d.get("setup_summary"), how_it_runs=d.get("how_it_runs"),
                coaching_cues_json=json.dumps(d.get("coaching_cues") or []), guided_questions_json=json.dumps(d.get("guided_questions") or []),
                constraints_json=json.dumps(d.get("constraints_progressions") or []), why_it_works=d.get("why_it_works"),
                search_tags_json=json.dumps(d.get("search_tags") or []), decision_cue_summary=d.get("decision_cue_summary"),
                decision_options_summary=d.get("decision_options_summary"), game_like_evidence=d.get("game_like_evidence"),
                age_context_notes=d.get("age_context_notes"), source_json=json.dumps({"source":d.get("source"),"source_version":d.get("source_version")}),
                is_searchable=False, publication_status="LEGACY_HOLD", surface_policy="REFERENCE_ONLY"
            ))
            created += 1

    for d in _edge_rows():
        rec = db.get(Drill, d["edge_id"])
        if rec is None:
            rec = Drill(drill_id=d["edge_id"], name=d["title"])
            db.add(rec)
            created += 1
        rec.version = "2.0"
        rec.name = d["title"]
        rec.review_status = "SOURCE VERIFIED"
        rec.family = d.get("family")
        rec.best_ages = d.get("best_ages")
        rec.primary_game_problem = d.get("game_problem")
        rec.search_tags_json = json.dumps(d.get("search_tags") or [])
        rec.goalies = _normalize_goalies(d.get("goalie"))
        rec.ice_footprint = _ice_footprint(d.get("space_organization"))
        rec.setup_summary = d.get("space_organization")
        rec.how_it_runs = d.get("source_text")
        rec.decision_cue_summary = d.get("representative_information")
        rec.decision_options_summary = d.get("player_decisions")
        rec.source_json = json.dumps({
            "source_asset": d.get("source_asset"),
            "source_evidence": d.get("source_evidence"),
            "goalie_source": d.get("goalie"),
        })
        rec.record_type = d.get("record_type")
        rec.route = d.get("route")
        rec.publication_status = d.get("publication_status")
        rec.surface_policy = d.get("surface_policy")
        rec.source_evidence = d.get("source_evidence")
        rec.source_text = d.get("source_text")
        rec.source_asset = d.get("source_asset")
        rec.source_boundary = d.get("source_boundary")
        rec.representative_information = d.get("representative_information")
        rec.player_decisions = d.get("player_decisions")
        rec.space_organization = d.get("space_organization")
        rec.coach_notes = d.get("coach_notes")
        rec.adaptation_text = d.get("adaptation_text")
        rec.schema_version = d.get("schema_version")
        rec.is_searchable = bool(d.get("is_searchable"))
        rec.active = True
    for g in _readiness_rows():
        rec = db.get(Drill, g["edge_id"])
        if rec is None:
            continue
        rec.edge_age_readiness_json = json.dumps(g.get("readiness") or {})
        rec.edge_readiness_basis = g.get("basis")
        rec.age_context_notes = g.get("note")

    for g in _capacity_rows():
        rec = db.get(Drill, g["edge_id"])
        if rec is None:
            continue
        rec.source_active_players_min = g.get("source_active_players_min")
        rec.source_active_players_max = g.get("source_active_players_max")
        rec.edge_station_group_min = g.get("edge_station_group_min")
        rec.edge_station_group_max = g.get("edge_station_group_max")
        rec.simultaneous_goalies = g.get("simultaneous_goalies")
        rec.capacity_basis = g.get("capacity_basis")
        rec.capacity_notes = g.get("capacity_notes")

    db.commit()
    return created
