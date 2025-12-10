"""
Script de prova del sistema d'actualitzacions
Prova si pot connectar a GitHub i detectar noves versions
"""

import sys
from pathlib import Path

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_updater():
    """Test del mòdul AutoUpdater"""
    
    print("\n" + "=" * 70)
    print("TEST DEL SISTEMA D'ACTUALITZACIONS")
    print("=" * 70)
    
    try:
        # 1. Importar i mostrar versió actual
        print("\n1️⃣  LLEGINT VERSIÓ ACTUAL...")
        from src.utils.version import APP_VERSION
        print(f"   ✅ Versió local: {APP_VERSION}")
        
        # 2. Importar AutoUpdater
        print("\n2️⃣  CARREGANT MÒDUL AUTOUPDATER...")
        from src.updater.auto_updater import AutoUpdater
        print(f"   ✅ Mòdul carregat correctament")
        
        # 3. Crear instància
        print("\n3️⃣  CREANT INSTÀNCIA D'AUTOUPDATER...")
        updater = AutoUpdater(github_owner="Blanqui04", github_repo="PythonTecnica_SOME")
        print(f"   ✅ Instància creada")
        print(f"   📌 GitHub Owner: {updater.github_owner}")
        print(f"   📌 GitHub Repo: {updater.github_repo}")
        
        # 4. Comprovar actualitzacions
        print("\n4️⃣  COMPROVANT SI HI HA ACTUALITZACIONS A GITHUB...")
        print("   ⏳ Connectant a GitHub API...")
        update_info = updater.check_for_updates()
        
        print(f"\n   📊 RESULTAT:")
        print(f"   ├─ Actualització disponible: {update_info.get('update_available', False)}")
        print(f"   ├─ Versió actual: {APP_VERSION}")
        print(f"   ├─ Versió remota: {update_info.get('version', 'desconeguda')}")
        
        if update_info.get("update_available"):
            print(f"   ├─ 📥 URL de descàrrega: {update_info.get('download_url', 'N/A')[:60]}...")
            print(f"   ├─ 📅 Publicat el: {update_info.get('published_at', 'N/A')}")
            print(f"   └─ 📝 Descripció: {update_info.get('body', 'N/A')[:100]}...")
            print(f"\n   🔔 NOVA VERSIÓ DISPONIBLE!")
        else:
            print(f"   └─ ✅ L'aplicació ja està actualitzada")
        
        # 5. Mostrar resum
        print("\n" + "=" * 70)
        print("RESUM DEL TEST")
        print("=" * 70)
        print(f"✅ Connexió a GitHub: CORRECTA")
        print(f"✅ Versió local detectada: {APP_VERSION}")
        print(f"✅ Mòdul AutoUpdater funcional: SÍ")
        print(f"{'⚠️  Actualització disponible: SÍ' if update_info.get('update_available') else '✅ Sistema actualitzat: SÍ'}")
        print("=" * 70 + "\n")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERROR D'IMPORTACIÓ: {e}")
        print("   Verificar que tots els móduls estiguin correctament instal·lats")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR EN EL TEST: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_updater()
    sys.exit(0 if success else 1)
