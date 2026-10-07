import json, os, uuid
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .db import Base, engine, get_db

from .models import (
    Drill,
    Edge5Evaluation,
    UserDrill,
    UserPractice,
    PracticeSegment,
    Contribution,
    DevelopmentGoal,
    PracticeReview,
    PracticeActivityReview,
    GameCheckIn
)
from .schemas import (
    Edge5Input,
    UserDrillCreate,
    UserPracticeCreate,
    ContributionCreate,
    DevelopmentGoalCreate,
    PracticeReviewCreate,
    GameCheckInCreate
)
from .seed import seed_drills
from .migrations import migrate_v02

VERSION="0.2.0-staging"
app=FastAPI(title="Carolina EDGE Library API", version=VERSION, description="Drill and practice library service for Carolina EDGE. EDGE 5 Elements is informative, never a creation/use gate.")

Base.metadata.create_all(bind=engine)
migrate_v02(engine)

if engine.dialect.name == "postgresql":
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            ALTER TABLE practice_activity_reviews
            ALTER COLUMN goal_delivery TYPE TEXT,
            ALTER COLUMN focus_element_1_result TYPE TEXT,
            ALTER COLUMN focus_element_2_result TYPE TEXT,
            ALTER COLUMN would_use_again TYPE TEXT
            """
        )

        conn.exec_driver_sql(
            """
            ALTER TABLE game_check_ins
            ALTER COLUMN next_practice_decision TYPE TEXT
            """
        )

with next(get_db()) as db:
    seed_drills(db)

def require_write_key(x_api_key: str|None = Header(default=None)):
    expected=os.getenv('WRITE_API_KEY')
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")

def drill_to_dict(d: Drill):
    return {
        'drill_id':d.drill_id,'version':d.version,'name':d.name,'review_status':d.review_status,'family':d.family,
        'primary_game_problem':d.primary_game_problem,'target_behaviors':d.target_behaviors,'best_ages':d.best_ages,'level':d.level,
        'goalies':d.goalies,'ice_footprint':d.ice_footprint,'setup_summary':d.setup_summary,'how_it_runs':d.how_it_runs,
        'coaching_cues':json.loads(d.coaching_cues_json or '[]'),'guided_questions':json.loads(d.guided_questions_json or '[]'),
        'constraints_progressions':json.loads(d.constraints_json or '[]'),'why_it_works':d.why_it_works,'search_tags':json.loads(d.search_tags_json or '[]'),
        'decision_cue_summary':d.decision_cue_summary,'decision_options_summary':d.decision_options_summary,
        'game_like_evidence':d.game_like_evidence,'age_context_notes':d.age_context_notes,
        'publication_status':d.publication_status,'surface_policy':d.surface_policy,'source_evidence':d.source_evidence,
        'source_text':d.source_text,'source_asset':d.source_asset,'source_boundary':d.source_boundary,
        'representative_information':d.representative_information,'player_decisions':d.player_decisions,
        'space_organization':d.space_organization,'coach_notes':d.coach_notes,'schema_version':d.schema_version,
        'edge_age_readiness':json.loads(d.edge_age_readiness_json or '{}'),
        'edge_readiness_basis':d.edge_readiness_basis,
        'source_active_players_min':d.source_active_players_min,
        'source_active_players_max':d.source_active_players_max,
        'edge_station_group_min':d.edge_station_group_min,
        'edge_station_group_max':d.edge_station_group_max,
        'simultaneous_goalies':d.simultaneous_goalies,
        'capacity_basis':d.capacity_basis,
        'capacity_notes':d.capacity_notes
    }
@app.get('/')
def root():
    return {
        'status': 'ok',
        'service': 'carolina-edge-library-api',
        'version': VERSION
    }
@app.get('/health')
def health(db: Session=Depends(get_db)):
    total = db.query(Drill).count()
    active = db.query(Drill).filter(Drill.active.is_(True)).count()
    inactive = db.query(Drill).filter(Drill.active.is_(False)).count()

    return {
        'status': 'ok',
        'version': VERSION,
        'drills': total,
        'active_drills': active,
        'inactive_drills': inactive
    }

@app.get('/v1/drills')
def search_drills(q: str|None=None, game_problem: str|None=None, family: str|None=None, age: str|None=None,
                  readiness_age: str|None=None, readiness: str|None=None,
                  ice: str|None=None, goalies: int|None=None, limit: int=Query(10,ge=1,le=50), db:Session=Depends(get_db)):
    qry=db.query(Drill).filter(Drill.active.is_(True), Drill.is_searchable.is_(True))
    if q:
        like=f"%{q}%"
        qry=qry.filter(or_(
            Drill.name.ilike(like),
            Drill.primary_game_problem.ilike(like),
            Drill.target_behaviors.ilike(like),
            Drill.search_tags_json.ilike(like),
            Drill.representative_information.ilike(like),
            Drill.player_decisions.ilike(like),
            Drill.source_text.ilike(like),
            Drill.coach_notes.ilike(like)
        ))
    if game_problem: qry=qry.filter(Drill.primary_game_problem.ilike(f"%{game_problem}%"))
    if family: qry=qry.filter(Drill.family.ilike(f"%{family}%"))
    if age: qry=qry.filter(or_(Drill.best_ages.is_(None), Drill.best_ages.ilike(f"%{age}%")))
    if readiness_age:
        qry=qry.filter(Drill.edge_age_readiness_json.ilike(f'%"{readiness_age}"%'))
        if readiness:
            qry=qry.filter(Drill.edge_age_readiness_json.ilike(f'%"{readiness_age}": "{readiness}"%'))
        else:
            qry=qry.filter(~Drill.edge_age_readiness_json.ilike(f'%"{readiness_age}": "DO NOT RUSH"%'))
    if ice: qry=qry.filter(Drill.ice_footprint.ilike(f"%{ice}%"))
    rows=qry.limit(limit).all()
    return {'count':len(rows),'items':[drill_to_dict(x) for x in rows], 'note':'EDGE 5 Elements should be evaluated in the coach\'s actual context; library search does not block lower-scoring drills.'}

def _text_blob(d: Drill):
    parts = [
        d.name, d.family, d.primary_game_problem, d.target_behaviors, d.search_tags_json,
        d.representative_information, d.player_decisions, d.source_text, d.coach_notes
    ]
    return " ".join(str(x or "") for x in parts).lower()

def _readiness_value(d: Drill, age: str|None):
    if not age:
        return None
    try:
        return json.loads(d.edge_age_readiness_json or "{}").get(age)
    except Exception:
        return None

def _recommendation_score(d: Drill, q: str|None, game_problem: str|None, family: str|None,
                          readiness_age: str|None, ice: str|None, goalies: int|None,
                          players: int|None):
    score = 0
    reasons = []
    blob = _text_blob(d)

    if game_problem:
        gp = game_problem.lower().strip()
        primary = (d.primary_game_problem or "").lower()
        if gp and gp in primary:
            score += 40
            reasons.append("game problem match")
        elif gp and gp in blob:
            score += 24
            reasons.append("related game-problem language")

    if q:
        term = q.lower().strip()
        if term and term in (d.name or "").lower():
            score += 24
            reasons.append("title match")
        elif term and term in (d.search_tags_json or "").lower():
            score += 20
            reasons.append("search-tag match")
        elif term and term in blob:
            score += 12
            reasons.append("content match")

    if family:
        fam = family.lower().strip()
        if fam and fam in (d.family or "").lower():
            score += 16
            reasons.append("family match")

    readiness = _readiness_value(d, readiness_age)
    readiness_points = {
        "PRIORITIZE NOW": 24,
        "INTRODUCE": 16,
        "CONTINUE DEVELOPING": 12,
        "DO NOT RUSH": -60,
    }
    if readiness:
        score += readiness_points.get(readiness, 0)
        reasons.append(f"{readiness_age} readiness: {readiness}")

    if ice:
        requested = ice.lower().strip()
        actual = (d.ice_footprint or "").lower()
        if requested and requested in actual:
            score += 10
            reasons.append("ice-space match")
        elif requested and actual:
            score -= 4

    if goalies is not None:
        g = (d.goalies or "").upper()
        wants_goalie = goalies > 0
        if wants_goalie and g == "YES":
            score += 10
            reasons.append("goalie match")
        elif not wants_goalie and g == "NO":
            score += 10
            reasons.append("no-goalie match")
        elif wants_goalie and g == "NO":
            score -= 12
        elif not wants_goalie and g == "YES":
            score -= 8
        if d.simultaneous_goalies is not None:
            if goalies == d.simultaneous_goalies:
                score += 6
                reasons.append("simultaneous-goalie capacity match")
            elif goalies > 0 and d.simultaneous_goalies == 0:
                score -= 4

    if players is not None and d.edge_station_group_min is not None and d.edge_station_group_max is not None:
        if d.edge_station_group_min <= players <= d.edge_station_group_max:
            score += 14
            reasons.append("station group-size match")
        elif players < d.edge_station_group_min:
            score -= 10
            reasons.append("below recommended station group")
        else:
            over = players - d.edge_station_group_max
            score -= min(12, 4 + over)
            reasons.append("above recommended station group")

    if d.representative_information:
        score += 4
        reasons.append("representative cues documented")
    if d.player_decisions:
        score += 4
        reasons.append("player decisions documented")
    if d.source_evidence and "VERIFIED" in d.source_evidence.upper():
        score += 4
        reasons.append("source verified")

    return score, reasons, readiness

@app.get('/v1/recommendations')
def recommend_drills(q: str|None=None, game_problem: str|None=None, family: str|None=None,
                     readiness_age: str|None=None, ice: str|None=None, goalies: int|None=None,
                     players: int|None=None, limit: int=Query(5,ge=1,le=20),
                     db:Session=Depends(get_db)):
    rows = db.query(Drill).filter(Drill.active.is_(True), Drill.is_searchable.is_(True)).all()
    ranked = []
    for d in rows:
        score, reasons, readiness = _recommendation_score(
            d, q, game_problem, family, readiness_age, ice, goalies, players
        )
        if readiness == "DO NOT RUSH":
            continue
        if (q or game_problem or family) and score <= 0:
            continue
        item = drill_to_dict(d)
        item["recommendation_score"] = score
        item["recommendation_reasons"] = reasons
        item["requested_readiness"] = readiness
        ranked.append(item)
    ranked.sort(key=lambda x: (-x["recommendation_score"], x["drill_id"]))
    return {
        "count": min(len(ranked), limit),
        "items": ranked[:limit],
        "ranking_version": "EDGE_RECOMMENDER_V2",
        "players_requested": players,
        "note": "Player count is scored against Carolina EDGE editorial station-group ranges; source active-player counts remain separately identified as source-derived."
    }

@app.get('/v1/practice-station-recommendations')
def recommend_practice_stations(total_players: int=Query(...,ge=2,le=40),
                                  stations: int=Query(4,ge=1,le=8),
                                  goalies: int=Query(0,ge=0,le=8),
                                  q: str|None=None,
                                  game_problem: str|None=None,
                                  readiness_age: str|None=None,
                                  ice: str|None=None,
                                  db:Session=Depends(get_db)):
    base = total_players // stations
    extra = total_players % stations
    group_sizes = [base + (1 if i < extra else 0) for i in range(stations)]
    rows = db.query(Drill).filter(Drill.active.is_(True), Drill.is_searchable.is_(True)).all()
    selected = []
    used = set()
    goalies_remaining = goalies

    for idx, group_size in enumerate(group_sizes, start=1):
        candidates = []
        for d in rows:
            if d.drill_id in used:
                continue
            # A station cannot recommend an activity that needs more simultaneously
            # active skaters than the station group actually contains. Editorial group
            # ranges remain a ranking preference, but source-derived active-player
            # minimums are a hard feasibility boundary.
            if d.source_active_players_min is not None and d.source_active_players_min > group_size:
                continue
            score, reasons, readiness = _recommendation_score(
                d, q, game_problem, None, readiness_age, ice, None, group_size
            )
            if readiness == "DO NOT RUSH":
                continue
            if (q or game_problem) and score <= 0:
                continue
            required_goalies = d.simultaneous_goalies or 0
            if required_goalies > goalies_remaining and required_goalies > 0:
                score -= 20
                reasons = reasons + ["goalie capacity unavailable"]
            elif required_goalies > 0:
                score += 8
                reasons = reasons + ["goalie allocation available"]
            candidates.append((score, d.drill_id, d, reasons, readiness, required_goalies))

        candidates.sort(key=lambda x: (-x[0], x[1]))
        if not candidates:
            selected.append({"station":idx,"group_size":group_size,"status":"NO_MATCH","drill":None})
            continue

        score, _, d, reasons, readiness, required_goalies = candidates[0]
        used.add(d.drill_id)
        allocated_goalies = 0
        if required_goalies <= goalies_remaining:
            allocated_goalies = required_goalies
            goalies_remaining -= allocated_goalies

        item = drill_to_dict(d)
        item["recommendation_score"] = score
        item["recommendation_reasons"] = reasons
        item["requested_readiness"] = readiness
        selected.append({
            "station":idx,
            "group_size":group_size,
            "goalies_allocated":allocated_goalies,
            "status":"RECOMMENDED",
            "drill":item
        })

    return {
        "ranking_version":"EDGE_STATION_SET_V1",
        "total_players":total_players,
        "stations":stations,
        "group_sizes":group_sizes,
        "goalies_requested":goalies,
        "goalies_unallocated":goalies_remaining,
        "items":selected,
        "note":"Capacity-compatible activity selection only; full Practice EDGE still controls sequencing, timing, progression, and coaching context."
    }

@app.get('/v1/practice-blueprint')
def build_practice_blueprint(total_players: int=Query(...,ge=6,le=40),
                             goalies: int=Query(0,ge=0,le=8),
                             total_minutes: int=Query(60,ge=45,le=90),
                             game_problem: str|None=None,
                             q: str|None=None,
                             readiness_age: str|None=None,
                             ice: str|None=None,
                             db:Session=Depends(get_db)):
    if total_minutes != 60:
        raise HTTPException(400, 'EDGE_PRACTICE_BLUEPRINT_V1 currently supports the approved 60-minute template only.')

    station_set = recommend_practice_stations(
        total_players=total_players,
        stations=4,
        goalies=goalies,
        q=q,
        game_problem=game_problem,
        readiness_age=readiness_age,
        ice=ice,
        db=db
    )

    groups = [chr(ord('A') + i) for i in range(4)]
    station_periods = []
    start = 5
    for period in range(4):
        assignments = []
        for gi, group in enumerate(groups):
            assignments.append({
                "group":group,
                "station":((gi + period) % 4) + 1
            })
        station_periods.append({
            "period":period + 1,
            "start_minute":start,
            "duration":7,
            "assignments":assignments
        })
        start += 7
        if period < 3:
            start += 1

    used_ids = {
        x["drill"]["drill_id"]
        for x in station_set["items"]
        if x.get("drill")
    }

    rows = db.query(Drill).filter(Drill.active.is_(True), Drill.is_searchable.is_(True)).all()
    final_candidates = []
    for d in rows:
        if d.drill_id in used_ids:
            continue
        readiness = _readiness_value(d, readiness_age)
        if readiness == "DO NOT RUSH":
            continue
        max_group = d.edge_station_group_max or 8
        copies = max(1, (total_players + max_group - 1) // max_group)
        per_copy = (total_players + copies - 1) // copies
        score, reasons, readiness = _recommendation_score(
            d, q, game_problem, None, readiness_age, ice, None, per_copy
        )
        if "game" in ((d.family or "") + " " + (d.name or "")).lower():
            score += 18
            reasons = reasons + ["game-format preference"]
        goalie_need = (d.simultaneous_goalies or 0) * copies
        if goalie_need <= goalies:
            score += 8
            reasons = reasons + ["goalie capacity supports concurrent game copies"]
        elif goalie_need > 0:
            score -= 16
            reasons = reasons + ["insufficient goalies for all concurrent copies"]
        final_candidates.append((score, d.drill_id, d, reasons, readiness, copies, per_copy, goalie_need))

    final_candidates.sort(key=lambda x: (-x[0], x[1]))
    final_game = None
    if final_candidates:
        score, _, d, reasons, readiness, copies, per_copy, goalie_need = final_candidates[0]
        item = drill_to_dict(d)
        item["recommendation_score"] = score
        item["recommendation_reasons"] = reasons
        item["requested_readiness"] = readiness
        final_game = {
            "duration":10,
            "activity":item,
            "concurrent_copies":copies,
            "players_per_copy_target":per_copy,
            "goalies_required_for_all_copies":goalie_need,
            "goalie_adjustment":(
                "Use tires/mini-nets for any copy without a goalie."
                if goalie_need > goalies else
                "Goalie allocation fits available goalies."
            )
        }

    application_activity = None
    ranked_station_drills = [
        x["drill"] for x in station_set["items"]
        if x.get("drill")
    ]
    if ranked_station_drills:
        application_activity = ranked_station_drills[0]

    return {
        "blueprint_version":"EDGE_PRACTICE_BLUEPRINT_V1",
        "template_basis":"CAROLINA_EDGE_EDITORIAL_60_MIN_V1",
        "inputs":{
            "total_players":total_players,
            "goalies":goalies,
            "total_minutes":total_minutes,
            "game_problem":game_problem,
            "query":q,
            "readiness_age":readiness_age,
            "ice":ice
        },
        "schedule":[
            {
                "phase":"Warm-up / activation",
                "start_minute":0,
                "duration":5,
                "activity_source":"COACH_DESIGNED",
                "guidance":"Use movement plus puck touches that prepare the primary game problem; avoid a scripted cone route unless it is serving a specific technical need."
            },
            {
                "phase":"Station block",
                "start_minute":5,
                "duration":31,
                "station_period_minutes":7,
                "change_minutes":1,
                "periods":station_periods,
                "stations":station_set["items"]
            },
            {
                "phase":"Application / progression block",
                "start_minute":36,
                "duration":12,
                "activity":application_activity,
                "guidance":"Re-use the strongest matching station activity with one meaningful constraint change that increases representative pressure, information, or transition without prescribing the solution."
            },
            {
                "phase":"Final game",
                "start_minute":48,
                "duration":10,
                "game":final_game
            },
            {
                "phase":"Quick recap / reset",
                "start_minute":58,
                "duration":2,
                "guidance":"One or two questions tied to the game problem; keep the recap brief."
            }
        ],
        "quality_controls":{
            "published_only":True,
            "do_not_rush_excluded_when_age_supplied":True,
            "source_and_edge_metadata_separated":True,
            "station_capacity_scored":True,
            "goalie_capacity_considered":True,
            "unique_station_activities":True
        },
        "diagram_handoff":{
            "status":"READY_FOR_MODEL_GEOMETRY",
            "must_validate_before_render":True,
            "geometry_boundary":"Generated rink geometry is Carolina EDGE presentation geometry unless the source explicitly supplies the exact spatial fact.",
            "stations":[
                {
                    "station":s["station"],
                    "group_size":s["group_size"],
                    "goalies_allocated":s.get("goalies_allocated",0),
                    "drill_id":s["drill"]["drill_id"],
                    "title":s["drill"]["name"],
                    "source_text":s["drill"].get("source_text"),
                    "space_organization":s["drill"].get("space_organization"),
                    "goalies":s["drill"].get("goalies"),
                    "source_boundary":s["drill"].get("source_boundary"),
                    "diagram_request_status":"NEEDS_MODEL_GEOMETRY"
                }
                for s in station_set["items"] if s.get("drill")
            ],
            "final_game":(
                {
                    "drill_id":final_game["activity"]["drill_id"],
                    "title":final_game["activity"]["name"],
                    "source_text":final_game["activity"].get("source_text"),
                    "space_organization":final_game["activity"].get("space_organization"),
                    "goalies":final_game["activity"].get("goalies"),
                    "source_boundary":final_game["activity"].get("source_boundary"),
                    "diagram_request_status":"NEEDS_MODEL_GEOMETRY"
                }
                if final_game else None
            )
        },
        "note":"This deterministic Practice EDGE blueprint is ready for the Diagram tool family. Geometry must be authored as Carolina EDGE presentation geometry, validated, and only then rendered/assembled."
    }

@app.get('/v1/drills/{drill_id}')
def get_drill(drill_id:str, db:Session=Depends(get_db)):
    d=db.get(Drill,drill_id)
    if not d or not d.active or not d.is_searchable: raise HTTPException(404,'Drill not found')
    return drill_to_dict(d)

@app.post('/v1/evaluations')
def evaluate_edge5(payload:Edge5Input, db:Session=Depends(get_db)):
    repetitions=(payload.active_players/payload.total_players)>=0.5
    pct=payload.active_players/payload.total_players
    elements={
        'fun_challenging':payload.fun_challenging,'age_appropriate':payload.age_appropriate,
        'game_like_context':payload.game_like_context,'repetitions':repetitions,'decisions':payload.decisions
    }
    score=sum(1 for v in elements.values() if v)
    labels={'fun_challenging':'Fun & Challenging','age_appropriate':'Age-Appropriate','game_like_context':'Game-Like Context','repetitions':'Repetitions','decisions':'Decisions'}
    not_met=[labels[k] for k,v in elements.items() if not v]
    awareness=payload.coach_awareness
    if not repetitions:
        rep=f"Repetitions is Not Met: {payload.active_players} of {payload.total_players} players are active at one time ({pct:.0%}); EDGE uses a 50% threshold."
        awareness=(awareness+' ' if awareness else '')+rep
    eid='E5-'+uuid.uuid4().hex[:12].upper()
    rec=Edge5Evaluation(evaluation_id=eid,drill_id=payload.drill_id,age=payload.age,level=payload.level,total_players=payload.total_players,
        active_players=payload.active_players,participation_pct=pct,ice_space=payload.ice_space,goalies=payload.goalies,
        fun_challenging=payload.fun_challenging,age_appropriate=payload.age_appropriate,game_like_context=payload.game_like_context,
        repetitions=repetitions,decisions=payload.decisions,decision_cues=payload.decision_cues,decision_options=payload.decision_options,
        score=score,elements_not_met='; '.join(not_met),coach_awareness=awareness,recommended_adjustment=payload.recommended_adjustment,context_notes=payload.context_notes)
    db.add(rec); db.commit()
    return {'evaluation_id':eid,'edge_5_elements_score':score,'out_of':5,'results':elements,'participation_pct':pct,
            'elements_not_met':not_met,'coach_awareness':awareness,'recommended_adjustment':payload.recommended_adjustment,
            'blocking':False,'principle':'A low EDGE 5 Elements score informs the coach; it never prevents creating, saving, recommending, or using the drill.'}

@app.post('/v1/user-drills',dependencies=[Depends(require_write_key)])
def save_user_drill(payload:UserDrillCreate,db:Session=Depends(get_db)):
    uid='UD-'+uuid.uuid4().hex[:12].upper()
    rec=UserDrill(user_drill_id=uid,owner_key=payload.owner_key,title=payload.title,based_on_drill_id=payload.based_on_drill_id,
        game_problem=payload.game_problem,objective=payload.objective,age=payload.age,level=payload.level,players=payload.players,goalies=payload.goalies,
        ice=payload.ice,duration=payload.duration,setup=payload.setup,how_it_runs=payload.how_it_runs,constraints=payload.constraints,
        coaching_cues=payload.coaching_cues,goalie_focus=payload.goalie_focus,safety_notes=payload.safety_notes,decision_cues=payload.decision_cues,
        decision_options=payload.decision_options,edge_evaluation_id=payload.edge_evaluation_id,user_notes=payload.user_notes)
    db.add(rec);db.commit()
    return {'user_drill_id':uid,'library_state':'My Library','contribution_consent':False}

@app.get('/v1/user-drills')
def list_user_drills(owner_key:str,db:Session=Depends(get_db)):
    rows=db.query(UserDrill).filter(UserDrill.owner_key==owner_key).order_by(UserDrill.updated_at.desc()).all()
    return {'count':len(rows),'items':[{'user_drill_id':r.user_drill_id,'title':r.title,'game_problem':r.game_problem,'age':r.age,'players':r.players,'library_state':r.library_state,'edge_evaluation_id':r.edge_evaluation_id} for r in rows]}

@app.post('/v1/user-practices',dependencies=[Depends(require_write_key)])
def save_user_practice(payload:UserPracticeCreate,db:Session=Depends(get_db)):
    uid='UP-'+uuid.uuid4().hex[:12].upper()
    rec=UserPractice(user_practice_id=uid,owner_key=payload.owner_key,title=payload.title,primary_game_problem=payload.primary_game_problem,
        age=payload.age,level=payload.level,players=payload.players,goalies=payload.goalies,coaches=payload.coaches,ice=payload.ice,
        total_minutes=payload.total_minutes,objective=payload.objective,edge_notes=payload.edge_notes,user_notes=payload.user_notes)
    db.add(rec)
    db.flush()
    for s in payload.segments:
        rep=None if s.players_active is None or s.players_total is None else (s.players_active/s.players_total)>=0.5
        db.add(PracticeSegment(user_practice_id=uid,segment_number=s.segment_number,start_minute=s.start_minute,duration=s.duration,
            activity_source=s.activity_source,activity_id=s.activity_id,activity_name=s.activity_name,purpose=s.purpose,players_active=s.players_active,
            players_total=s.players_total,repetitions_met=rep,goalie_role=s.goalie_role,setup_notes=s.setup_notes,segment_notes=s.segment_notes))
    db.commit()
    return {'user_practice_id':uid,'library_state':'My Library','segments_saved':len(payload.segments),'contribution_consent':False}
@app.get('/v1/user-practices', dependencies=[Depends(require_write_key)])
def list_user_practices(
    owner_key: str,
    db: Session = Depends(get_db)
):
    practices = (
        db.query(UserPractice)
        .filter(UserPractice.owner_key == owner_key)
        .order_by(UserPractice.updated_at.desc())
        .all()
    )

    items = []

    for practice in practices:
        segments = (
            db.query(PracticeSegment)
            .filter(
                PracticeSegment.user_practice_id
                == practice.user_practice_id
            )
            .order_by(PracticeSegment.segment_number)
            .all()
        )

        items.append({
            'user_practice_id': practice.user_practice_id,
            'title': practice.title,
            'primary_game_problem': practice.primary_game_problem,
            'age': practice.age,
            'level': practice.level,
            'players': practice.players,
            'goalies': practice.goalies,
            'coaches': practice.coaches,
            'ice': practice.ice,
            'total_minutes': practice.total_minutes,
            'objective': practice.objective,
            'edge_notes': practice.edge_notes,
            'user_notes': practice.user_notes,
            'library_state': practice.library_state,
            'segments': [
                {
                    'segment_number': s.segment_number,
                    'start_minute': s.start_minute,
                    'duration': s.duration,
                    'activity_source': s.activity_source,
                    'activity_id': s.activity_id,
                    'activity_name': s.activity_name,
                    'purpose': s.purpose,
                    'players_active': s.players_active,
                    'players_total': s.players_total,
                    'repetitions_met': s.repetitions_met,
                    'goalie_role': s.goalie_role,
                    'setup_notes': s.setup_notes,
                    'segment_notes': s.segment_notes
                }
                for s in segments
            ]
        })

    return {
        'count': len(items),
        'items': items
    }
@app.get('/v1/contributions', dependencies=[Depends(require_write_key)])
def list_contributions(
    owner_key: str,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Contribution)
        .filter(Contribution.owner_key == owner_key)
        .order_by(Contribution.submitted_at.desc())
        .all()
    )

    return {
        'count': len(rows),
        'items': [
            {
                'queue_id': r.queue_id,
                'content_type': r.content_type,
                'user_content_id': r.user_content_id,
                'owner_key': r.owner_key,
                'consent_verified': r.consent_verified,
                'status': r.status,
                'notes': r.notes,
                'submitted_at': (
                    r.submitted_at.isoformat()
                    if r.submitted_at is not None
                    else None
                )
            }
            for r in rows
        ]
    }
@app.get('/v1/contributions', dependencies=[Depends(require_write_key)])
def list_contributions(
    owner_key: str,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Contribution)
        .filter(Contribution.owner_key == owner_key)
        .order_by(Contribution.submitted_at.desc())
        .all()
    )

    return {
        'count': len(rows),
        'items': [
            {
                'queue_id': r.queue_id,
                'content_type': r.content_type,
                'user_content_id': r.user_content_id,
                'owner_key': r.owner_key,
                'consent_verified': r.consent_verified,
                'status': r.status,
                'notes': r.notes,
                'submitted_at': (
                    r.submitted_at.isoformat()
                    if r.submitted_at is not None
                    else None
                )
            }
            for r in rows
        ]
    }

@app.post('/v1/contributions',dependencies=[Depends(require_write_key)])
def submit_contribution(payload:ContributionCreate,db:Session=Depends(get_db)):
    if not payload.contribution_consent:
        raise HTTPException(400,'Explicit contribution consent is required. Saving to My Library is not consent to contribute.')
    if payload.content_type=='drill':
        obj=db.get(UserDrill,payload.user_content_id)
        if not obj or obj.owner_key != payload.owner_key: raise HTTPException(404,'User drill not found')
        snapshot={c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name not in {'created_at','updated_at'}}
        obj.contribution_consent=True; obj.library_state='Submitted to EDGE'
    else:
        obj=db.get(UserPractice,payload.user_content_id)
        if not obj or obj.owner_key != payload.owner_key: raise HTTPException(404,'User practice not found')
        snapshot={c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name not in {'created_at','updated_at'}}
        segments=db.query(PracticeSegment).filter(PracticeSegment.user_practice_id==obj.user_practice_id).order_by(PracticeSegment.segment_number).all()
        snapshot['segments']=[{c.name:getattr(s,c.name) for c in s.__table__.columns if c.name!='id'} for s in segments]
        obj.contribution_consent=True; obj.library_state='Submitted to EDGE'
    qid='CQ-'+uuid.uuid4().hex[:12].upper()
    db.add(Contribution(queue_id=qid,content_type=payload.content_type,user_content_id=payload.user_content_id,owner_key=payload.owner_key,
                        consent_verified=True,snapshot_json=json.dumps(snapshot,default=str),notes=payload.notes))
    db.commit()
    return {'queue_id':qid,'status':'Submitted','snapshot_created':True,'message':'A snapshot was submitted; later private edits do not change the review copy.'}
@app.post(
    '/v1/development-goals',
    dependencies=[Depends(require_write_key)]
)
def create_development_goal(
    payload: DevelopmentGoalCreate,
    db: Session = Depends(get_db)
):
    goal_id = 'DG-' + uuid.uuid4().hex[:12].upper()

    rec = DevelopmentGoal(
        goal_id=goal_id,
        owner_key=payload.owner_key,
        title=payload.title,
        description=payload.description,
        status='Active'
    )

    db.add(rec)
    db.commit()

    return {
        'goal_id': goal_id,
        'title': rec.title,
        'status': rec.status
    }


@app.get(
    '/v1/development-goals',
    dependencies=[Depends(require_write_key)]
)
def list_development_goals(
    owner_key: str,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(DevelopmentGoal)
        .filter(DevelopmentGoal.owner_key == owner_key)
        .order_by(DevelopmentGoal.updated_at.desc())
        .all()
    )

    return {
        'count': len(rows),
        'items': [
            {
                'goal_id': r.goal_id,
                'title': r.title,
                'description': r.description,
                'status': r.status
            }
            for r in rows
        ]
    }


@app.post(
    '/v1/practice-reviews',
    dependencies=[Depends(require_write_key)]
)
def save_practice_review(
    payload: PracticeReviewCreate,
    db: Session = Depends(get_db)
):
    if payload.user_practice_id is not None:
        practice = db.get(UserPractice, payload.user_practice_id)

        if not practice or practice.owner_key != payload.owner_key:
            raise HTTPException(
                404,
                'User practice not found'
            )

    if payload.development_goal_id is not None:
        goal = db.get(
            DevelopmentGoal,
            payload.development_goal_id
        )

        if not goal or goal.owner_key != payload.owner_key:
            raise HTTPException(
                404,
                'Development goal not found'
            )

    review_id = 'PR-' + uuid.uuid4().hex[:12].upper()

    review = PracticeReview(
        review_id=review_id,
        owner_key=payload.owner_key,
        user_practice_id=payload.user_practice_id,
        development_goal_id=payload.development_goal_id,
        practice_goal=payload.practice_goal,
        overall_result=payload.overall_result,
        what_worked=payload.what_worked,
        what_didnt=payload.what_didnt,
        overall_observation=payload.overall_observation,
        next_practice_decision=payload.next_practice_decision,
        next_focus=payload.next_focus
    )

    db.add(review)

    # Make sure the parent review exists before
    # child activity-review rows are inserted.
    db.flush()

    for activity in payload.activities:
        db.add(
            PracticeActivityReview(
                review_id=review_id,
                segment_number=activity.segment_number,
                activity_source=activity.activity_source,
                activity_id=activity.activity_id,
                activity_name=activity.activity_name,
                intended_goal=activity.intended_goal,
                goal_delivery=activity.goal_delivery,
                focus_element_1=activity.focus_element_1,
                focus_element_1_result=activity.focus_element_1_result,
                focus_element_2=activity.focus_element_2,
                focus_element_2_result=activity.focus_element_2_result,
                coach_observation=activity.coach_observation,
                adjustment_next_time=activity.adjustment_next_time,
                would_use_again=activity.would_use_again
            )
        )

    db.commit()

    return {
        'review_id': review_id,
        'activities_saved': len(payload.activities),
        'next_practice_decision': payload.next_practice_decision
    }


@app.get(
    '/v1/practice-reviews',
    dependencies=[Depends(require_write_key)]
)
def list_practice_reviews(
    owner_key: str,
    development_goal_id: str | None = None,
    db: Session = Depends(get_db)
):
    qry = (
        db.query(PracticeReview)
        .filter(PracticeReview.owner_key == owner_key)
    )

    if development_goal_id is not None:
        qry = qry.filter(
            PracticeReview.development_goal_id
            == development_goal_id
        )

    reviews = (
        qry.order_by(PracticeReview.created_at.desc())
        .all()
    )

    items = []

    for review in reviews:
        activities = (
            db.query(PracticeActivityReview)
            .filter(
                PracticeActivityReview.review_id
                == review.review_id
            )
            .order_by(PracticeActivityReview.id)
            .all()
        )

        items.append({
            'review_id': review.review_id,
            'user_practice_id': review.user_practice_id,
            'development_goal_id': (
                review.development_goal_id
            ),
            'practice_goal': review.practice_goal,
            'overall_result': review.overall_result,
            'what_worked': review.what_worked,
            'what_didnt': review.what_didnt,
            'overall_observation': (
                review.overall_observation
            ),
            'next_practice_decision': (
                review.next_practice_decision
            ),
            'next_focus': review.next_focus,
            'created_at': (
                review.created_at.isoformat()
                if review.created_at is not None
                else None
            ),
            'activities': [
                {
                    'segment_number': a.segment_number,
                    'activity_source': a.activity_source,
                    'activity_id': a.activity_id,
                    'activity_name': a.activity_name,
                    'intended_goal': a.intended_goal,
                    'goal_delivery': a.goal_delivery,
                    'focus_element_1': (
                        a.focus_element_1
                    ),
                    'focus_element_1_result': (
                        a.focus_element_1_result
                    ),
                    'focus_element_2': (
                        a.focus_element_2
                    ),
                    'focus_element_2_result': (
                        a.focus_element_2_result
                    ),
                    'coach_observation': (
                        a.coach_observation
                    ),
                    'adjustment_next_time': (
                        a.adjustment_next_time
                    ),
                    'would_use_again': (
                        a.would_use_again
                    )
                }
                for a in activities
            ]
        })

    return {
        'count': len(items),
        'items': items
    }
@app.post(
    '/v1/game-check-ins',
    dependencies=[Depends(require_write_key)]
)
def save_game_check_in(
    payload: GameCheckInCreate,
    db: Session = Depends(get_db)
):
    goal = db.get(DevelopmentGoal, payload.development_goal_id)

    if not goal or goal.owner_key != payload.owner_key:
        raise HTTPException(
            404,
            'Development goal not found'
        )

    check_in_id = 'GC-' + uuid.uuid4().hex[:12].upper()

    rec = GameCheckIn(
        check_in_id=check_in_id,
        owner_key=payload.owner_key,
        development_goal_id=payload.development_goal_id,
        game_label=payload.game_label,
        game_date=payload.game_date,
        transfer_result=payload.transfer_result,
        what_showed_up=payload.what_showed_up,
        what_still_breaks_down=payload.what_still_breaks_down,
        coach_observation=payload.coach_observation,
        next_implication=payload.next_implication,
        next_practice_decision=payload.next_practice_decision
    )

    db.add(rec)
    db.commit()

    return {
        'check_in_id': rec.check_in_id,
        'development_goal_id': rec.development_goal_id,
        'transfer_result': rec.transfer_result,
        'next_practice_decision': rec.next_practice_decision,
        'status': 'Saved'
    }


@app.get(
    '/v1/game-check-ins',
    dependencies=[Depends(require_write_key)]
)
def list_game_check_ins(
    owner_key: str,
    development_goal_id: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(GameCheckIn).filter(
        GameCheckIn.owner_key == owner_key
    )

    if development_goal_id is not None:
        query = query.filter(
            GameCheckIn.development_goal_id == development_goal_id
        )

    rows = (
        query
        .order_by(GameCheckIn.created_at.desc())
        .all()
    )

    return {
        'count': len(rows),
        'items': [
            {
                'check_in_id': r.check_in_id,
                'development_goal_id': r.development_goal_id,
                'game_label': r.game_label,
                'game_date': r.game_date,
                'transfer_result': r.transfer_result,
                'what_showed_up': r.what_showed_up,
                'what_still_breaks_down': r.what_still_breaks_down,
                'coach_observation': r.coach_observation,
                'next_implication': r.next_implication,
                'next_practice_decision': r.next_practice_decision,
                'created_at': (
                    r.created_at.isoformat()
                    if r.created_at is not None
                    else None
                )
            }
            for r in rows
        ]
    }

@app.get(
    '/v1/development-progress',
    dependencies=[Depends(require_write_key)]
)
def get_development_progress(
    owner_key: str,
    development_goal_id: str,
    db: Session = Depends(get_db)
):
    goal = db.get(DevelopmentGoal, development_goal_id)

    if not goal or goal.owner_key != owner_key:
        raise HTTPException(
            404,
            'Development goal not found'
        )

    practice_reviews = (
        db.query(PracticeReview)
        .filter(
            PracticeReview.owner_key == owner_key,
            PracticeReview.development_goal_id == development_goal_id
        )
        .order_by(PracticeReview.created_at.asc())
        .all()
    )

    game_check_ins = (
        db.query(GameCheckIn)
        .filter(
            GameCheckIn.owner_key == owner_key,
            GameCheckIn.development_goal_id == development_goal_id
        )
        .order_by(GameCheckIn.created_at.asc())
        .all()
    )

    practice_items = []

    for review in practice_reviews:
        activities = (
            db.query(PracticeActivityReview)
            .filter(
                PracticeActivityReview.review_id == review.review_id
            )
           .order_by(PracticeActivityReview.segment_number.asc())
            .all()
        )

        practice_items.append({
            'review_id': review.review_id,
            'user_practice_id': review.user_practice_id,
            'practice_goal': review.practice_goal,
            'overall_result': review.overall_result,
            'what_worked': review.what_worked,
            'what_didnt': review.what_didnt,
            'overall_observation': review.overall_observation,
            'next_practice_decision': review.next_practice_decision,
            'next_focus': review.next_focus,
            'created_at': (
                review.created_at.isoformat()
                if review.created_at is not None
                else None
            ),
            'activities': [
                {
                    'segment_number': a.segment_number,
                    'activity_source': a.activity_source,
                    'activity_id': a.activity_id,
                    'activity_name': a.activity_name,
                    'intended_goal': a.intended_goal,
                    'goal_delivery': a.goal_delivery,
                    'focus_element_1': a.focus_element_1,
                    'focus_element_1_result': (
                        a.focus_element_1_result
                    ),
                    'focus_element_2': a.focus_element_2,
                    'focus_element_2_result': (
                        a.focus_element_2_result
                    ),
                    'coach_observation': a.coach_observation,
                    'adjustment_next_time': (
                        a.adjustment_next_time
                    ),
                    'would_use_again': a.would_use_again
                }
                for a in activities
            ]
        })

    game_items = [
        {
            'check_in_id': r.check_in_id,
            'game_label': r.game_label,
            'game_date': r.game_date,
            'transfer_result': r.transfer_result,
            'what_showed_up': r.what_showed_up,
            'what_still_breaks_down': (
                r.what_still_breaks_down
            ),
            'coach_observation': r.coach_observation,
            'next_implication': r.next_implication,
            'next_practice_decision': (
                r.next_practice_decision
            ),
            'created_at': (
                r.created_at.isoformat()
                if r.created_at is not None
                else None
            )
        }
        for r in game_check_ins
    ]

    timeline = []

    for review in practice_items:
        timeline.append({
            'evidence_type': 'practice_review',
            'evidence_id': review['review_id'],
            'created_at': review['created_at'],
            'result': review['overall_result'],
            'observation': review['overall_observation'],
            'next_decision': (
                review['next_practice_decision']
            )
        })

    for check_in in game_items:
        timeline.append({
            'evidence_type': 'game_check_in',
            'evidence_id': check_in['check_in_id'],
            'created_at': check_in['created_at'],
            'result': check_in['transfer_result'],
            'observation': check_in['coach_observation'],
            'next_decision': (
                check_in['next_practice_decision']
            )
        })

    timeline.sort(
        key=lambda item: item['created_at'] or ''
    )

    return {
        'development_goal': {
            'goal_id': goal.goal_id,
            'title': goal.title,
            'description': goal.description,
            'status': goal.status,
            'created_at': (
                goal.created_at.isoformat()
                if goal.created_at is not None
                else None
            ),
            'updated_at': (
                goal.updated_at.isoformat()
                if goal.updated_at is not None
                else None
            )
        },
        'practice_review_count': len(practice_items),
        'game_check_in_count': len(game_items),
        'practice_reviews': practice_items,
        'game_check_ins': game_items,
        'evidence_timeline': timeline
    }
