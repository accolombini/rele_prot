# Arquitetura do Front-end - Sistema ProtecAI

## 🎯 Objetivo

Criar interface web simples e funcional para:
1. Executar pipeline de dados (extração → normalização → banco)
2. Gerar relatórios sob demanda
3. Visualizar status do sistema
4. Upload e processamento de novos arquivos de relés

---

## 🏗️ Stack Tecnológica

### Backend
- **Flask 3.0+** - Framework web Python
- **Flask-CORS** - Suporte CORS para APIs
- **Flask-SocketIO** (opcional) - WebSockets para logs em tempo real

### Frontend
- **HTML5/CSS3/JavaScript** - Vanilla JS (sem frameworks pesados)
- **Bootstrap 5.3** - UI components e responsividade
- **Font Awesome 6** - Ícones
- **Chart.js** (opcional) - Gráficos no dashboard

### Comunicação
- **REST API** - Endpoints JSON para operações
- **Server-Sent Events (SSE)** - Logs em tempo real (alternativa a WebSockets)

---

## 📁 Estrutura de Arquivos

```
rele_prot/
├── src/
│   └── web/
│       ├── app.py                 # Aplicação Flask principal
│       ├── config.py              # Configurações
│       ├── static/
│       │   ├── css/
│       │   │   ├── style.css      # Estilos customizados
│       │   │   └── dashboard.css  # Estilos dashboard
│       │   ├── js/
│       │   │   ├── main.js        # Script principal
│       │   │   ├── pipeline.js    # Lógica pipeline
│       │   │   ├── reports.js     # Lógica relatórios
│       │   │   └── upload.js      # Lógica upload
│       │   └── img/
│       │       └── logo.png       # Logo ProtecAI
│       ├── templates/
│       │   ├── base.html          # Template base (header, nav, footer)
│       │   ├── index.html         # Dashboard principal
│       │   ├── pipeline.html      # Página pipeline
│       │   ├── reports.html       # Página relatórios
│       │   ├── upload.html        # Página upload
│       │   └── components/
│       │       ├── navbar.html    # Componente navbar
│       │       ├── alerts.html    # Componente alertas
│       │       └── card.html      # Componente cards
│       └── api/
│           ├── __init__.py
│           ├── pipeline_api.py    # Endpoints pipeline
│           ├── reports_api.py     # Endpoints relatórios
│           ├── upload_api.py      # Endpoints upload
│           └── status_api.py      # Endpoints status
```

---

## 🔌 API REST - Endpoints

### 1. Status do Sistema

#### `GET /api/status`
**Descrição:** Retorna estatísticas gerais do sistema

**Response:**
```json
{
  "relays": {
    "total": 50,
    "by_manufacturer": {
      "GE": 15,
      "Schneider": 20,
      "Siemens": 15
    }
  },
  "parameters": {
    "total": 18532,
    "average_per_relay": 370.64
  },
  "protections": {
    "total": 423,
    "identified_ansi": 89,
    "unknown_ansi": 334
  },
  "database": {
    "connected": true,
    "size_mb": 45.3
  },
  "last_pipeline_run": {
    "timestamp": "2025-11-20T17:12:59",
    "duration_seconds": 3.2,
    "status": "success",
    "files_processed": 8
  },
  "disk_usage": {
    "inputs_mb": 125.4,
    "outputs_mb": 67.8,
    "logs_mb": 12.3
  }
}
```

---

### 2. Pipeline de Dados

#### `POST /api/pipeline/run`
**Descrição:** Inicia execução da pipeline completa

**Request Body:**
```json
{
  "clean_outputs": false,     // Limpar outputs antes?
  "force_reprocess": false,   // Forçar reprocessamento de duplicados?
  "notify_completion": true   // Enviar notificação ao concluir?
}
```

