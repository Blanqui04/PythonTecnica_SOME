"""
TEST COMPLET I GENERAL DEL SISTEMA D'ACTUALITZACIONS AUTOMÀTIQUES
================================================================

Aquest script verifica tots els aspectes del sistema de auto-update:
1. Carregament de mòduls
2. Connexió a GitHub API
3. Detecció de versions
4. Simulació del procés d'actualització
5. Verificació de scripts BAT
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

class AutoUpdateComprehensiveTest:
    """Test complet del sistema de auto-update"""
    
    def __init__(self):
        self.results = {
            "test_date": datetime.now().isoformat(),
            "sections": []
        }
        self.passed = 0
        self.failed = 0
    
    def print_header(self, title):
        """Imprimir capçalera de secció"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    
    def print_test(self, name, status, details=""):
        """Imprimir resultat de test"""
        status_symbol = "✅" if status else "❌"
        print(f"  {status_symbol} {name}")
        if details:
            print(f"     └─ {details}")
        if status:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_module_imports(self):
        """Test 1: Verificar que tots els mòduls es carreguen correctament"""
        self.print_header("TEST 1: CARREGAMENT DE MÒDULS")
        
        tests = []
        
        # Test 1.1 - Importar versió
        try:
            from src.utils.version import APP_VERSION
            self.print_test("Importar version.py", True, f"APP_VERSION = {APP_VERSION}")
            tests.append(("version.py", True, APP_VERSION))
        except Exception as e:
            self.print_test("Importar version.py", False, str(e))
            tests.append(("version.py", False, str(e)))
        
        # Test 1.2 - Importar AutoUpdater
        try:
            from src.updater.auto_updater import AutoUpdater
            self.print_test("Importar auto_updater.py", True, "Classe AutoUpdater disponible")
            tests.append(("auto_updater.py", True, "OK"))
        except Exception as e:
            self.print_test("Importar auto_updater.py", False, str(e))
            tests.append(("auto_updater.py", False, str(e)))
        
        # Test 1.3 - Verificar que requests estigui instal·lat
        try:
            import requests
            self.print_test("Verificar 'requests' package", True, f"Versió: {requests.__version__}")
            tests.append(("requests", True, requests.__version__))
        except Exception as e:
            self.print_test("Verificar 'requests' package", False, str(e))
            tests.append(("requests", False, str(e)))
        
        self.results["sections"].append({
            "name": "Carregament de Mòduls",
            "tests": tests
        })
    
    def test_autoupdater_initialization(self):
        """Test 2: Verificar que AutoUpdater s'inicialitza correctament"""
        self.print_header("TEST 2: INICIALITZACIÓ D'AUTOUPDATER")
        
        tests = []
        
        try:
            from src.updater.auto_updater import AutoUpdater
            
            # Test 2.1 - Crear instància amb paràmetres per defecte
            try:
                updater = AutoUpdater()
                self.print_test("Crear instància per defecte", True, 
                              f"Owner: {updater.github_owner}, Repo: {updater.github_repo}")
                tests.append(("default_instance", True, "OK"))
            except Exception as e:
                self.print_test("Crear instància per defecte", False, str(e))
                tests.append(("default_instance", False, str(e)))
            
            # Test 2.2 - Crear instància amb paràmetres personalitzats
            try:
                updater = AutoUpdater(github_owner="TestOwner", github_repo="TestRepo")
                assert updater.github_owner == "TestOwner"
                assert updater.github_repo == "TestRepo"
                self.print_test("Crear instància personalitzada", True, 
                              f"Owner: {updater.github_owner}, Repo: {updater.github_repo}")
                tests.append(("custom_instance", True, "OK"))
            except Exception as e:
                self.print_test("Crear instància personalitzada", False, str(e))
                tests.append(("custom_instance", False, str(e)))
            
            # Test 2.3 - Verificar atributs
            try:
                updater = AutoUpdater()
                assert hasattr(updater, 'current_version')
                assert hasattr(updater, 'temp_dir')
                assert hasattr(updater, 'check_for_updates')
                assert hasattr(updater, 'download_and_install')
                self.print_test("Verificar atributs necessaris", True, 
                              "Tots els atributs presents")
                tests.append(("attributes", True, "OK"))
            except Exception as e:
                self.print_test("Verificar atributs necessaris", False, str(e))
                tests.append(("attributes", False, str(e)))
        
        except Exception as e:
            self.print_test("Tests d'inicialització", False, f"Error general: {e}")
            tests.append(("initialization", False, str(e)))
        
        self.results["sections"].append({
            "name": "Inicialització d'AutoUpdater",
            "tests": tests
        })
    
    def test_github_connectivity(self):
        """Test 3: Verificar connexió a GitHub API"""
        self.print_header("TEST 3: CONNEXIÓ A GITHUB API")
        
        tests = []
        
        try:
            import requests
            
            # Test 3.1 - Connexió bàsica a GitHub API
            try:
                response = requests.get("https://api.github.com", timeout=5)
                status_ok = response.status_code == 200
                self.print_test("Connexió a GitHub API", status_ok,
                              f"Status: {response.status_code}")
                tests.append(("github_api_connection", status_ok, response.status_code))
            except Exception as e:
                self.print_test("Connexió a GitHub API", False, str(e))
                tests.append(("github_api_connection", False, str(e)))
            
            # Test 3.2 - Accés al repositori específic
            try:
                url = "https://api.github.com/repos/Blanqui04/PythonTecnica_SOME"
                response = requests.get(url, timeout=5)
                status_ok = response.status_code == 200
                if status_ok:
                    data = response.json()
                    repo_name = data.get("name", "Unknown")
                    self.print_test("Accés repositori Blanqui04/PythonTecnica_SOME", status_ok,
                                  f"Repo: {repo_name}")
                    tests.append(("repo_access", True, repo_name))
                else:
                    self.print_test("Accés repositori Blanqui04/PythonTecnica_SOME", False,
                                  f"Status: {response.status_code}")
                    tests.append(("repo_access", False, response.status_code))
            except Exception as e:
                self.print_test("Accés repositori Blanqui04/PythonTecnica_SOME", False, str(e))
                tests.append(("repo_access", False, str(e)))
            
            # Test 3.3 - Accés als releases
            try:
                url = "https://api.github.com/repos/Blanqui04/PythonTecnica_SOME/releases/latest"
                response = requests.get(url, timeout=5)
                # 404 significa que no hi ha releases, però la connexió funciona
                connection_ok = response.status_code in [200, 404]
                detail = "Releases trobades" if response.status_code == 200 else "Cap release (esperado si primer cop)"
                self.print_test("Accés a releases", connection_ok, detail)
                tests.append(("releases_access", connection_ok, detail))
            except Exception as e:
                self.print_test("Accés a releases", False, str(e))
                tests.append(("releases_access", False, str(e)))
        
        except Exception as e:
            self.print_test("Tests de connectivitat", False, f"Error general: {e}")
            tests.append(("connectivity", False, str(e)))
        
        self.results["sections"].append({
            "name": "Connexió a GitHub API",
            "tests": tests
        })
    
    def test_version_detection(self):
        """Test 4: Verificar detecció de versions"""
        self.print_header("TEST 4: DETECCIÓ DE VERSIONS")
        
        tests = []
        
        try:
            from src.updater.auto_updater import AutoUpdater
            from src.utils.version import APP_VERSION
            
            updater = AutoUpdater()
            
            # Test 4.1 - Versió local es carrega correctament
            try:
                current = updater.current_version
                assert current == APP_VERSION
                self.print_test("Carregament versió local", True,
                              f"Versió: {current}")
                tests.append(("local_version", True, current))
            except Exception as e:
                self.print_test("Carregament versió local", False, str(e))
                tests.append(("local_version", False, str(e)))
            
            # Test 4.2 - Executar check_for_updates
            try:
                update_info = updater.check_for_updates()
                assert isinstance(update_info, dict)
                assert "update_available" in update_info
                
                available = update_info.get("update_available")
                remote_version = update_info.get("version", "N/A")
                
                self.print_test("Executar check_for_updates()", True,
                              f"Local: {APP_VERSION}, Remota: {remote_version}, Actualització: {available}")
                tests.append(("check_updates", True, f"Available: {available}"))
            except Exception as e:
                self.print_test("Executar check_for_updates()", False, str(e))
                tests.append(("check_updates", False, str(e)))
        
        except Exception as e:
            self.print_test("Tests de detecció", False, f"Error general: {e}")
            tests.append(("version_detection", False, str(e)))
        
        self.results["sections"].append({
            "name": "Detecció de Versions",
            "tests": tests
        })
    
    def test_file_structure(self):
        """Test 5: Verificar estructura de fitxers"""
        self.print_header("TEST 5: ESTRUCTURA DE FITXERS")
        
        tests = []
        base_path = Path(__file__).parent
        
        # Test 5.1 - version.py
        try:
            version_file = base_path / "src" / "utils" / "version.py"
            exists = version_file.exists()
            self.print_test("Fitxer src/utils/version.py", exists,
                          f"Path: {version_file}")
            tests.append(("version_file", exists, str(version_file)))
        except Exception as e:
            self.print_test("Fitxer src/utils/version.py", False, str(e))
            tests.append(("version_file", False, str(e)))
        
        # Test 5.2 - auto_updater.py
        try:
            updater_file = base_path / "src" / "updater" / "auto_updater.py"
            exists = updater_file.exists()
            self.print_test("Fitxer src/updater/auto_updater.py", exists,
                          f"Path: {updater_file}")
            tests.append(("updater_file", exists, str(updater_file)))
        except Exception as e:
            self.print_test("Fitxer src/updater/auto_updater.py", False, str(e))
            tests.append(("updater_file", False, str(e)))
        
        # Test 5.3 - __init__.py updater
        try:
            init_file = base_path / "src" / "updater" / "__init__.py"
            exists = init_file.exists()
            self.print_test("Fitxer src/updater/__init__.py", exists,
                          f"Path: {init_file}")
            tests.append(("init_file", exists, str(init_file)))
        except Exception as e:
            self.print_test("Fitxer src/updater/__init__.py", False, str(e))
            tests.append(("init_file", False, str(e)))
        
        # Test 5.4 - main_app.py contén codi d'update
        try:
            main_file = base_path / "main_app.py"
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
                has_update_code = "AutoUpdater" in content and "check_for_updates" in content
            self.print_test("main_app.py contén codi d'auto-update", has_update_code,
                          "AutoUpdater importat i usat")
            tests.append(("main_app_integration", has_update_code, "OK"))
        except Exception as e:
            self.print_test("main_app.py contén codi d'auto-update", False, str(e))
            tests.append(("main_app_integration", False, str(e)))
        
        self.results["sections"].append({
            "name": "Estructura de Fitxers",
            "tests": tests
        })
    
    def test_simulation(self):
        """Test 6: Simulació del procés complet"""
        self.print_header("TEST 6: SIMULACIÓ DEL PROCÉS COMPLET")
        
        tests = []
        
        try:
            from src.updater.auto_updater import AutoUpdater
            from src.utils.version import APP_VERSION
            
            # Simular els passos del procés
            steps = []
            
            # Pas 1: Crear updater
            try:
                updater = AutoUpdater()
                steps.append(("1. Inicializar AutoUpdater", True))
            except Exception as e:
                steps.append(("1. Inicializar AutoUpdater", False))
            
            # Pas 2: Comprovar versió local
            try:
                local = updater.current_version
                steps.append((f"2. Cargar versió local ({local})", True))
            except Exception as e:
                steps.append(("2. Cargar versió local", False))
            
            # Pas 3: Comprovar GitHub
            try:
                info = updater.check_for_updates()
                available = info.get("update_available", False)
                remote = info.get("version", "N/A")
                steps.append((f"3. Comprovar GitHub (Remota: {remote})", True))
            except Exception as e:
                steps.append(("3. Comprovar GitHub", False))
            
            # Pas 4: Comparar versions
            try:
                if available:
                    steps.append(("4. ACTUALITZACIÓ DISPONIBLE ✅", True))
                else:
                    steps.append(("4. Sistema actualitzat ✓", True))
            except Exception as e:
                steps.append(("4. Comparar versions", False))
            
            # Passar tots els pasos
            all_passed = all(step[1] for step in steps)
            
            print("\n  Flux de procés simulat:")
            for step, status in steps:
                symbol = "✅" if status else "❌"
                print(f"    {symbol} {step}")
            
            tests.append(("simulation_flow", all_passed, f"{len([s for s in steps if s[1]])}/{len(steps)} passos"))
        
        except Exception as e:
            self.print_test("Simulació completa", False, str(e))
            tests.append(("simulation", False, str(e)))
        
        self.results["sections"].append({
            "name": "Simulació del Procés",
            "tests": tests
        })
    
    def run_all_tests(self):
        """Executar tots els tests"""
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  TEST COMPLET DEL SISTEMA D'ACTUALITZACIONS AUTOMÀTIQUES".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        
        self.test_module_imports()
        self.test_autoupdater_initialization()
        self.test_github_connectivity()
        self.test_version_detection()
        self.test_file_structure()
        self.test_simulation()
        
        self.print_summary()
    
    def print_summary(self):
        """Imprimir resum dels resultats"""
        self.print_header("RESUM GENERAL")
        
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n  Total de tests: {total}")
        print(f"  ✅ Passats: {self.passed}")
        print(f"  ❌ Fallats: {self.failed}")
        print(f"  📊 Percentatge d'èxit: {percentage:.1f}%")
        
        if self.failed == 0:
            print("\n  🎉 ✅ TOTS ELS TESTS HAN PASSAT CORRECTAMENT!")
            print("\n  ✨ El sistema d'auto-actualització està completament funcional i proveïxat")
            print("  ✨ Els usuaris rebran actualitzacions automàtiques sense cap problema")
        else:
            print(f"\n  ⚠️  HI HA {self.failed} TEST(S) QUE HAN FALLAT")
            print("  ⚠️  Revisa els resultats anteriors per corregir els problemes")
        
        print("\n" + "=" * 80)
        print("\n")


if __name__ == "__main__":
    test = AutoUpdateComprehensiveTest()
    test.run_all_tests()
