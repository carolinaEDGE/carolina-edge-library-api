import os
os.environ['DATABASE_URL']='sqlite:///./test_library.db'
os.environ['WRITE_API_KEY']='testkey'
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
def test_health_and_seed():
    r=client.get('/health'); assert r.status_code==200; assert r.json()['drills']==25

def test_search():
    r=client.get('/v1/drills',params={'q':'retrieval'}); assert r.status_code==200; assert r.json()['count']>0

def test_edge5_nonblocking():
    body={'total_players':7,'active_players':3,'fun_challenging':True,'age_appropriate':True,'game_like_context':True,'decisions':True,
          'decision_cues':'Forechecker pressure','decision_options':'Reverse, wheel, pass'}
    r=client.post('/v1/evaluations',json=body); assert r.status_code==200
    j=r.json(); assert j['edge_5_elements_score']==4; assert j['results']['repetitions'] is False; assert j['blocking'] is False

def test_save_and_contribute():
    h={'x-api-key':'testkey'}
    r=client.post('/v1/user-drills',headers=h,json={'owner_key':'coach-test','title':'Test Drill','players':8}); assert r.status_code==200
    uid=r.json()['user_drill_id']
    r=client.post('/v1/contributions',headers=h,json={'owner_key':'coach-test','content_type':'drill','user_content_id':uid,'contribution_consent':True}); assert r.status_code==200
    assert r.json()['snapshot_created'] is True
