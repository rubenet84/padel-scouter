<#
.SYNOPSIS
    Backups la base de datos PostgreSQL del contenedor Docker.
.EXAMPLE
    .\scripts\backup-db.ps1                     # backup con timestamp
    .\scripts\backup-db.ps1 -Restore latest     # restaura el más reciente
    .\scripts\backup-db.ps1 -Restore backups\backup_20260702_143000.sql
#>

param(
    [string]$Restore
)

$project_root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backup_dir   = Join-Path $project_root "backups"
$container    = "padel_postgres"
$db_user      = "padel"
$db_name      = "padel_scouter"

# Crear carpeta de backups si no existe
New-Item -ItemType Directory -Force -Path $backup_dir | Out-Null

if ($Restore) {
    # --- MODO RESTORE ---
    if ($Restore -eq "latest") {
        $Restore = Get-ChildItem -Path $backup_dir -Filter "*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
        if (-not $Restore) { Write-Error "No hay backups en $backup_dir"; exit 1 }
    }
    Write-Host "Restaurando $Restore ..." -ForegroundColor Yellow
    docker exec -i $container psql -U $db_user -d $db_name < $Restore
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Restaurado correctamente" -ForegroundColor Green
    } else {
        Write-Error "Error restaurando el backup"
    }
    exit
}

# --- MODO BACKUP ---
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$filename  = "backup_$timestamp.sql"
$filepath  = Join-Path $backup_dir $filename

Write-Host "Haciendo backup de $db_name ..." -ForegroundColor Cyan
docker exec $container pg_dump -U $db_user -d $db_name > $filepath

if ($LASTEXITCODE -eq 0 -and (Test-Path $filepath)) {
    $size = "{0:N2} KB" -f ((Get-Item $filepath).Length / 1KB)
    Write-Host "Backup creado: $filename ($size)" -ForegroundColor Green
    # Limpiar backups viejos (>30 días)
    Get-ChildItem -Path $backup_dir -Filter "*.sql" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force
} else {
    Write-Error "Error creando el backup"
}
