"""Simple SQL check for table references"""

# SQL queries to run in pgAdmin or database client

# HOYTOM
print("-- HOYTOM REFERENCES:")
print("""
SELECT DISTINCT ref_some
FROM "1000_SQB_qualitat".mesureshoytom
WHERE ref_some IS NOT NULL
ORDER BY ref_some
LIMIT 10;
""")

# TORSIO
print("\n-- TORSIO REFERENCES:")
print("""
SELECT DISTINCT ref_some
FROM "1000_SQB_qualitat".mesurestorsio
WHERE ref_some IS NOT NULL
ORDER BY ref_some
LIMIT 10;
""")

# ZWICK
print("\n-- ZWICK REFERENCES:")
print("""
SELECT DISTINCT reference
FROM "1000_SQB_qualitat".mesureszwick
WHERE reference IS NOT NULL
ORDER BY reference
LIMIT 10;
""")

# Count rows
print("\n-- ROW COUNTS:")
print("""
SELECT 'hoytom' as table, COUNT(*) FROM "1000_SQB_qualitat".mesureshoytom
UNION ALL
SELECT 'torsio', COUNT(*) FROM "1000_SQB_qualitat".mesurestorsio
UNION ALL
SELECT 'zwick', COUNT(*) FROM "1000_SQB_qualitat".mesureszwick;
""")
