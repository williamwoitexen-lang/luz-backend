# Testes Unitários e de Integração

Estrutura organizada de testes:

## 📁 Estrutura

```
tests/
├── unit/                 # Testes unitários (sem dependências externas)
├── integration/          # Testes de integração (com endpoints)
├── fixtures/             # Dados compartilhados
├── conftest.py          # Configuração pytest global
└── __init__.py
```

## 🧪 Como Rodar

### Todos os testes
```bash
pytest tests/
```

### Apenas unitários
```bash
pytest tests/unit/
```

### Apenas integração
```bash
pytest tests/integration/
```

### Um arquivo específico
```bash
pytest tests/unit/test_text_cleaning.py
```

### Com output detalhado
```bash
pytest tests/ -v
```

### Com coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📝 Categorias

### Unit Tests (`tests/unit/`)
- `test_text_cleaning.py` - Limpeza de PDF
- `test_vault_rsa_unit.py` - Criptografia RSA
- `test_auth_local.py` - Autenticação local
- `test_sqlserver_connection.py` - Conexão SQL Server

### Integration Tests (`tests/integration/`)
- `test_chat_api.py` - Endpoints de chat
- `test_auth_endpoints.py` - Endpoints autenticação
- `test_ingest_text_cleaning.py` - Endpoints ingest com limpeza
- `test_master_data_endpoints.py` - Endpoints master data
- `test_prod_endpoints.py` - Testes em produção

### Fixtures (`tests/fixtures/`)
- `conftest.py` - Setup global (client, database, mocks)
- Mock data e constants compartilhados

## ✅ Boas Práticas

1. **Unit tests** devem ser rápidos e isolados
   - Não usam banco de dados real
   - Não chamam APIs externas
   - Usam mocks para dependências

2. **Integration tests** podem ser lentos
   - Testam fluxos completos
   - Podem chamar endpoints
   - Validam integração de componentes

3. **Nomes claros**
   - `test_<função_ou_feature>.py`
   - `def test_<comportamento_esperado>()`

## 🔄 CI/CD

O pytest.ini aponta para `tests/` automaticamente:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

## 📊 Coverage

Veja coverage em `htmlcov/index.html` após rodar:
```bash
pytest tests/ --cov=app --cov-report=html
```
