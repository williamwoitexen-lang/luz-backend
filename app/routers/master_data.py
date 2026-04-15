"""
Routers para gerenciar dados mestres (locais, categorias, papéis).
Endpoints simplificados para GET - dados já devem existir no Azure SQL Server.

## Exemplos de Uso

### Locations
```
GET /api/v1/master-data/locations
GET /api/v1/master-data/locations?country_name=Brazil&active_only=true
GET /api/v1/master-data/countries
GET /api/v1/master-data/regions
GET /api/v1/master-data/cities-by-country/Brazil
```

### Roles
```
GET /api/v1/master-data/roles
GET /api/v1/master-data/roles/1
GET /api/v1/master-data/roles?active_only=true
```

### Categories
```
GET /api/v1/master-data/categories
GET /api/v1/master-data/categories/1
GET /api/v1/master-data/categories?active_only=true
```
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.location_service import LocationService
from app.services.category_service import CategoryService
from app.services.role_service import RoleService

router = APIRouter(prefix="/api/v1/master-data", tags=["master-data"])

# ============================================================
# LOCATIONS (GET endpoints)
# ============================================================

@router.get("/locations", summary="List all locations", description="Get all locations with optional filters (simplified response)")
async def get_locations(
    country_names: Optional[List[str]] = Query(None, description="Filter by country names (e.g., 'Brazil' or 'Brazil,USA')"),
    city_names: Optional[List[str]] = Query(None, description="Filter by city names (e.g., 'Curitiba' or 'São Paulo,Curitiba')"),
    regions: Optional[List[str]] = Query(None, description="Filter by regions (e.g., 'LATAM' or 'LATAM,NA')"),
    active_only: bool = Query(False, description="Return only active locations (is_active=true)")
):
    """
    Get all locations with optional filters (returns only essential fields).
    
    **Query Parameters:**
    - `country_names`: Filter locations by country names (accepts single or multiple values)
    - `city_names`: Filter locations by city names (accepts single or multiple values)
    - `regions`: Filter locations by regions (accepts single or multiple values)
    - `active_only`: Return only active locations (default: false)
    
    **Response Example - Simplified response:**
    ```json
    [
      {
        "location_id": 1,
        "country_name": "Brazil",
        "city_name": "São Paulo",
        "address": "Avenida Paulista, 1000"
      },
      {
        "location_id": 2,
        "country_name": "Brazil",
        "city_name": "Curitiba",
        "address": "Rua das Flores, 500"
      }
    ]
    ```
    
    **Usage Examples:**
    1. Get ALL locations:
       ```
       GET /api/v1/master-data/locations
       ```
    
    2. Get only ACTIVE locations:
       ```
       GET /api/v1/master-data/locations?active_only=true
       ```
    
    3. Filter by SINGLE COUNTRY:
       ```
       GET /api/v1/master-data/locations?country_names=Brazil&active_only=true
       ```
    
    4. Filter by MULTIPLE COUNTRIES:
       ```
       GET /api/v1/master-data/locations?country_names=Brazil&country_names=USA&active_only=true
       ```
    
    5. Filter by CITY:
       ```
       GET /api/v1/master-data/locations?country_names=Brazil&city_names=Curitiba
       ```
    
    6. Filter by MULTIPLE CITIES:
       ```
       GET /api/v1/master-data/locations?city_names=Curitiba&city_names=São%20Paulo
       ```
    
    7. Filter by REGION:
       ```
       GET /api/v1/master-data/locations?regions=LATAM&active_only=true
       ```
    
    8. Filter by MULTIPLE REGIONS:
       ```
       GET /api/v1/master-data/locations?regions=LATAM&regions=NA&active_only=true
       ```
    """
    try:
        return await LocationService.get_locations(country_names=country_names, city_names=city_names, regions=regions, active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/countries", summary="List all countries", description="Get all unique countries")
async def get_countries(active_only: bool = Query(False, description="Return only countries with active locations")):
    """
    Get all unique countries from locations.
    
    **Response Example:**
    ```json
    [
      {
        "country_id": 1,
        "country_name": "Brazil",
        "location_count": 6,
        "is_active": true
      }
    ]
    ```
    """
    try:
        return await LocationService.get_countries(active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cities", summary="List all cities", description="Get all unique cities (optionally filtered by countries)")
async def get_cities(
    country_names: Optional[List[str]] = Query(None, description="Filter by country names (e.g., 'Brazil' or 'Brazil,USA')"),
    active_only: bool = Query(False, description="Return only cities with active locations")
):
    """
    Get all unique cities (optionally filtered by country names).
    
    **Query Parameters:**
    - `country_names`: Filter cities by country names (accepts single or multiple values)
    - `active_only`: Return only cities with active locations (default: false)
    
    **Response Example:**
    ```json
    [
      {
        "location_id": 1,
        "city_name": "São Paulo",
        "state_name": "São Paulo",
        "country_name": "Brazil"
      },
      {
        "location_id": 2,
        "city_name": "Curitiba",
        "state_name": "Paraná",
        "country_name": "Brazil"
      }
    ]
    ```
    
    **Usage Examples:**
    1. Get ALL cities:
       ```
       GET /api/v1/master-data/cities
       ```
    
    2. Get cities in SINGLE COUNTRY:
       ```
       GET /api/v1/master-data/cities?country_names=Brazil&active_only=true
       ```
    
    3. Get cities in MULTIPLE COUNTRIES:
       ```
       GET /api/v1/master-data/cities?country_names=Brazil&country_names=USA&active_only=true
       ```
    """
    try:
        return await LocationService.get_cities(country_names=country_names, active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/regions", summary="List all regions", description="Get all unique regions (LATAM, NA, EMEA, APAC, etc.)")
async def get_regions(active_only: bool = Query(False, description="Return only regions with active locations")):
    """
    Get all unique regions (LATAM, NA, EMEA, APAC, etc.).
    
    **Response Example:**
    ```json
    [
      {
        "region_id": 1,
        "region": "LATAM",
        "country_count": 4,
        "location_count": 11,
        "is_active": true
      }
    ]
    ```
    """
    try:
        return await LocationService.get_regions(active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/states-by-country/{country_name}", summary="List states by country", description="Get all states for a specific country")
async def get_states_by_country(country_name: str, active_only: bool = Query(False, description="Return only states with active locations")):
    """
    Get all states for a specific country.
    
    **Path Parameters:**
    - `country_name`: Name of the country (e.g., 'Brazil')
    
    **Response Example:**
    ```json
    [
      {
        "state_id": 1,
        "state_name": "São Paulo",
        "country_name": "Brazil",
        "city_count": 3,
        "is_active": true
      }
    ]
    ```
    
    **Usage Example:**
    - `/states-by-country/Brazil`
    - `/states-by-country/Mexico?active_only=true`
    """
    try:
        return await LocationService.get_states_by_country(country_name=country_name, active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hierarchy", summary="Get complete location hierarchy", description="Get the complete region → country → state → city hierarchy")
async def get_hierarchy(active_only: bool = Query(False, description="Return only active hierarchy levels")):
    """
    Get complete region → country → state → city hierarchy.
    
    **Response Example:**
    ```json
    {
      "LATAM": {
        "Brazil": {
          "São Paulo": ["São Paulo", "Campinas"],
          "Rio de Janeiro": ["Rio de Janeiro"]
        },
        "Mexico": {
          "Mexico City": ["Mexico City"]
        }
      }
    }
    ```
    
    **Use Cases:**
    - Building hierarchical dropdowns/selectors
    - Geographic data visualization
    - Location tree structures
    """
    try:
        return await LocationService.get_hierarchy(active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# ROLES (GET endpoints)
# ============================================================

@router.get("/roles", summary="List all job roles", description="Get all job roles/levels")
async def get_roles(
    active_only: bool = Query(False, description="Return only active roles"),
    language: str = Query("pt", regex="^(pt|en|es)$", description="Language for role names (pt, en, es). Default: pt")
):
    """
    Get all job roles/levels.
    
    **Response Example (11 rotos ativos):**
    ```json
    [
      {
        "role_id": 1,
        "role_name": "Chief Executive Officer",
        "is_active": true
      },
      {
        "role_id": 2,
        "role_name": "Vice President",
        "is_active": true
      },
      {
        "role_id": 3,
        "role_name": "Senior Manager",
        "is_active": true
      },
      {
        "role_id": 4,
        "role_name": "Manager",
        "is_active": true
      },
      {
        "role_id": 5,
        "role_name": "Supervisor",
        "is_active": true
      },
      {
        "role_id": 6,
        "role_name": "Specialist",
        "is_active": true
      },
      {
        "role_id": 7,
        "role_name": "Analyst",
        "is_active": true
      },
      {
        "role_id": 8,
        "role_name": "Coordinator",
        "is_active": true
      },
      {
        "role_id": 9,
        "role_name": "Associate",
        "is_active": true
      },
      {
        "role_id": 10,
        "role_name": "Intern",
        "is_active": true
      },
      {
        "role_id": 11,
        "role_name": "Contractor",
        "is_active": true
      }
    ]
    ```
    
    **Exemplos de Uso:**
    
    1. **Obter TODOS os papéis:**
       ```
       GET /api/v1/master-data/roles
       ```
    
    2. **Obter APENAS papéis ativos:**
       ```
       GET /api/v1/master-data/roles?active_only=true
       ```
    
    3. **Com curl:**
       ```bash
       curl "http://localhost:8000/api/v1/master-data/roles?active_only=true"
       ```
    
    4. **Com Python:**
       ```python
       import requests
       
       response = requests.get("http://localhost:8000/api/v1/master-data/roles")
       roles = response.json()
       
       # Filtrar apenas roles com "Manager" no nome
       managers = [r for r in roles if "Manager" in r["role_name"]]
       for role in managers:
           console.log(f"ID: {role['role_id']} - {role['role_name']}")
       ```
    
    5. **Com JavaScript:**
       ```javascript
       const response = await fetch("http://localhost:8000/api/v1/master-data/roles");
       const roles = await response.json();
       
       // Contar roles
       console.log(`Total de papéis: ${roles.length}`);
       
       // Criar dropdown
       const select = document.querySelector("select");
       roles.forEach(role => {
           const option = document.createElement("option");
           option.value = role.role_id;
           option.text = role.role_name;
           select.appendChild(option);
       });
       ```
    """
    try:
        return await RoleService.get_roles(active_only=active_only, language=language)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/roles/{role_id}", summary="Get role details", description="Get a specific role by ID")
async def get_role(role_id: int):
    """
    Get a specific role by ID.
    
    **Path Parameters:**
    - `role_id`: ID of the role (e.g., 1)
    
    **Response Example:**
    ```json
    {
      "role_id": 1,
      "role_name": "Senior Manager",
      "is_active": true,
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-01T10:00:00"
    }
    ```
    
    **Error Responses:**
    - 404: Role not found
    - 400: Invalid role ID
    """
    try:
        return await RoleService.get_role_by_id(role_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# CATEGORIES (GET endpoints)
# ============================================================

@router.get("/categories", summary="List all benefit categories", description="Get all benefit categories")
async def get_categories(
    active_only: bool = Query(False, description="Return only active categories"),
    language: str = Query("pt", regex="^(pt|en|es)$", description="Language for category names (pt, en, es). Default: pt")
):
    """
    Get all benefit categories.
    
    **Response Example (14 categorias ativas):**
    ```json
    [
      {
        "category_id": 1,
        "category_name": "Health Insurance",
        "description": "Medical and health coverage",
        "is_active": true
      },
      {
        "category_id": 2,
        "category_name": "Dental Plan",
        "description": "Dental coverage and orthodontics",
        "is_active": true
      },
      {
        "category_id": 3,
        "category_name": "Vision Plan",
        "description": "Eye care and glasses coverage",
        "is_active": true
      },
      {
        "category_id": 4,
        "category_name": "Retirement Plan",
        "description": "401k and pension benefits",
        "is_active": true
      },
      {
        "category_id": 5,
        "category_name": "Life Insurance",
        "description": "Life insurance coverage",
        "is_active": true
      },
      {
        "category_id": 6,
        "category_name": "Disability Insurance",
        "description": "Short and long-term disability",
        "is_active": true
      },
      {
        "category_id": 7,
        "category_name": "Flexible Spending Account",
        "description": "FSA for healthcare and dependent care",
        "is_active": true
      },
      {
        "category_id": 8,
        "category_name": "Stock Options",
        "description": "Employee stock purchase plan",
        "is_active": true
      },
      {
        "category_id": 9,
        "category_name": "Tuition Reimbursement",
        "description": "Education and professional development",
        "is_active": true
      },
      {
        "category_id": 10,
        "category_name": "Commuter Benefits",
        "description": "Public transit and parking benefits",
        "is_active": true
      },
      {
        "category_id": 11,
        "category_name": "Wellness Program",
        "description": "Fitness and health promotion",
        "is_active": true
      },
      {
        "category_id": 12,
        "category_name": "Paid Time Off",
        "description": "Vacation, sick leave, holidays",
        "is_active": true
      },
      {
        "category_id": 13,
        "category_name": "Family Leave",
        "description": "Maternity and paternity leave",
        "is_active": true
      },
      {
        "category_id": 14,
        "category_name": "Employee Assistance Program",
        "description": "Mental health and counseling services",
        "is_active": true
      }
    ]
    ```
    
    **Exemplos de Uso:**
    
    1. **Obter TODAS as categorias:**
       ```
       GET /api/v1/master-data/categories
       ```
    
    2. **Obter APENAS categorias ativas:**
       ```
       GET /api/v1/master-data/categories?active_only=true
       ```
    
    3. **Com curl:**
       ```bash
       curl "http://localhost:8000/api/v1/master-data/categories?active_only=true" | json_pp
       ```
    
    4. **Com Python:**
       ```python
       import requests
       
       response = requests.get("http://localhost:8000/api/v1/master-data/categories")
       categories = response.json()
       
       # Listar apenas categorias de seguro
       insurance = [c for c in categories if "Insurance" in c["category_name"]]
       for cat in insurance:
           console.log(f"- {cat['category_name']}: {cat['description']}")
       ```
    
    5. **Com JavaScript:**
       ```javascript
       const response = await fetch("http://localhost:8000/api/v1/master-data/categories");
       const categories = await response.json();
       
       // Criar lista de benefícios para o usuário
       const benefitsList = document.querySelector("#benefits");
       categories.forEach(cat => {
           const item = document.createElement("div");
           item.innerHTML = `
               <h3>${cat.category_name}</h3>
               <p>${cat.description}</p>
           `;
           benefitsList.appendChild(item);
       });
       ```
    """
    try:
        return await CategoryService.get_categories(active_only=active_only, language=language)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/categories/{category_id}", summary="Get category details", description="Get a specific category by ID")
async def get_category(category_id: int):
    """
    Get a specific category by ID.
    
    **Path Parameters:**
    - `category_id`: ID of the category (e.g., 1)
    
    **Response Example:**
    ```json
    {
      "category_id": 1,
      "category_name": "Health Insurance",
      "description": "Medical and health coverage",
      "is_active": true,
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-01T10:00:00"
    }
    ```
    
    **Error Responses:**
    - 404: Category not found
    - 400: Invalid category ID
    """
    try:
        return await CategoryService.get_category_by_id(category_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
