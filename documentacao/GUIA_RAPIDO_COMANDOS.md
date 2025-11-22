# ⚡ GUIA RÁPIDO - COMANDOS ESSENCIAIS

**Sistema**: ProtecAI - Análise de Relés de Proteção  
**Atualizado**: 22/11/2025

---

## 🚀 INÍCIO RÁPIDO (3 COMANDOS)

```bash
# 1. Ativar ambiente
source /Volumes/Mac_XIII/virtualenvs/rele_prot/bin/activate

# 2. Processar novos arquivos
python src/python/main.py

# 3. Gerar todos os relatórios
python -c "from src.python.reporters.report_generator import ReportGenerator; g = ReportGenerator(output_base_path='outputs/relatorios'); [g.generate_report(f'REL0{i}') if i < 10 else g.generate_report(f'REL{i}') for i in range(1, 10)]"
```

---

## 🐳 DOCKER

### Gerenciar Container PostgreSQL
```bash
# Status
docker ps | grep protecai

# Iniciar
docker start protecai_postgres

# Parar
docker stop protecai_postgres

# Logs
docker logs protecai_postgres

# Executar SQL
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "SELECT COUNT(*) FROM protec_ai.relays;"
```

### Recriar Schema/Views
```bash
# Recriar schema completo
docker exec -i protecai_postgres psql -U protecai -d protecai_db < docker/postgres/init.sql

# Recriar apenas views
docker exec -i protecai_postgres psql -U protecai -d protecai_db < docker/postgres/create_views.sql
```

---

## 📊 RELATÓRIOS

### Gerar Relatórios Individuais
```bash
# REL06 (Completo de Relés)
python -c "from src.python.reporters.report_generator import ReportGenerator; g = ReportGenerator(output_base_path='outputs/relatorios'); g.generate_report('REL06')"

# REL08 (Análise de Tensão)
python -c "from src.python.reporters.report_generator import ReportGenerator; g = ReportGenerator(output_base_path='outputs/relatorios'); g.generate_report('REL08')"

# Qualquer relatório
python -c "from src.python.reporters.report_generator import ReportGenerator; g = ReportGenerator(output_base_path='outputs/relatorios'); g.generate_report('REL01')"
```

### Gerar Todos os Relatórios
```bash
python -c "
from src.python.reporters.report_generator import ReportGenerator
g = ReportGenerator(output_base_path='outputs/relatorios')
for rel_id in ['REL01', 'REL02', 'REL03', 'REL04', 'REL05', 
               'REL06', 'REL07', 'REL08', 'REL09']:
    print(f'\n🔄 Gerando {rel_id}...')
    g.generate_report(rel_id)
    print(f'✅ {rel_id} concluído')
"
```

### Limpar Relatórios Antigos
```bash
rm -rf outputs/relatorios/csv/*.csv
rm -rf outputs/relatorios/xlsx/*.xlsx
rm -rf outputs/relatorios/pdf/*.pdf
```

---

## 🔄 PIPELINE

### Executar Pipeline Completa
```bash
cd /Users/accol/Library/Mobile\ Documents/com~apple~CloudDocs/UNIVERSIDADES/UFF/PROJETOS/PETROBRAS/PETRO_ProtecAI/rele_prot
python src/python/main.py
```

### Limpar Outputs
```bash
# Limpar CSVs
rm -f outputs/csv/*.csv
rm -f outputs/norm_csv/*.csv

# Limpar Excel
rm -f outputs/excel/*.xlsx

# Limpar tudo
rm -rf outputs/csv/*.csv outputs/excel/*.xlsx outputs/norm_csv/*.csv
```

### Resetar Registry (Reprocessar Tudo)
```bash
# Backup
cp inputs/registry/processed_files.json inputs/registry/backup_$(date +%Y%m%d_%H%M%S).json

# Limpar
echo '{"processed_files": {}, "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%S.%6N)'"}' > inputs/registry/processed_files.json
```

---

## 🗄️ DATABASE

