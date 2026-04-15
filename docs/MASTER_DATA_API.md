# Endpoints da API de Dados Mestres

## Visão Geral
API REST somente leitura para acessar dados mestres: Localidades (países, estados, cidades), Categorias de Benefícios e Funções.

**IMPORTANTE**: Esta API é SOMENTE LEITURA (endpoints GET apenas). Os dados mestres são gerenciados através de seeding de banco de dados e scripts administrativos, NÃO via API REST.

Todos os endpoints estão disponíveis em: `/api/v1/master-data/`

Todos os endpoints requerem token de autenticação Azure AD no header: `Authorization: Bearer {token}`

---

## API de Localidades

### Obter Todas as Localidades
```
GET /api/v1/master-data/locations
Parâmetros de Consulta (opcional):
  - country: Filtrar por nome do país (string)
  - region: Filtrar por região (string) - LATAM, NA, EMEA, APAC
Resposta: [{ location_id, country_name, state_name, city_name, region, is_active }, ...]
```

### Obter Todos os Países
```
GET /api/v1/master-data/countries
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas países ativos (bool, padrão=false)
Resposta: [{ country_id, country_name, is_active }, ...]
```

**Países Disponíveis**: Brasil, Argentina, Chile, México, USA, Suécia, Itália, Polônia, Hungria, França, Espanha, Reino Unido, China, Tailândia, Índia, Austrália

### Obter Todas as Regiões
```
GET /api/v1/master-data/regions
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas regiões ativas (bool, padrão=false)
Resposta: [{ region_id, region_name, is_active }, ...]
```

**Regiões Disponíveis**:
- LATAM (América do Sul) - Ativa
- NA (América do Norte) - Pré-preenchida
- EMEA (Europa/Oriente Médio/África) - Pré-preenchida
- APAC (Ásia Pacífico) - Pré-preenchida

### Obter Estados por País
```
GET /api/v1/master-data/states-by-country/{country_name}
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas estados ativos (bool, padrão=false)
Resposta: [{ state_id, state_name, country_name, is_active }, ...]
```

Exemplo:
```bash
curl "http://localhost:8000/api/v1/master-data/states-by-country/Brazil" \
  -H "Authorization: Bearer {token}"
```

### Obter Cidades por País
```
GET /api/v1/master-data/cities-by-country/{country_name}
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas cidades ativas (bool, padrão=false)
Resposta: [{ city_id, city_name, state_name, country_name, region, is_active }, ...]
```

Exemplo:
```bash
curl "http://localhost:8000/api/v1/master-data/cities-by-country/Brazil" \
  -H "Authorization: Bearer {token}"
```

### Obter Cidades por Região
```
GET /api/v1/master-data/cities-by-region/{region}
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas cidades ativas (bool, padrão=false)
Resposta: [{ city_id, city_name, state_name, country_name, region, is_active }, ...]
```

Exemplo:
```bash
curl "http://localhost:8000/api/v1/master-data/cities-by-region/LATAM" \
  -H "Authorization: Bearer {token}"
```

### Obter Hierarquia Completa de Localidades
```
GET /api/v1/master-data/hierarchy
Resposta: 
{
  "regions": [
    {
      "region_name": "LATAM",
      "countries": [
        {
          "country_name": "Brazil",
          "states": [
            {
              "state_name": "São Paulo",
              "cities": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

**Dados de Localidade Disponíveis**:
- Países: 16 total (Brasil, Argentina, Chile, México, USA, Suécia, Itália, Polônia, Hungria, França, Espanha, Reino Unido, China, Tailândia, Índia, Austrália)
- Estados: Todos os estados/províncias principais para cada país
- Cidades: 46 cidades em todas as regiões
  - LATAM (Ativa): Cidades brasileiras + cidades da Argentina, Chile, México
  - NA, EMEA, APAC: Pré-preenchidas mas disponíveis

---

## API de Categorias (Categorias de Benefícios)

### Obter Todas as Categorias
```
GET /api/v1/master-data/categories
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas categorias ativas (bool, padrão=false)
Resposta: [{ category_id, category_name, description, is_active }, ...]
```

### Obter Detalhes da Categoria
```
GET /api/v1/master-data/categories/{category_id}
Resposta: { category_id, category_name, description, is_active }
```

**Categorias Pré-preenchidas** (13 total):
1. Admissão
2. Folha de Pagamento
3. Férias e Ausências
4. Jornada e Ponto
5. Saúde e Bem-Estar
6. Desenvolvimento e Carreira
7. Movimentações Internas
8. Políticas e Normas
9. Diversidade e Inclusão
10. Segurança da Informação
11. Relações Trabalhistas
12. Desligamento
13. RH Geral

---

## API de Funções (Níveis de Trabalho)

### Obter Todas as Funções
```
GET /api/v1/master-data/roles
Parâmetros de Consulta (opcional):
  - active_only: Filtrar apenas funções ativas (bool, padrão=false)
