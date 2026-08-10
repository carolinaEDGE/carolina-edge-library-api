import json, os, uuid
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Drill, Edge5Evaluation, UserDrill, UserPractice, PracticeSegment, Contribution
from .schemas import Edge5Input, UserDrillCreate, UserPracticeCreate, ContributionCreate
from .seed import seed_drills

VERSION="0.1.0"
app=FastAPI(title="Carolina EDGE Library API", version=VERSION, description="Drill and practice library service for Carolina EDGE. EDGE 5 Elements is informative, never a creation/use gate.")

Base.metadata.create_all(bind=engine)
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
        'game_like_evidence':d.game_like_evidence,'age_context_notes':d.age_context_notes
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
                  ice: str|None=None, goalies: int|None=None, limit: int=Query(10,ge=1,le=50), db:Session=Depends(get_db)):
    qry=db.query(Drill).filter(Drill.active.is_(True))
    if q:
        like=f"%{q}%"; qry=qry.filter(or_(Drill.name.ilike(like),Drill.primary_game_problem.ilike(like),Drill.target_behaviors.ilike(like),Drill.search_tags_json.ilike(like)))
    if game_problem: qry=qry.filter(Drill.primary_game_problem.ilike(f"%{game_problem}%"))
    if family: qry=qry.filter(Drill.family.ilike(f"%{family}%"))
    if age: qry=qry.filter(or_(Drill.best_ages.is_(None), Drill.best_ages.ilike(f"%{age}%")))
    if ice: qry=qry.filter(Drill.ice_footprint.ilike(f"%{ice}%"))
    rows=qry.limit(limit).all()
    return {'count':len(rows),'items':[drill_to_dict(x) for x in rows], 'note':'EDGE 5 Elements should be evaluated in the coach\'s actual context; library search does not block lower-scoring drills.'}

@app.get('/v1/drills/{drill_id}')
def get_drill(drill_id:str, db:Session=Depends(get_db)):
    d=db.get(Drill,drill_id)
    if not d: raise HTTPException(404,'Drill not found')
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


@app.post('/v1/contributions',dependencies=[Depends(require_write_key)])
def submit_contribution(payload:ContributionCreate,db:Session=Depends(get_db)):
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
