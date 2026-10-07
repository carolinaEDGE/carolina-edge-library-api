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
    assert j["drills"]==65
    assert j["active_drills"]==65

def test_only_approved_publish_records_are_searchable():
    r=client.get("/v1/drills",params={"limit":50})
    assert r.status_code==200
    j=r.json()
    expected = {
        "EDGE-A002","EDGE-A006","EDGE-A009","EDGE-A010","EDGE-A011","EDGE-A012",
        "EDGE-A014","EDGE-A106","EDGE-A107","EDGE-A108","EDGE-A109","EDGE-A110",
        "EDGE-A1700","EDGE-A196","EDGE-A197","EDGE-A198","EDGE-A218","EDGE-A219",
        "EDGE-A220","EDGE-A291","EDGE-A292","EDGE-A293","EDGE-A294","EDGE-A295",
        "EDGE-A1182","EDGE-A194","EDGE-A170","EDGE-A254",
        "EDGE-A190","EDGE-A544","EDGE-A1241","EDGE-A1364",
        "EDGE-A1594","EDGE-A1339","EDGE-A1198","EDGE-A1427"
    }
    assert j["count"]==36
    assert {x["drill_id"] for x in j["items"]} == expected
    assert all(x["surface_policy"]=="PUBLISH_NOW" for x in j["items"])
    assert all(x["publication_status"]=="READY FOR IMPORT" for x in j["items"])

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


def test_existing_legacy_rows_are_backfilled_to_hold():
    from app.db import SessionLocal
    from app.models import Drill
    from app.seed import seed_drills

    with SessionLocal() as db:
        legacy = db.get(Drill, "IQ-001")
        assert legacy is not None
        legacy.publication_status = None
        legacy.surface_policy = None
        legacy.is_searchable = True
        db.commit()

        seed_drills(db)
        db.refresh(legacy)
        assert legacy.publication_status == "LEGACY_HOLD"
        assert legacy.surface_policy == "REFERENCE_ONLY"
        assert legacy.is_searchable is False


def test_manual_b_candidates_are_seeded_with_selective_publication():
    from app.db import SessionLocal
    from app.models import Drill
    promoted = {
        "EDGE-A1700","EDGE-A196","EDGE-A197","EDGE-A198","EDGE-A218","EDGE-A219",
        "EDGE-A220","EDGE-A291","EDGE-A292","EDGE-A293","EDGE-A294","EDGE-A295"
    }
    hidden = {"EDGE-A1189","EDGE-A221","EDGE-A222","EDGE-A346"}
    candidate_ids = promoted | hidden
    with SessionLocal() as db:
        rows = db.query(Drill).filter(Drill.drill_id.in_(candidate_ids)).all()
        assert {r.drill_id for r in rows} == candidate_ids
        for r in rows:
            assert r.source_asset
            assert r.source_text
            assert r.adaptation_text
            if r.drill_id in promoted:
                assert r.is_searchable is True
                assert r.surface_policy == "PUBLISH_NOW"
                assert r.publication_status == "READY FOR IMPORT"
            else:
                assert r.is_searchable is False
                assert r.surface_policy == "DO_NOT_SURFACE"
                assert r.publication_status == "ADAPTATION_QA"

    r = client.get("/v1/drills/EDGE-A218")
    assert r.status_code == 200

    r = client.get("/v1/drills/EDGE-A221")
    assert r.status_code == 404


def test_promoted_adaptations_are_searchable_and_remaining_candidates_stay_hidden():
    promoted = {
        "EDGE-A1700","EDGE-A196","EDGE-A197","EDGE-A198","EDGE-A218","EDGE-A219",
        "EDGE-A220","EDGE-A291","EDGE-A292","EDGE-A293","EDGE-A294","EDGE-A295"
    }
    hidden = {"EDGE-A1189","EDGE-A221","EDGE-A222","EDGE-A346"}

    for drill_id in promoted:
        r = client.get(f"/v1/drills/{drill_id}")
        assert r.status_code == 200
        j = r.json()
        assert j["publication_status"] == "READY FOR IMPORT"
        assert j["surface_policy"] == "PUBLISH_NOW"

    for drill_id in hidden:
        r = client.get(f"/v1/drills/{drill_id}")
        assert r.status_code == 404

    r = client.get("/v1/drills", params={"q":"puck support","limit":50})
    assert r.status_code == 200
    ids = {x["drill_id"] for x in r.json()["items"]}
    assert {"EDGE-A218","EDGE-A219","EDGE-A197","EDGE-A198"} & ids
    assert not (hidden & ids)


