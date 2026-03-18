"""Force-update page schemas in the database from seed definitions."""
import json
from src.adapters.http.dependency_injection import SessionLocal
from sqlalchemy import text
from src.infrastructure.persistence.seed_schemas_fiscal import (
    OPERATION_NATURES_PAGE_SCHEMA,
    OPERATION_NATURES_FORM_SCHEMA,
    FISCAL_RULES_FORM_SCHEMA,
)

db = SessionLocal()

for page_key, schema in [
    ("operation_natures", OPERATION_NATURES_PAGE_SCHEMA),
    ("operation_natures_form", OPERATION_NATURES_FORM_SCHEMA),
    ("fiscal_rules_form", FISCAL_RULES_FORM_SCHEMA),
]:
    schema_json = json.dumps(schema, ensure_ascii=False)
    result = db.execute(
        text("UPDATE page_versions SET schema_json = :schema, updated_at = NOW() WHERE page_key = :key AND status = 'published'"),
        {"schema": schema_json, "key": page_key},
    )
    print(f"Updated {page_key}: {result.rowcount} rows")

db.commit()
db.close()
print("Done!")
