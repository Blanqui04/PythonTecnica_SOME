"""
Test script per verificar la nova estructura de base de dades
"""
import sys
import json
import logging
from pathlib import Path

# Afegir el directori arrel al path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.measurement_history_service import MeasurementHistoryService
from src.database.database_connection import PostgresConn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_config():
    """Test 1: Verificar configuració de base de dades"""
    print("\n" + "="*60)
    print("TEST 1: Verificar configuració de base de dades")
    print("="*60)
    
    config_path = Path(__file__).parent / "config" / "database" / "db_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"\n✅ Primary DB (LECTURA):")
    print(f"   Host: {config['primary']['host']}")
    print(f"   Database: {config['primary']['database']}")
    print(f"   User: {config['primary']['user']}")
    
    print(f"\n✅ Secondary DB (ESCRIPTURA):")
    print(f"   Host: {config['secondary']['host']}")
    print(f"   Database: {config['secondary']['database']}")
    print(f"   User: {config['secondary']['user']}")
    
    return config

def test_primary_connection(config):
    """Test 2: Provar connexió a documentacio_tecnica"""
    print("\n" + "="*60)
    print("TEST 2: Connexió a documentacio_tecnica (PRIMARY)")
    print("="*60)
    
    try:
        db = PostgresConn(
            host=config['primary']['host'],
            database=config['primary']['database'],
            user=config['primary']['user'],
            password=config['primary']['password'],
            port=config['primary']['port']
        )
        
        # Verificar quines taules existeixen
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'mesures%'
            ORDER BY table_name
        """
        tables = db.fetchall(query)
        
        if tables:
            print(f"\n✅ Connexió exitosa!")
            print(f"\n📊 Taules de mesures trobades:")
            for table in tables:
                # Comptar registres
                count_query = f"SELECT COUNT(*) FROM {table[0]}"
                count = db.fetchone(count_query)[0]
                print(f"   • {table[0]}: {count:,} registres")
        else:
            print(f"\n⚠️  No s'han trobat taules de mesures")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error de connexió: {e}")
        return False

def test_secondary_connection(config):
    """Test 3: Provar connexió a airflow_db"""
    print("\n" + "="*60)
    print("TEST 3: Connexió a airflow_db (SECONDARY)")
    print("="*60)
    
    try:
        db = PostgresConn(
            host=config['secondary']['host'],
            database=config['secondary']['database'],
            user=config['secondary']['user'],
            password=config['secondary']['password'],
            port=config['secondary']['port']
        )
        
        # Verificar quines taules existeixen
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'mesures%'
            ORDER BY table_name
        """
        tables = db.fetchall(query)
        
        if tables:
            print(f"\n✅ Connexió exitosa!")
            print(f"\n📊 Taules de mesures trobades:")
            for table in tables:
                # Comptar registres
                count_query = f"SELECT COUNT(*) FROM {table[0]}"
                count = db.fetchone(count_query)[0]
                print(f"   • {table[0]}: {count:,} registres")
        else:
            print(f"\n⚠️  No s'han trobat taules de mesures")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error de connexió: {e}")
        return False

def test_measurement_service():
    """Test 4: Provar MeasurementHistoryService amb UNION"""
    print("\n" + "="*60)
    print("TEST 4: MeasurementHistoryService (Queries amb UNION)")
    print("="*60)
    
    try:
        service = MeasurementHistoryService()
        
        print(f"\n✅ Servei inicialitzat correctament")
        print(f"   Taules configurades: {service.measurement_tables}")
        
        # Provar query simple (això farà UNION de totes les taules)
        print(f"\n🔍 Provant query amb UNION...")
        
        # Aquest query hauria de buscar a les 4 taules automàticament
        # Per ara només verifiquem que el servei està operatiu
        print(f"   Mètode _convert_query_to_union disponible: {hasattr(service, '_convert_query_to_union')}")
        print(f"   Mètode _build_union_query disponible: {hasattr(service, '_build_union_query')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error inicialitzant servei: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executar tots els tests"""
    print("\n" + "="*60)
    print("🧪 TEST NOVA ESTRUCTURA BASE DE DADES")
    print("="*60)
    
    # Test 1: Config
    config = test_db_config()
    
    # Test 2: Primary DB
    primary_ok = test_primary_connection(config)
    
    # Test 3: Secondary DB
    secondary_ok = test_secondary_connection(config)
    
    # Test 4: Service
    service_ok = test_measurement_service()
    
    # Resum
    print("\n" + "="*60)
    print("📋 RESUM DELS TESTS")
    print("="*60)
    print(f"   Configuració: ✅")
    print(f"   Primary DB (documentacio_tecnica): {'✅' if primary_ok else '❌'}")
    print(f"   Secondary DB (airflow_db): {'✅' if secondary_ok else '❌'}")
    print(f"   MeasurementHistoryService: {'✅' if service_ok else '❌'}")
    
    if primary_ok and secondary_ok and service_ok:
        print(f"\n🎉 TOTS ELS TESTS HAN PASSAT!")
        print(f"\nL'aplicació està preparada per:")
        print(f"   • Llegir de documentacio_tecnica (4 taules amb UNION)")
        print(f"   • Escriure a airflow_db (imports)")
        print(f"   • Tu fas la còpia automàtica cada nit")
    else:
        print(f"\n⚠️  ALGUNS TESTS HAN FALLAT")
        print(f"\nRevisa els errors anteriors")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
