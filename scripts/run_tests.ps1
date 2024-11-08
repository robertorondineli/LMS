# Limpa cache e arquivos temporários
Write-Host "Limpando cache e arquivos temporários..." -ForegroundColor Yellow
Remove-Item -Path ".\**\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue

# Ativa o ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Instala dependências de teste
Write-Host "Instalando dependências de teste..." -ForegroundColor Yellow
pip install pytest pytest-django pytest-cov pytest-env factory-boy

# Executa os testes
Write-Host "Executando testes..." -ForegroundColor Green
pytest

# Gera relatório de cobertura
Write-Host "Gerando relatório de cobertura..." -ForegroundColor Yellow
coverage html

# Abre o relatório no navegador
Write-Host "Abrindo relatório de cobertura..." -ForegroundColor Green
Start-Process "htmlcov\index.html" 