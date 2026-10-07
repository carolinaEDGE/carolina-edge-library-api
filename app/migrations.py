from sqlalchemy import inspect

V02_COLUMNS = {
    "record_type": "VARCHAR(40)",
    "route": "VARCHAR(40)",
    "publication_status": "VARCHAR(50)",
    "surface_policy": "VARCHAR(50)",
    "source_evidence": "VARCHAR(40)",
    "source_text": "TEXT",
    "source_asset": "TEXT",
    "source_boundary": "TEXT",
    "representative_information": "TEXT",
    "player_decisions": "TEXT",
    "space_organization": "TEXT",
    "coach_notes": "TEXT",
    "adaptation_text": "TEXT",
    "schema_version": "VARCHAR(60)",
    "is_searchable": "BOOLEAN NOT NULL DEFAULT FALSE",
}

def migrate_v02(engine):
    inspector = inspect(engine)
    if "drills" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("drills")}
    with engine.begin() as conn:
        for name, ddl in V02_COLUMNS.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE drills ADD COLUMN {name} {ddl}")