def test_retrieval_taxonomy_is_seeded_for_publish_records():
    from app.db import SessionLocal
    from app.models import Drill
    ids = {"EDGE-A002","EDGE-A009","EDGE-A218","EDGE-A219","EDGE-A295"}
    with SessionLocal() as db:
        rows = {r.drill_id:r for r in db.query(Drill).filter(Drill.drill_id.in_(ids)).all()}
        assert rows["EDGE-A002"].family == "Retrieval / Breakout"
        assert "forecheck pressure" in (rows["EDGE-A002"].search_tags_json or "")
        assert rows["EDGE-A009"].family == "Transition / Numerical Advantage"
        assert "3v2" in (rows["EDGE-A009"].search_tags_json or "")
        assert rows["EDGE-A218"].family == "Puck Support / Small-Area Game"
        assert "puck support" in (rows["EDGE-A218"].search_tags_json or "")
        assert rows["EDGE-A219"].family == "Puck Support / Small-Area Game"
        assert "penalty kill" in (rows["EDGE-A219"].search_tags_json or "")
        assert rows["EDGE-A295"].family == "Puck Support / Offensive Zone"
        assert "seam" in (rows["EDGE-A295"].search_tags_json or "")


def test_gap_fill_activities_are_source_verified_and_searchable():
    expected = {
        "EDGE-A1182":"Faceoff / Small-Area Game",
        "EDGE-A194":"Net-Front / Rebound Game",
        "EDGE-A170":"Possession / Support",
        "EDGE-A254":"Net-Front / Point Support",
    }
    for drill_id, family in expected.items():
        r = client.get(f"/v1/drills/{drill_id}")
        assert r.status_code == 200
        j = r.json()
        assert j["publication_status"] == "READY FOR IMPORT"
        assert j["surface_policy"] == "PUBLISH_NOW"
        assert j["source_evidence"] == "VERIFIED SOURCE TEXT"

    scenarios = [
        ("faceoff", "EDGE-A1182"),
        ("rebound", "EDGE-A194"),
        ("outside support", "EDGE-A170"),
        ("screen", "EDGE-A254"),
    ]
    for query, drill_id in scenarios:
        r = client.get("/v1/drills", params={"q":query,"limit":50})
        assert r.status_code == 200
        ids = {x["drill_id"] for x in r.json()["items"]}
        assert drill_id in ids, (query, ids)


def test_second_gap_fill_set_is_source_verified_and_searchable():
    expected = {
        "EDGE-A190":"Breakout / Puck Support",
        "EDGE-A544":"Retrieval / Forecheck",
        "EDGE-A1241":"Goalie / Rebound Control",
        "EDGE-A1364":"Transition / Regroup",
    }
    for drill_id, family in expected.items():
        r = client.get(f"/v1/drills/{drill_id}")
        assert r.status_code == 200
        j = r.json()
        assert j["publication_status"] == "READY FOR IMPORT"
        assert j["surface_policy"] == "PUBLISH_NOW"
        assert j["source_evidence"] == "VERIFIED SOURCE TEXT"

    scenarios = [
        ("breakout", "EDGE-A190"),
        ("forecheck", "EDGE-A544"),
        ("goalie", "EDGE-A1241"),
        ("regroup", "EDGE-A1364"),
    ]
    for query, drill_id in scenarios:
        r = client.get("/v1/drills", params={"q":query,"limit":50})
        assert r.status_code == 200
        ids = {x["drill_id"] for x in r.json()["items"]}
        assert drill_id in ids, (query, ids)


def test_defensive_zone_and_forecheck_gap_fill_set():
    expected = {
        "EDGE-A1594":"Defensive Zone / Coverage",
        "EDGE-A1339":"Defensive Zone / Net-Front Coverage",
        "EDGE-A1198":"Forecheck / Breakout",
        "EDGE-A1427":"Forecheck / Transition",
    }
    for drill_id, family in expected.items():
        r = client.get(f"/v1/drills/{drill_id}")
        assert r.status_code == 200
        j = r.json()
        assert j["publication_status"] == "READY FOR IMPORT"
        assert j["surface_policy"] == "PUBLISH_NOW"
        assert j["source_evidence"] == "VERIFIED SOURCE TEXT"

    scenarios = [
        ("defensive zone", "EDGE-A1594"),
        ("coverage", "EDGE-A1339"),
        ("forecheck", "EDGE-A1198"),
        ("continuous", "EDGE-A1427"),
    ]
    for query, drill_id in scenarios:
        r = client.get("/v1/drills", params={"q":query,"limit":50})
        assert r.status_code == 200
        ids = {x["drill_id"] for x in r.json()["items"]}
        assert drill_id in ids, (query, ids)
