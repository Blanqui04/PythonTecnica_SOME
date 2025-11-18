"""Check what references exist in each table"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.database_connection import PostgresConn
import configparser

def check_table_refs(table_name: str):
    """Check references in a table"""
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    
    # Load DB config
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    
    db = PostgresConn(
        host=config['database']['host'],
        database=config['database']['database'],
        user=config['database']['user'],
        password=config['database']['password'],
        port=int(config['database']['port'])
    )
    
    # Map table to ref column
    ref_columns = {
        'mesureshoytom': 'ref_some',
        'mesurestorsio': 'ref_some',
        'mesureszwick': 'reference'
    }
    
    ref_col = ref_columns.get(table_name)
    
    try:
        query = f'''
            SELECT DISTINCT {ref_col}
            FROM "1000_SQB_qualitat".{table_name}
            WHERE {ref_col} IS NOT NULL
            ORDER BY {ref_col}
            LIMIT 20
        '''
        
        result = db.fetchall(query)
        
        if result:
            print(f"\nFound {len(result)} distinct references (first 20):")
            for i, row in enumerate(result, 1):
                print(f"  {i}. {row[0]}")
        else:
            print("No references found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    for table in ['mesureshoytom', 'mesurestorsio', 'mesureszwick']:
        check_table_refs(table)
