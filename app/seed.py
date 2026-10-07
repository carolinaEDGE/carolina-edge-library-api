import json
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Drill

SEED = Path(__file__).resolve().parents[1] / "data" / "drills.json"

def seed_drills(db: Session):
    if db.query(Drill).count() > 0:
        return 0
    rows=json.loads(SEED.read_text(encoding='utf-8'))
    for d in rows:
        db.add(Drill(
            drill_id=d['drill_id'], version=str(d.get('version') or '1.0'), name=d['name'], review_status=d.get('review_status'),
            family=d.get('family'), primary_game_problem=d.get('primary_game_problem'), target_behaviors=d.get('target_behaviors'),
            best_ages=d.get('best_ages'), level=d.get('level'), goalies=str(d.get('goalies')) if d.get('goalies') is not None else None,
            ice_footprint=d.get('ice_footprint'), setup_summary=d.get('setup_summary'), how_it_runs=d.get('how_it_runs'),
            coaching_cues_json=json.dumps(d.get('coaching_cues') or []), guided_questions_json=json.dumps(d.get('guided_questions') or []),
            constraints_json=json.dumps(d.get('constraints_progressions') or []), why_it_works=d.get('why_it_works'),
            search_tags_json=json.dumps(d.get('search_tags') or []), decision_cue_summary=d.get('decision_cue_summary'),
            decision_options_summary=d.get('decision_options_summary'), game_like_evidence=d.get('game_like_evidence'),
            age_context_notes=d.get('age_context_notes'), source_json=json.dumps({'source':d.get('source'),'source_version':d.get('source_version')})
        ))
    db.commit()
    return len(rows)