**Response:**
```json
{
  "job_id": "pipeline_20251121_093045",
  "status": "running",
  "started_at": "2025-11-21T09:30:45",
  "estimated_duration_seconds": 15,
  "phases": [
    {
      "name": "extraction",
      "status": "pending",
      "progress": 0
    },
    {
      "name": "normalization",
      "status": "pending",
      "progress": 0
    },
    {
      "name": "database_load",
      "status": "pending",
      "progress": 0
    }
  ]
}
```

#### `GET /api/pipeline/status/<job_id>`
**Descrição:** Consulta status de execução da pipeline

**Response:**
```json
{
  "job_id": "pipeline_20251121_093045",
  "status": "running",            // pending, running, completed, failed
  "current_phase": "normalization",
  "progress": 55,                 // Porcentagem global
  "phases": [
    {
      "name": "extraction",
      "status": "completed",
      "progress": 100,
      "files_processed": 8,
      "duration_seconds": 2.1
    },
    {
      "name": "normalization",
      "status": "running",
      "progress": 65,
      "files_processed": 5,
      "duration_seconds": 1.8
    },
    {
      "name": "database_load",
      "status": "pending",
      "progress": 0
    }
  ],
  "logs_url": "/api/pipeline/logs/pipeline_20251121_093045"
}
```

#### `GET /api/pipeline/logs/<job_id>`
**Descrição:** Retorna logs da execução (streaming via SSE)

**Headers:**
```
Accept: text/event-stream
```

**Response (SSE stream):**
```
data: {"level": "INFO", "message": "Iniciando FASE 1 - EXTRAÇÃO", "timestamp": "2025-11-21T09:30:45"}

data: {"level": "INFO", "message": "Processando arquivo: P241.pdf", "timestamp": "2025-11-21T09:30:46"}

data: {"level": "SUCCESS", "message": "Arquivo P241.pdf: 127 parâmetros extraídos", "timestamp": "2025-11-21T09:30:47"}

data: {"level": "INFO", "message": "FASE 1 concluída: 8 arquivos, 3947 parâmetros", "timestamp": "2025-11-21T09:30:48"}
```

#### `GET /api/pipeline/history`
**Descrição:** Retorna histórico de execuções

**Query params:**
- `limit` (int, default=10): Número de execuções
- `offset` (int, default=0): Offset para paginação

**Response:**
```json
{
  "total": 47,
  "limit": 10,
  "offset": 0,
  "executions": [
    {
      "job_id": "pipeline_20251121_093045",
      "started_at": "2025-11-21T09:30:45",
      "completed_at": "2025-11-21T09:31:03",
      "duration_seconds": 18.2,
      "status": "completed",
      "files_processed": 8,
      "errors": 0
    },
    // ... mais 9 execuções
  ]
}
```

---

### 3. Relatórios

#### `POST /api/reports/generate`
**Descrição:** Gera um relatório

**Request Body:**
```json
{
  "report_type": "inventory",   // inventory, protections, transformers, parameters, audit
  "format": "pdf",               // csv, xlsx, pdf
  "filters": {
    "relay_ids": ["R001", "R002"],
    "manufacturers": ["GE", "Schneider"],
    "date_from": "2025-11-01",
    "date_to": "2025-11-21"
  },
  "options": {
    "include_charts": true,
    "language": "pt-BR"
  }
}
```

**Response:**
```json
{
  "job_id": "report_inventory_20251121_094512",
  "status": "generating",
  "estimated_duration_seconds": 5,
  "download_url": null  // Será preenchido quando concluído
}
```

#### `GET /api/reports/status/<job_id>`
**Descrição:** Consulta status de geração do relatório

**Response:**
```json
{
  "job_id": "report_inventory_20251121_094512",
  "status": "completed",  // generating, completed, failed
  "progress": 100,
  "file_info": {
    "filename": "inventario_reles_20251121_094517.pdf",
    "size_bytes": 234567,
    "download_url": "/api/reports/download/inventario_reles_20251121_094517.pdf"
  }
}
```

