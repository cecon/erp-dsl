from src.adapters.http.dependency_injection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check table
r = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name='natureza_operacao'")).fetchall()
print("Table exists:", bool(r))
if r:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='natureza_operacao' ORDER BY ordinal_position")).fetchall()
    for c in cols:
        print(f"  {c[0]}: {c[1]}")

# Check page schema  
r2 = db.execute(text("SELECT page_key, scope FROM published_schemas WHERE page_key='natureza_operacao'")).fetchall()
print("Page schema:", bool(r2))

# Check generic entities
r3 = db.execute(text("SELECT DISTINCT entity_type FROM generic_entities WHERE entity_type LIKE '%natureza%'")).fetchall()
print("Generic entities with natureza:", r3)

# List all entity types
r4 = db.execute(text("SELECT DISTINCT entity_type FROM generic_entities LIMIT 20")).fetchall()
print("All entity types:", [x[0] for x in r4])

# List all page keys  
r5 = db.execute(text("SELECT page_key FROM published_schemas")).fetchall()
print("All page keys:", [x[0] for x in r5])

db.close()