### Consultas Rápidas
```bash
# Total de relés
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "SELECT COUNT(*) FROM protec_ai.relays;"

# Relés por fabricante
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "
SELECT m.name, COUNT(*) 
FROM protec_ai.relays r
JOIN protec_ai.relay_models rm ON r.relay_model_id = rm.id
JOIN protec_ai.manufacturers m ON rm.manufacturer_id = m.id
GROUP BY m.name;
"

# Últimos 5 relés processados
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "
SELECT bay_identifier, relay_type, voltage_class_kv, processed_at 
FROM protec_ai.relays 
ORDER BY processed_at DESC 
LIMIT 5;
"
```

### Backup e Restore
```bash
# Backup
docker exec protecai_postgres pg_dump -U protecai protecai_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i protecai_postgres psql -U protecai -d protecai_db < backup_20251122.sql
```

### Limpar Banco (CUIDADO!)
```bash
# Deletar todos os dados (mantém schema)
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "
TRUNCATE TABLE protec_ai.parameters CASCADE;
TRUNCATE TABLE protec_ai.protection_functions CASCADE;
TRUNCATE TABLE protec_ai.voltage_transformers CASCADE;
TRUNCATE TABLE protec_ai.current_transformers CASCADE;
TRUNCATE TABLE protec_ai.relays CASCADE;
TRUNCATE TABLE protec_ai.relay_models CASCADE;
TRUNCATE TABLE protec_ai.manufacturers CASCADE;
TRUNCATE TABLE protec_ai.ansi_functions CASCADE;
"
```

---

## 📝 LOGS

### Ver Logs
```bash
# Último log
tail -100 logs/pipeline_$(date +%Y%m%d)*.log

# Monitorar em tempo real
tail -f logs/pipeline_*.log

# Buscar erros
grep -i error logs/pipeline_*.log

# Buscar warnings
grep -i warning logs/pipeline_*.log

# Ver logs de hoje
ls -lht logs/pipeline_$(date +%Y%m%d)*.log
```

### Limpar Logs Antigos
```bash
# Deletar logs com mais de 30 dias
find logs/ -name "pipeline_*.log" -mtime +30 -delete

# Deletar todos os logs (CUIDADO!)
rm -f logs/pipeline_*.log
```

---

## 🔍 TESTES E VALIDAÇÃO

### Validar Arquivos de Entrada
```bash
# Contar PDFs
ls -1 inputs/pdf/*.pdf | wc -l

# Contar .S40
ls -1 inputs/txt/*.S40 | wc -l

# Ver novos arquivos não processados
python -c "
from src.python.utils.file_manager import FileManager
from pathlib import Path
fm = FileManager(registry_path='inputs/registry/processed_files.json')
pdfs = list(Path('inputs/pdf').glob('*.pdf'))
s40s = list(Path('inputs/txt').glob('*.S40'))
all_files = pdfs + s40s
new_files = [f for f in all_files if not fm.is_file_processed(str(f))]
print(f'Novos arquivos: {len(new_files)}')
for f in new_files:
    print(f'  - {f.name}')
"
```

### Validar Outputs
```bash
# Contar CSVs gerados
ls -1 outputs/csv/*.csv | wc -l

# Contar relatórios gerados
ls -1 outputs/relatorios/xlsx/*.xlsx | wc -l

# Ver último relatório gerado
ls -lt outputs/relatorios/xlsx/ | head -5
```

---

## 🛠️ GIT

### Status e Commits
```bash
# Status
git status

# Add arquivos importantes
git add docker/postgres/create_views.sql
git add src/python/reporters/excel_reporter.py
git add src/python/reporters/report_generator.py
git add src/python/main.py
git add src/python/normalizers/relay_normalizer.py

# Commit
git commit -m "feat: Descrição da mudança"

# Push
git push origin main
```

### Ver Histórico
```bash
# Últimos 5 commits
git log --oneline -5

# Arquivos modificados no último commit
git show --name-only

# Diff de um arquivo
git diff src/python/reporters/excel_reporter.py
```

---

