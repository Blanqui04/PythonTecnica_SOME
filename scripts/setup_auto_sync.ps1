# ============================================================
# Script per configurar tasca automatica al Windows Task Scheduler
# ============================================================

$taskName = "SincronitzacioBD_PythonTecnica"
$scriptPath = "C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\scripts\sync_databases_auto.bat"
$workingDir = "C:\Github\PythonTecnica_SOME\PythonTecnica_SOME"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   CONFIGURACIO TASCA AUTOMATICA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el script existeix
if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] No s'ha trobat l'script $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Script trobat: $scriptPath" -ForegroundColor Green
Write-Host ""

# Eliminar tasca anterior si existeix
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Tasca existent trobada. Eliminant..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "[OK] Tasca anterior eliminada" -ForegroundColor Green
}

Write-Host ""
Write-Host "[INFO] Creant nova tasca programada..." -ForegroundColor Cyan
Write-Host "   Nom: $taskName" -ForegroundColor Gray
Write-Host "   Hora: Cada dia a les 24:00 (mitjanit)" -ForegroundColor Gray
Write-Host "   Script: $scriptPath" -ForegroundColor Gray
Write-Host ""

# Crear l'accio
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Crear el trigger (cada dia a les 24:00)
$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"

# Configuracio de la tasca
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Crear principal amb l'usuari actual
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# Registrar la tasca
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Sincronitzacio automatica de bases de dades PythonTecnica" `
        -ErrorAction Stop
    
    Write-Host "[OK] Tasca creada correctament!" -ForegroundColor Green
    Write-Host ""
    
    # Mostrar informacio de la tasca
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   INFORMACIO DE LA TASCA" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $taskName
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    
    Write-Host ""
    Write-Host "Nom: $($task.TaskName)" -ForegroundColor White
    Write-Host "Programacio: Cada dia a les 24:00" -ForegroundColor White
    Write-Host "Usuari: $($task.Principal.UserId)" -ForegroundColor White
    Write-Host "Directori: $workingDir" -ForegroundColor White
    Write-Host "Estat: $($task.State)" -ForegroundColor White
    Write-Host "Darrera execucio: $($taskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "Propera execucio: $($taskInfo.NextRunTime)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   OPCIONS" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Per executar la tasca manualment:" -ForegroundColor Yellow
    Write-Host "   Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Per veure l'historial d'execucions:" -ForegroundColor Yellow
    Write-Host "   Get-ScheduledTaskInfo -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Per desactivar la tasca:" -ForegroundColor Yellow
    Write-Host "   Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Per eliminar la tasca:" -ForegroundColor Yellow
    Write-Host "   Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    
    # Preguntar si vol executar ara
    $response = Read-Host "Vols executar la sincronitzacio ara per provar? (S/N)"
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host ""
        Write-Host "[INFO] Executant sincronitzacio de prova..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $taskName
        
        Write-Host "[OK] Tasca iniciada! Consulta els logs per veure el resultat." -ForegroundColor Green
        Write-Host "   Log: C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\logs\sync_databases.log" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "[ERROR] Error al crear la tasca: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Configuracio completada!" -ForegroundColor Green
Write-Host ""
