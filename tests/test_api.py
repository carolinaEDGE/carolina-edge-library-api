import os
from pathlib import Path

TEST_DB = Path("./test_library.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"]="sqlite:///./test_library.db"
os.environ["WRITE_API_KEY"]="testkey"

from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health_and_seed():
    r=client.get("/health")
    assert r.status_code==200
    j=r.json()
    assert j["version"]=="0.2.0-staging"
    assert j["drills"]==37
    assert j["active_drills"]==37

def test_only_verified_publish_seed_is_searchable():
    r=client.get("/v1/drills",params={"limit":50})
    assert r.status_code==200
    j=r.json()
    assert j["count"]==12
    assert {x["drill_id"] for x in j["items"]} == {
        "EDGE-A002","EDGE-A006","EDGE-A009","EDGE-A010","EDGE-A011","EDGE-A012",
        "EDGE-A014","EDGE-A106","EDGE-A107","EDGE-A108","EDGE-A109","EDGE-A110"
    }
    assert all(x["surface_policy"]=="PUBLISH_NOW" for x in j["items"])

def test_legacy_drill_is_isolated():
    r=client.get("/v1/drills/IQ-001")
    assert r.status_code==404

def test_source_provenance_is_returned():
    r=client.get("/v1/drills/EDGE-A002")
    assert r.status_code==200
    j=r.json()
    assert j["source_evidence"]=="VERIFIED"
    assert "Forwards line up" in j["source_text"]
    assert j["source_boundary"].startswith("Source-derived fields only")

def test_edge5_nonblocking():
    body={"total_players":7,"active_players":3,"fun_challenging":True,"age_appropriate":True,"game_like_context":True,"decisions":True,
          "decision_cues":"Forechecker pressure","decision_options":"Reverse, wheel, pass"}
    r=client.post("/v1/evaluations",json=body)
    assert r.status_code==200
    j=r.json()
    assert j["edge_5_elements_score"]==4
    assert j["results"]["repetitions"] is False
    assert j["blocking"] is False

def test_save_and_contribute():
    h={"x-api-key":"testkey"}
    r=client.post("/v1/user-drills",headers=h,json={"owner_key":"coach-test","title":"Test Drill","players":8})
    assert r.status_code==200
    uid=r.json()["user_drill_id"]
    r=client.post("/v1/contributions",headers=h,json={"owner_key":"coach-test","content_type":"drill","user_content_id":uid,"contribution_consent":True})
    assert r.status_code==200
    assert r.json()["snapshot_created"] is True


def test_practice_edge_retrieval_scenarios():
    scenarios = [
        ("angling", {"EDGE-A106","EDGE-A107","EDGE-A108","EDGE-A109"}),
        ("pressure", {"EDGE-A002","EDGE-A107"}),
        ("transition", {"EDGE-A009","EDGE-A108","EDGE-A109"}),
        ("2v1", {"EDGE-A009","EDGE-A010","EDGE-A011"}),
        ("puck protection", {"EDGE-A006","EDGE-A012","EDGE-A110"}),
    ]
    for query, expected_any in scenarios:
        r = client.get("/v1/drills", params={"q": query, "limit": 50})
        assert r.status_code == 200
        ids = {x["drill_id"] for x in r.json()["items"]}
        assert ids & expected_any, (query, ids)

def test_no_reference_or_legacy_leakage_in_retrieval():
    for query in ["angling","pressure","transition","battle","1v1"]:
        r = client.get("/v1/drills", params={"q": query, "limit": 50})
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["drill_id"].startswith("EDGE-A")
            assert item["surface_policy"] == "PUBLISH_NOW"
            assert item["publication_status"] == "READY FOR IMPORT"


def test_seed_values_fit_declared_string_columns():
    from sqlalchemy import String
    from app.models import Drill
    from app.seed import _edge_rows, _normalize_goalies, _ice_footprint

    for d in _edge_rows():
        mapped = {
            "drill_id": d["edge_id"],
            "version": "2.0",
            "name": d["title"],
            "review_status": "SOURCE VERIFIED",
            "primary_game_problem": d.get("game_problem"),
            "goalies": _normalize_goalies(d.get("goalie")),
            "ice_footprint": _ice_footprint(d.get("space_organization")),
            "record_type": d.get("record_type"),
            "route": d.get("route"),
            "publication_status": d.get("publication_status"),
            "surface_policy": d.get("surface_policy"),
            "source_evidence": d.get("source_evidence"),
            "schema_version": d.get("schema_version"),
        }
        for name, value in mapped.items():
            if value is None:
                continue
            col = Drill.__table__.columns[name]
            if isinstance(col.type, String) and col.type.length:
                assert len(str(value)) <= col.type.length, (name, value, col.type.length)