## 🧹 LIMPEZA GERAL

### Script de Limpeza Completa
```bash
#!/bin/bash
# clean_all.sh

echo "🧹 Limpando outputs..."
rm -rf outputs/csv/*.csv
rm -rf outputs/excel/*.xlsx
rm -rf outputs/norm_csv/*.csv
rm -rf outputs/relatorios/csv/*.csv
rm -rf outputs/relatorios/xlsx/*.xlsx
rm -rf outputs/relatorios/pdf/*.pdf

echo "🧹 Limpando logs antigos..."
find logs/ -name "pipeline_*.log" -mtime +7 -delete

echo "🧹 Backup do registry..."
cp inputs/registry/processed_files.json inputs/registry/backup_$(date +%Y%m%d_%H%M%S).json

echo "✅ Limpeza concluída!"
```

---

## 📦 INSTALAÇÃO (Nova Máquina)

### Setup Completo
```bash
# 1. Clonar repositório
git clone <repo_url> rele_prot
cd rele_prot

# 2. Criar virtual environment
python3 -m venv /Volumes/Mac_XIII/virtualenvs/rele_prot
source /Volumes/Mac_XIII/virtualenvs/rele_prot/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar PostgreSQL
docker-compose up -d

# 5. Aguardar PostgreSQL
sleep 10

# 6. Testar conexão
docker exec -i protecai_postgres psql -U protecai -d protecai_db -c "SELECT 1;"

# 7. Executar pipeline
python src/python/main.py
```

---

## 🔥 ATALHOS ÚTEIS

### Aliases (Adicionar ao ~/.zshrc)
```bash
# ProtecAI Aliases
alias protec='cd /Users/accol/Library/Mobile\ Documents/com~apple~CloudDocs/UNIVERSIDADES/UFF/PROJETOS/PETROBRAS/PETRO_ProtecAI/rele_prot'
alias protec-env='source /Volumes/Mac_XIII/virtualenvs/rele_prot/bin/activate'
alias protec-run='protec && protec-env && python src/python/main.py'
alias protec-reports='protec && protec-env && python -c "from src.python.reporters.report_generator import ReportGenerator; g = ReportGenerator(output_base_path=\"outputs/relatorios\"); [g.generate_report(f\"REL0{i}\") for i in range(1, 10)]"'
alias protec-logs='tail -f /Users/accol/Library/Mobile\ Documents/com~apple~CloudDocs/UNIVERSIDADES/UFF/PROJETOS/PETROBRAS/PETRO_ProtecAI/rele_prot/logs/pipeline_*.log'
alias protec-db='docker exec -it protecai_postgres psql -U protecai -d protecai_db'
```

### Usar Aliases
```bash
# Ir para projeto e ativar env
protec && protec-env

# Executar pipeline
protec-run

# Gerar todos os relatórios
protec-reports

# Ver logs em tempo real
protec-logs

# Abrir psql
protec-db
```

---

## 📞 TROUBLESHOOTING

### Container não inicia
```bash
# Ver erro
docker logs protecai_postgres

# Forçar recriação
docker-compose down
docker-compose up -d
```

### Erro "view does not exist"
```bash
# Recriar views
docker exec -i protecai_postgres psql -U protecai -d protecai_db < docker/postgres/create_views.sql
```

### Erro "permission denied"
```bash
# Dar permissão aos scripts
chmod +x scripts/*.sh

# Verificar owner dos arquivos
ls -la outputs/
```

### Python não encontra módulos
```bash
# Verificar virtual env ativo
which python

# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

---

## ✅ CHECKLIST DIÁRIO

```markdown
- [ ] Docker PostgreSQL rodando
- [ ] Virtual environment ativado
- [ ] Novos arquivos em inputs/pdf ou inputs/txt
- [ ] Pipeline executada sem erros
- [ ] Relatórios gerados
- [ ] Commit das mudanças
- [ ] Logs verificados
```

---

**⚡ COMANDOS SEMPRE À MÃO!**

*Use Ctrl+F para buscar rapidamente*