Resposta: [{ role_id, role_name, is_active }, ...]
```

### Obter Detalhes da Função
```
GET /api/v1/master-data/roles/{role_id}
Resposta: { role_id, role_name, is_active }
```

**Funções Pré-preenchidas** (15 total):
1. Analista
2. Aprendiz
3. Assistente
4. Coordenador
5. Diretor
6. Especialista
7. Estagiário
8. Gerente
9. Gerente Sênior
10. Head
11. Operacional
12. Presidente
13. Supervisor
14. Técnico
15. Vice-Presidente

---

## Notas Importantes

### API SOMENTE LEITURA
- Todos os endpoints usam apenas o método GET
- **SEM operações POST, PUT, PATCH ou DELETE disponíveis**
- As modificações de dados mestres são gerenciadas através de:
  - Migrações de banco de dados (veja `db/schema_seed.sql`)
  - Ferramentas administrativas CLI (se disponíveis)
  - Atualizações diretas do banco de dados por administradores do sistema

### Características dos Dados
- Todos os registros têm flag `is_active` para exclusão lógica
- Timestamps usam `GETDATE()` do lado do servidor (SQL Server)
- Relacionamentos por chave estrangeira:
  - Cidades → Estados → Países → Regiões
- Todos os endpoints suportam parâmetro opcional `active_only=true` para filtro

### Região LATAM (Padrão Ativo)
- Região de implantação primária com dados ativos
- Outras regiões (NA, EMEA, APAC) são pré-preenchidas para expansão futura
- Podem ser ativadas através de ferramentas administrativas

### Considerações de Performance
- Endpoint de hierarquia retorna árvore completa (pode ser grande)
- Use endpoints de filtro específicos para melhor performance:
  - Em vez de `/hierarchy`, use `/cities-by-country/{country}`
  - Use `active_only=true` para reduzir tamanho do resultado
- O frontend deve cachear resultados para minimizar chamadas à API

---

## Testes

Todos os endpoints de dados mestres são testados em testes unitários:
```bash
python3 -m pytest tests/unit/test_master_data.py -v
```

Cobertura de teste de exemplo:
```bash
GET /api/v1/master-data/locations
GET /api/v1/master-data/categories
GET /api/v1/master-data/roles
GET /api/v1/master-data/cities-by-country/Brazil
GET /api/v1/master-data/hierarchy
```

---

## Respostas de Erro

| Status | Erro | Causa |
|--------|------|-------|
| 401 | Não Autorizado | Token de autenticação ausente ou inválido |
| 404 | Recurso não encontrado | ID ou nome de país/região/categoria/função inválido |
| 500 | Erro interno do servidor | Problema de conexão com banco de dados |

Exemplo de resposta de erro:
```json
{
  "detail": "Country 'PaísInválido' not found"
}
```

---

## Exemplos de Integração

### Uso no Frontend (JavaScript/TypeScript)
```javascript
// Obter todos os países
const countries = await fetch('/api/v1/master-data/countries', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Obter cidades por país
const cities = await fetch('/api/v1/master-data/cities-by-country/Brazil', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Obter todas as funções
const roles = await fetch('/api/v1/master-data/roles', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Obter hierarquia completa (para seletores de localização)
const hierarchy = await fetch('/api/v1/master-data/hierarchy', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### Uso no Backend (Python)
```python
from app.services.location_service import LocationService
from app.services.category_service import CategoryService
from app.services.job_title_role_service import JobTitleRoleService

# Obter todos os países
countries = LocationService.get_all_countries()

# Obter cidades por país
cities = LocationService.get_cities_by_country("Brazil")

# Obter hierarquia completa
hierarchy = LocationService.get_hierarchy()

# Obter todas as categorias
categories = CategoryService.get_all_categories()

# Obter todas as funções
roles = JobTitleRoleService.get_all_roles()
```
