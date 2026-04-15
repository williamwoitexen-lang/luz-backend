# Exemplos de Uso dos Serviços

Este documento contém exemplos práticos de como utilizar cada serviço da aplicação.

---

## 1. LocationService

### Obter todas as localizações

```python
from app.services.location_service import LocationService

# Obter todas as localizações
locations = await LocationService.get_locations()

# Obter apenas localizações ativas
active_locations = await LocationService.get_locations(active_only=True)

# Filtrar por país
locations = await LocationService.get_locations(country_name="Brazil")

# Filtrar por região
locations = await LocationService.get_locations(region="LATAM")
```

### Obter localização por ID

```python
# Obter uma localização específica
location = await LocationService.get_location_by_id(location_id=1)
```

### Criar nova localização

```python
# Criar uma nova localização
new_location = await LocationService.create_location(
    country_name="Brazil",
    state_name="São Paulo",
    city_name="São Paulo",
    region="LATAM",
    continent="South America",
    operation_type="Manufacturing"
)
```

### Atualizar localização

```python
# Atualizar uma localização
updated = await LocationService.update_location(
    location_id=1,
    country_name="Brazil",
    state_name="Rio de Janeiro",
    city_name="Rio de Janeiro",
    region="LATAM",
    continent="South America",
    operation_type="Distribution"
)
```

### Desativar localização

```python
# Desativar uma localização
await LocationService.delete_location(location_id=1)
```

---

## 2. RoleService

### Obter todos os papéis/cargos

```python
from app.services.role_service import RoleService

# Obter todos os papéis
roles = await RoleService.get_roles()

# Obter apenas papéis ativos
active_roles = await RoleService.get_roles(active_only=True)
```

### Obter papel por ID

```python
# Obter um papel específico
role = await RoleService.get_role_by_id(role_id=1)
```

### Criar novo papel

```python
# Criar um novo papel/cargo
new_role = await RoleService.create_role(role_name="Senior Manager")
```

### Atualizar papel

```python
# Atualizar um papel existente
updated = await RoleService.update_role(
    role_id=1,
    role_name="Senior Director"
)
```

### Desativar papel

```python
# Desativar um papel
await RoleService.delete_role(role_id=1)
```

---

## 3. CategoryService

### Obter todas as categorias

```python
from app.services.category_service import CategoryService

# Obter todas as categorias
categories = await CategoryService.get_categories()

# Obter apenas categorias ativas
active_categories = await CategoryService.get_categories(active_only=True)
```

### Obter categoria por ID

```python
# Obter uma categoria específica
category = await CategoryService.get_category_by_id(category_id=1)
```

### Criar nova categoria

```python
# Criar uma nova categoria de benefícios
new_category = await CategoryService.create_category(
    category_name="Health Insurance",
    description="Health and medical insurance coverage"
)
```

### Atualizar categoria

```python
# Atualizar uma categoria existente
updated = await CategoryService.update_category(
    category_id=1,
    category_name="Premium Health Insurance",
    description="Comprehensive health and medical insurance"
)
```

### Desativar categoria

```python
# Desativar uma categoria
await CategoryService.delete_category(category_id=1)
```

---

## 4. DocumentService

### Ingerir documento

```python
from app.services.document_service import DocumentService
from fastapi import UploadFile

# Ingerir um documento (upload)
result = await DocumentService.ingest_document_file(
    file=upload_file,  # FastAPI UploadFile
    document_type="policy",
    location_id=1,
    user_email="user@example.com"
)
# Retorna: {"document_id": "uuid", "version": 1, "status": "processing"}
```

### Recuperar documento

```python
# Buscar documento por ID
document = await DocumentService.get_document(document_id="uuid-here")

# Buscar documentos por tipo
documents = await DocumentService.get_documents_by_type(document_type="policy")

# Buscar documentos por localização
documents = await DocumentService.get_documents_by_location(location_id=1)
```

### Deletar versão de documento

```python
# Deletar uma versão específica de um documento
await DocumentService.delete_document_version(
    document_id="uuid-here",
    version=1
)
```

---

## 5. Usar nos Endpoints FastAPI

### Exemplo em um Router

```python
from fastapi import APIRouter, HTTPException
from app.services.location_service import LocationService

router = APIRouter()

@router.get("/locations")
async def list_locations(active_only: bool = False):
    try:
        locations = await LocationService.get_locations(active_only=active_only)
        return {"data": locations, "count": len(locations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/{location_id}")
async def get_location(location_id: int):
    try:
        location = await LocationService.get_location_by_id(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. Padrões Comuns

### Pattern: Async/Await

Todos os serviços usam `async`, então sempre use `await` ao chamar:

```python
# ✅ Correto
result = await LocationService.get_locations()

# ❌ Errado
result = LocationService.get_locations()  # retorna coroutine
```

### Pattern: Tratamento de Erros

```python
from fastapi import HTTPException

try:
    location = await LocationService.get_location_by_id(1)
except Exception as e:
    logger.error(f"Error fetching location: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

### Pattern: Filtros

Todos os serviços suportam `active_only=True`:

```python
# Obter apenas registros ativos
active_only = await LocationService.get_locations(active_only=True)
active_roles = await RoleService.get_roles(active_only=True)
active_categories = await CategoryService.get_categories(active_only=True)
```

---

## Estrutura do Banco de Dados

### Tabelas Utilizadas

| Serviço | Tabela |
|---------|--------|
| LocationService | `dim_electrolux_locations` |
| RoleService | `dim_roles` |
| CategoryService | `dim_categories` |
| DocumentService | `documents`, `document_versions` |

### Conexão SQL Server

Todos os serviços usam:

```python
from app.core.sqlserver import get_sqlserver_connection

sql = get_sqlserver_connection()
sql.execute(query, params)
```

A conexão é gerenciada automaticamente com:
- Lazy loading (conecta sob demanda)
- Thread-safe (lock para múltiplas requisições)
- Timeout de 5 segundos (previne bloqueio)
- Managed Identity (autenticação Azure)

