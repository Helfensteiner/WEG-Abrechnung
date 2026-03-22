# git-commit.ps1
# Hilfsskript fuer WEG-Abrechnung: bereinigt Git-Lock-Dateien und erstellt Commit
# Aufruf: Rechtsklick -> "Mit PowerShell ausfuehren"  ODER  .\git-commit.ps1

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== WEG-Abrechnung Git-Commit ===" -ForegroundColor Cyan

# 1. Lock-Dateien entfernen
$locks = @(".git\index.lock", ".git\HEAD.lock", ".git\MERGE_HEAD.lock", ".git\COMMIT_EDITMSG.lock")
foreach ($lock in $locks) {
    if (Test-Path $lock) {
        Remove-Item $lock -Force
        Write-Host "  Entfernt: $lock" -ForegroundColor Yellow
    }
}

# 2. Status anzeigen
Write-Host ""
Write-Host "Geaenderte Dateien:" -ForegroundColor Cyan
git status --short
Write-Host ""

# 3. Commit-Nachricht abfragen
$msg = Read-Host "Commit-Nachricht (leer = abbrechen)"
if ([string]::IsNullOrWhiteSpace($msg)) {
    Write-Host "Abgebrochen." -ForegroundColor Red
    exit 0
}

# 4. Alles stagen und committen
git add hausverwaltung.py VERSION CHANGELOG.md
git -c user.email="jens.bilgery@gmail.com" -c user.name="Jens Bilgery" commit -m "$msg"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Commit erfolgreich!" -ForegroundColor Green

    # 5. Tag abfragen (optional)
    $tag = Read-Host "Git-Tag setzen? (z.B. v0.7.2 - leer = ueberspringen)"
    if (-not [string]::IsNullOrWhiteSpace($tag)) {
        git tag $tag
        Write-Host "Tag '$tag' gesetzt." -ForegroundColor Green
    }

    # 6. Push abfragen
    $push = Read-Host "Jetzt pushen? (j/n)"
    if ($push -eq "j" -or $push -eq "J") {
        git push
        if (-not [string]::IsNullOrWhiteSpace($tag)) {
            git push origin $tag
        }
        Write-Host "Push abgeschlossen." -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Commit fehlgeschlagen. Bitte Fehlermeldung pruefen." -ForegroundColor Red
}

Write-Host ""
Write-Host "Fertig. Fenster kann geschlossen werden." -ForegroundColor Cyan
Read-Host "Druecke Enter zum Beenden"