#### `GET /api/reports/list`
**Descrição:** Lista relatórios gerados

**Query params:**
- `limit` (int, default=20)
- `offset` (int, default=0)
- `format` (string): Filtrar por formato

**Response:**
```json
{
  "total": 156,
  "limit": 20,
  "offset": 0,
  "reports": [
    {
      "filename": "inventario_reles_20251121_094517.pdf",
      "report_type": "inventory",
      "format": "pdf",
      "size_bytes": 234567,
      "created_at": "2025-11-21T09:45:17",
      "download_url": "/api/reports/download/inventario_reles_20251121_094517.pdf"
    },
    // ... mais 19 relatórios
  ]
}
```

#### `GET /api/reports/download/<filename>`
**Descrição:** Download do arquivo de relatório

**Response:**
```
Content-Type: application/pdf (ou application/vnd.ms-excel, text/csv)
Content-Disposition: attachment; filename="inventario_reles_20251121_094517.pdf"
[binary data]
```

#### `DELETE /api/reports/<filename>`
**Descrição:** Exclui um relatório gerado

**Response:**
```json
{
  "success": true,
  "message": "Relatório excluído com sucesso"
}
```

---

### 4. Upload de Arquivos

#### `POST /api/upload`
**Descrição:** Upload de arquivos de relés

**Request:**
```
Content-Type: multipart/form-data
file: [binary data]
```

**Response:**
```json
{
  "success": true,
  "file": {
    "filename": "P999.pdf",
    "size_bytes": 456789,
    "format": "pdf",
    "uploaded_at": "2025-11-21T10:15:32",
    "status": "pending_processing",
    "estimated_parameters": null  // Será preenchido após processamento
  }
}
```

#### `GET /api/files/pending`
**Descrição:** Lista arquivos carregados mas não processados

**Response:**
```json
{
  "total": 5,
  "files": [
    {
      "filename": "P999.pdf",
      "size_bytes": 456789,
      "format": "pdf",
      "uploaded_at": "2025-11-21T10:15:32",
      "status": "pending_processing"
    },
    // ... mais 4 arquivos
  ]
}
```

#### `POST /api/files/process`
**Descrição:** Processa arquivos pendentes

**Request Body:**
```json
{
  "files": ["P999.pdf", "P1000.pdf"],  // ou null para processar todos
  "run_full_pipeline": true             // Executar pipeline completa após upload?
}
```

**Response:**
```json
{
  "job_id": "process_20251121_101832",
  "status": "running",
  "files_count": 2,
  "pipeline_job_id": "pipeline_20251121_101833"  // Se run_full_pipeline=true
}
```

#### `GET /api/files/list`
**Descrição:** Lista todos os arquivos no sistema

**Query params:**
- `processed` (bool): Filtrar processados/não processados
- `format` (string): Filtrar por formato (pdf, txt, s40)

**Response:**
```json
{
  "total": 50,
  "files": [
    {
      "filename": "P241.pdf",
      "size_bytes": 234567,
      "format": "pdf",
      "uploaded_at": "2025-11-20T15:30:00",
      "processed_at": "2025-11-20T16:45:23",
      "status": "processed",
      "parameters_extracted": 127,
      "relay_id": "R001"
    },
    // ... mais 49 arquivos
  ]
}
```

---

## 🎨 Interface do Usuário

### 1. Base Layout (base.html)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ProtecAI{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navbar -->
    {% include 'components/navbar.html' %}
    
    <!-- Main Content -->
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar (opcional) -->
            <nav class="col-md-2 d-md-block bg-light sidebar">
                <!-- Menu lateral -->
            </nav>
            
            <!-- Content Area -->
            <main class="col-md-10 ms-sm-auto px-md-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JS -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 2. Dashboard (index.html)

