"""
Monitor específic per al reprocessament complet dels DOS paths
Segueix el progrés de NetworkScanner + ProjectScanner
"""

import sys
import os
import time
import subprocess
from datetime import datetime

def monitor_complete_reprocessing():
    """Monitor del reprocessament complet"""
    print("📊 MONITOR REPROCESSAMENT COMPLET DOS PATHS")
    print("=" * 65)
    print(f"⏰ Inici monitorització: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📍 PROCESSANT:")
    print("   [1/2] NetworkScanner:  \\\\gompcnou\\KIOSK\\results")
    print("   [2/2] ProjectScanner:  \\\\gompc\\kiosk\\PROJECTES")
    print()
    
    start_time = datetime.now()
    
    try:
        # Monitorització contínua
        for cycle in range(120):  # Monitor durant 2 hores màxim
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"🔄 Cicle {cycle+1}/120 - {current_time.strftime('%H:%M:%S')}")
            print(f"   ⏱️  Temps transcorregut: {elapsed}")
            
            # Verificar processos Python
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True, shell=True)
                
                python_processes = []
                memory_usage = []
                
                for line in result.stdout.split('\n'):
                    if 'python.exe' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            memory_str = parts[4].replace(',', '').replace(' K', '')
                            try:
                                memory_kb = int(memory_str)
                                memory_mb = memory_kb / 1024
                                python_processes.append(parts[1])  # PID
                                memory_usage.append(memory_mb)
                            except:
                                pass
                
                total_memory_mb = sum(memory_usage)
                max_memory_mb = max(memory_usage) if memory_usage else 0
                
                print(f"   🐍 Processos Python: {len(python_processes)}")
                print(f"   💾 Memòria total: {total_memory_mb:,.0f} MB")
                print(f"   📈 Procés més gran: {max_memory_mb:,.0f} MB")
                
                # Indicadors d'estat
                if len(python_processes) >= 3:
                    print("   🔄 PROCESSOS ACTIUS - Reprocessant...")
                elif len(python_processes) == 0:
                    print("   ⭐ PROCESSOS FINALITZATS")
                    break
                else:
                    print("   ⏸️  PROCESSOS BAIXOS - Possiblement finalitzant...")
                
                # Alertes de memòria
                if total_memory_mb > 8000:  # Més de 8GB
                    print("   ⚠️  ALTA UTILITZACIÓ DE MEMÒRIA!")
                elif total_memory_mb > 5000:  # Més de 5GB
                    print("   📊 Utilitzant molta memòria (normal)")
                
            except Exception as e:
                print(f"   ⚠️  Error verificant processos: {e}")
            
            print("-" * 50)
            
            # Estimació de progrés
            if cycle > 0:
                estimated_total_minutes = 180  # 3 hores estimades
                progress_pct = (elapsed.total_seconds() / 60) / estimated_total_minutes * 100
                remaining_minutes = estimated_total_minutes - (elapsed.total_seconds() / 60)
                
                if progress_pct < 100:
                    print(f"   📊 Progrés estimat: {progress_pct:.1f}%")
                    print(f"   ⏳ Temps restant aprox: {remaining_minutes:.0f} minuts")
                    print("-" * 50)
            
            # Pausa entre cicles
            try:
                time.sleep(60)  # 1 minut entre verificacions
            except KeyboardInterrupt:
                print(f"\n⚠️  Monitorització interrompuda per l'usuari")
                break
                
        # Resum final
        final_time = datetime.now()
        total_duration = final_time - start_time
        
        print(f"\n🎯 FI DE MONITORITZACIÓ")
        print("=" * 40)
        print(f"⏰ Hora final: {final_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duració total monitorització: {total_duration}")
        
        # Verificació final de processos
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True, shell=True)
            
            final_processes = len([line for line in result.stdout.split('\n') if 'python.exe' in line])
            
            if final_processes == 0:
                print("✅ REPROCESSAMENT COMPLETAT - No hi ha processos Python")
            else:
                print(f"🔄 {final_processes} processos Python encara actius")
                
        except:
            pass
        
    except Exception as e:
        print(f"❌ Error en monitorització: {e}")
        import traceback
        traceback.print_exc()

def quick_status():
    """Estat ràpid del reprocessament"""
    print("🔍 ESTAT RÀPID REPROCESSAMENT COMPLET")
    print("=" * 45)
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Verificar processos
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        
        processes = [line for line in result.stdout.split('\n') if 'python.exe' in line]
        
        if len(processes) > 0:
            print(f"🐍 {len(processes)} processos Python actius")
            
            total_memory = 0
            for line in processes:
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        memory_kb = int(parts[4].replace(',', '').replace(' K', ''))
                        total_memory += memory_kb / 1024
                    except:
                        pass
            
            print(f"💾 Memòria total: {total_memory:,.0f} MB")
            
            if total_memory > 5000:
                print("🔄 REPROCESSAMENT ACTIU")
            else:
                print("⏸️  Activitat baixa")
        else:
            print("⭐ No hi ha processos Python - Possiblement finalitzat")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("📊 OPCIONS DE MONITORITZACIÓ:")
    print("1. Monitor complet (2 hores)")
    print("2. Estat ràpid")
    print()
    
    choice = input("Selecciona opció (1/2): ").strip()
    
    if choice == '1':
        print("\n🚀 INICIANT MONITOR COMPLET...")
        print("   (Prem Ctrl+C per aturar)")
        print()
        monitor_complete_reprocessing()
    elif choice == '2':
        quick_status()
    else:
        print("❌ Opció no vàlida")