**Seções:**
- **Header com estatísticas**: Cards com total de relés, parâmetros, proteções
- **Status da última execução**: Badge de sucesso/falha, duração, timestamp
- **Gráficos**: Relés por fabricante (pizza), Parâmetros por relé (barras)
- **Ações rápidas**: Botões grandes para Pipeline, Relatórios, Upload
- **Atividade recente**: Tabela com últimas 5 execuções

### 3. Pipeline (pipeline.html)

**Seções:**
- **Controle de execução**: Botão "Iniciar Pipeline" com opções (limpar outputs, forçar reprocessamento)
- **Progresso em tempo real**: Barra de progresso global + 3 fases individuais
- **Logs ao vivo**: Console com logs em tempo real (scroll automático)
- **Histórico**: Tabela com últimas 10 execuções (paginação)

### 4. Relatórios (reports.html)

**Seções:**
- **Geração de relatórios**: Form com dropdowns (tipo, formato), filtros (datas, relés), botão "Gerar"
- **Status de geração**: Barra de progresso quando gerando
- **Relatórios disponíveis**: Grid de cards com preview, tamanho, data, botão download/excluir

### 5. Upload (upload.html)

**Seções:**
- **Área de upload**: Drag & drop zone, suporta múltiplos arquivos
- **Arquivos carregados**: Lista com nome, tamanho, status, botão "Processar"
- **Validação**: Alerta se formato inválido, tamanho muito grande
- **Opções**: Checkbox "Executar pipeline após upload"

---

## 🔒 Segurança (MVP - Básica)

### Versão Inicial (21/11)
- **Sem autenticação** (uso interno, rede local)
- **Validação de inputs** (tamanho arquivo, formato)
- **CORS restrito** (apenas localhost)
- **Rate limiting básico** (evitar sobrecarga)

### Versão Futura
- Autenticação JWT
- RBAC (Admin, Operator, Viewer)
- Logging de auditoria
- HTTPS obrigatório

---

## ⚡ Performance

### Otimizações
- **Cache**: Flask-Caching para status do sistema (TTL 30s)
- **Background jobs**: Celery para pipeline e relatórios (evitar timeout)
- **Streaming**: SSE para logs (evitar polling)
- **Compressão**: Gzip para responses >1KB

### Limites
- **Upload**: Max 50MB por arquivo
- **Relatórios**: Max 1000 relés por relatório
- **Histórico**: Max 100 execuções na UI (paginação)

---

## 📦 Dependências

### requirements_web.txt
```
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9

# Opcional (background jobs)
# celery==5.3.4
# redis==5.0.1
```

---

## 🚀 Execução

### Desenvolvimento
```bash
# Ativar ambiente
workon rele_prot

# Instalar dependências
pip install -r requirements_web.txt

# Configurar variáveis
export FLASK_APP=src/web/app.py
export FLASK_ENV=development

# Iniciar servidor
flask run --host=0.0.0.0 --port=5000
```

### Produção (Gunicorn)
```bash
# Instalar gunicorn
pip install gunicorn

# Iniciar com 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 src.web.app:app
```

---

## 🧪 Testes

### Testes de API
```python
# tests/test_api.py
import pytest
from src.web.app import app

def test_status_endpoint():
    client = app.test_client()
    response = client.get('/api/status')
    assert response.status_code == 200
    assert 'relays' in response.json

def test_pipeline_run():
    client = app.test_client()
    response = client.post('/api/pipeline/run', json={})
    assert response.status_code == 200
    assert 'job_id' in response.json
```

### Executar testes
```bash
pytest tests/test_api.py -v
```

---

## 📝 Próximos Passos (Pós 21/11)

1. **Autenticação e autorização**
2. **Background jobs com Celery**
3. **Notificações** (email, webhook)
4. **Dashboards avançados** (Chart.js, D3.js)
5. **API pública** (documentação OpenAPI/Swagger)
6. **Docker compose** (Flask + PostgreSQL + Redis)
7. **Deploy em nuvem** (AWS, Azure, GCP)

---

**Última atualização:** 20 de novembro de 2025, 17:45
