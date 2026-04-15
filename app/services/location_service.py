"""
Location Service for managing locations (countries, cities, regions).
Now using dim_electrolux_locations table for simplified structure.
"""

import logging
from typing import List, Dict, Optional
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


class LocationService:
    """Service for managing locations using dim_electrolux_locations."""

    # ============================================================
    # LOCATION OPERATIONS
    # ============================================================

    @staticmethod
    async def create_location(country_name: str, state_name: str, city_name: str, 
                             region: str, continent: str, operation_type: str) -> Dict:
        """Create a new location."""
        try:
            sql = get_sqlserver_connection()
            query = """
            INSERT INTO dim_electrolux_locations 
            (country_name, state_name, city_name, region, continent, operation_type, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """
            sql.execute(query, [country_name, state_name, city_name, region, continent, operation_type])
            logger.info(f"Location created: {city_name}, {country_name}")
            return {
                "country_name": country_name,
                "state_name": state_name,
                "city_name": city_name,
                "region": region,
                "continent": continent,
                "operation_type": operation_type,
                "is_active": True
            }
        except Exception as e:
            logger.error(f"Error creating location: {e}")
            raise

    @staticmethod
    async def get_locations(
        country_names: Optional[List[str]] = None,
        city_names: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        active_only: bool = False,
        country_name: Optional[str] = None,
        city_name: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[Dict]:
        """Get locations with optional filters (returns all location records - no deduplication needed, each location is unique).
        
        Filters:
        - country_names: Filter by one or more countries
        - city_names: Filter by one or more cities
        - regions: Filter by one or more regions
        """
        try:
            sql = get_sqlserver_connection()
            query = "SELECT location_id, country_name, state_name, city_name, location_name, address FROM dim_electrolux_locations WHERE 1=1"
            
            # Backward-compatible aliases used by tests/callers.
            if country_name:
                country_names = (country_names or []) + [country_name]
            if city_name:
                city_names = (city_names or []) + [city_name]
            if region:
                regions = (regions or []) + [region]
            
            params = []

            # Handle country_names filter (supports list or single value)
            if country_names:
                if isinstance(country_names, str):
                    country_names = [country_names]
                if country_names:  # Only add if not empty
                    placeholders = ",".join(["?" for _ in country_names])
                    query += f" AND country_name IN ({placeholders})"
                    params.extend(country_names)
            
            # Handle city_names filter (supports list or single value)
            if city_names:
                if isinstance(city_names, str):
                    city_names = [city_names]
                if city_names:  # Only add if not empty
                    placeholders = ",".join(["?" for _ in city_names])
                    query += f" AND city_name IN ({placeholders})"
                    params.extend(city_names)
            
            # Handle regions filter (supports list or single value)
            if regions:
                if isinstance(regions, str):
                    regions = [regions]
                if regions:  # Only add if not empty
                    placeholders = ",".join(["?" for _ in regions])
                    query += f" AND region IN ({placeholders})"
                    params.extend(regions)
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY country_name, city_name, address"
            
            results = sql.execute(query, params) if params else sql.execute(query)
            return [{
                "location_id": r["location_id"],
                "country_name": r["country_name"],
                "state_name": r.get("state_name"),
                "city_name": r["city_name"],
                "location_name": r.get("location_name"),
                "address": r.get("address") or ""
            } for r in results]
        except Exception as e:
            logger.error(f"Error fetching locations: {e}")
            raise

    @staticmethod
    async def get_cities(
        country_names: Optional[List[str]] = None,
        active_only: bool = False
    ) -> List[Dict]:
        """Get distinct cities (optionally filtered by country_names).
        
        Can be used for:
        - City dropdown showing unique cities
        - City dropdown filtered by selected country(ies)
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT DISTINCT city_name, state_name, country_name, MIN(location_id) as location_id
            FROM dim_electrolux_locations
            WHERE 1=1
            """
            params = []
            
            # Handle country_names filter (supports list or single value)
            if country_names:
                if isinstance(country_names, str):
                    country_names = [country_names]
                if country_names:  # Only add if not empty
                    placeholders = ",".join(["?" for _ in country_names])
                    query += f" AND country_name IN ({placeholders})"
                    params.extend(country_names)
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " GROUP BY city_name, state_name, country_name ORDER BY country_name, city_name"
            
            results = sql.execute(query, params) if params else sql.execute(query)
            return [{
                "location_id": r["location_id"],
                "city_name": r["city_name"],
                "state_name": r.get("state_name"),
                "country_name": r["country_name"]
            } for r in results]
        except Exception as e:
            logger.error(f"Error fetching cities: {e}")
            raise

    @staticmethod
    async def get_location_id_by_city_and_address(country_name: str, city_name: str, address: str) -> Optional[int]:
        """
        Get location_id by country, city and address.
        Used to identify the exact location for LLM context.
        Returns location_id if found, None otherwise.
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT TOP 1 location_id 
            FROM dim_electrolux_locations 
            WHERE country_name = ? AND city_name = ? AND address = ? AND is_active = 1
            """
            results = sql.execute(query, [country_name, city_name, address])
            
            if results:
                return results[0]["location_id"]
            
            logger.warning(f"Location not found for: {country_name}, {city_name}, {address}")
            return None
        except Exception as e:
            logger.error(f"Error fetching location_id: {e}")
            return None

    @staticmethod
    async def get_countries(active_only: bool = False) -> List[Dict]:
        """Get distinct countries."""
        try:
            sql = get_sqlserver_connection()
            query = "SELECT DISTINCT country_name FROM dim_electrolux_locations WHERE 1=1"
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY country_name"
            
            results = sql.execute(query)
            return [{"country_name": r["country_name"]} for r in results]
        except Exception as e:
            logger.error(f"Error fetching countries: {e}")
            raise

    @staticmethod
    async def get_states_by_country(country_name: str, active_only: bool = False) -> List[Dict]:
        """Get distinct states for a country."""
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT DISTINCT state_name FROM dim_electrolux_locations 
            WHERE country_name = ? AND 1=1
            """
            params = [country_name]
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY state_name"
            
            results = sql.execute(query, params)
            return [{"state_name": r["state_name"]} for r in results]
        except Exception as e:
            logger.error(f"Error fetching states: {e}")
            raise

    @staticmethod
    async def get_regions(active_only: bool = False) -> List[Dict]:
        """Get distinct regions."""
        try:
            sql = get_sqlserver_connection()
            query = "SELECT DISTINCT region, continent FROM dim_electrolux_locations WHERE 1=1"
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY region"
            
            results = sql.execute(query)
            return [{"region": r.get("region"), "continent": r.get("continent")} for r in results]
        except Exception as e:
            logger.error(f"Error fetching regions: {e}")
            raise

    @staticmethod
    async def update_location(location_id: int, city_name: str, operation_type: str) -> Dict:
        """Update a location."""
        try:
            sql = get_sqlserver_connection()
            query = """
            UPDATE dim_electrolux_locations 
            SET city_name = ?, operation_type = ?, updated_at = GETUTCDATE()
            WHERE location_id = ?
            """
            sql.execute(query, [city_name, operation_type, location_id])
            logger.info(f"Location updated: {location_id}")
            return {"location_id": location_id, "city_name": city_name, "operation_type": operation_type}
        except Exception as e:
            logger.error(f"Error updating location: {e}")
            raise

    @staticmethod
    async def enable_location(location_id: int) -> Dict:
        """Enable a location."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 1, updated_at = GETUTCDATE() WHERE location_id = ?"
            sql.execute(query, [location_id])
            logger.info(f"Location enabled: {location_id}")
            return {"location_id": location_id, "is_active": True}
        except Exception as e:
            logger.error(f"Error enabling location: {e}")
            raise

    @staticmethod
    async def disable_location(location_id: int) -> Dict:
        """Disable a location."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 0, updated_at = GETUTCDATE() WHERE location_id = ?"
            sql.execute(query, [location_id])
            logger.info(f"Location disabled: {location_id}")
            return {"location_id": location_id, "is_active": False}
        except Exception as e:
            logger.error(f"Error disabling location: {e}")
            raise

    @staticmethod
    async def enable_country(country_name: str) -> Dict:
        """Enable all locations in a country."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 1, updated_at = GETUTCDATE() WHERE country_name = ?"
            sql.execute(query, [country_name])
            logger.info(f"Country enabled: {country_name}")
            return {"country_name": country_name, "is_active": True}
        except Exception as e:
            logger.error(f"Error enabling country: {e}")
            raise

    @staticmethod
    async def disable_country(country_name: str) -> Dict:
        """Disable all locations in a country."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 0, updated_at = GETUTCDATE() WHERE country_name = ?"
            sql.execute(query, [country_name])
            logger.info(f"Country disabled: {country_name}")
            return {"country_name": country_name, "is_active": False}
        except Exception as e:
            logger.error(f"Error disabling country: {e}")
            raise

    @staticmethod
    async def enable_region(region: str) -> Dict:
        """Enable all locations in a region."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 1, updated_at = GETUTCDATE() WHERE region = ?"
            sql.execute(query, [region])
            logger.info(f"Region enabled: {region}")
            return {"region": region, "is_active": True}
        except Exception as e:
            logger.error(f"Error enabling region: {e}")
            raise

    @staticmethod
    async def disable_region(region: str) -> Dict:
        """Disable all locations in a region."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_electrolux_locations SET is_active = 0, updated_at = GETUTCDATE() WHERE region = ?"
            sql.execute(query, [region])
            logger.info(f"Region disabled: {region}")
            return {"region": region, "is_active": False}
        except Exception as e:
            logger.error(f"Error disabling region: {e}")
            raise

    @staticmethod
    async def delete_location(location_id: int) -> Dict:
        """Delete a location."""
        try:
            sql = get_sqlserver_connection()
            query = "DELETE FROM dim_electrolux_locations WHERE location_id = ?"
            sql.execute(query, [location_id])
            logger.info(f"Location deleted: {location_id}")
            return {"location_id": location_id, "deleted": True}
        except Exception as e:
            logger.error(f"Error deleting location: {e}")
            raise

    # ============================================================
    # HIERARCHICAL ENDPOINTS (for cascading selects on frontend)
    # ============================================================

    @staticmethod
    async def get_hierarchy(active_only: bool = False) -> Dict:
        """
        Get complete location hierarchy (regions -> countries -> states -> cities).
        Used for cascading selects on frontend.
        """
        try:
            sql = get_sqlserver_connection()
            
            # Get all regions
            region_query = "SELECT DISTINCT region, continent FROM dim_electrolux_locations WHERE 1=1"
            if active_only:
                region_query += " AND is_active = 1"
            region_query += " ORDER BY region"
            
            regions = sql.execute(region_query)
            regions_list = []
            
            for region_row in regions:
                region = region_row["region"]
                
                # Get countries in this region
                country_query = "SELECT DISTINCT country_name FROM dim_electrolux_locations WHERE region = ? AND 1=1"
                country_params = [region]
                if active_only:
                    country_query += " AND is_active = 1"
                country_query += " ORDER BY country_name"
                
                countries = sql.execute(country_query, country_params)
                countries_list = []
                
                for country_row in countries:
                    country_name = country_row["country_name"]
                    
                    # Get states in this country
                    state_query = "SELECT DISTINCT state_name FROM dim_electrolux_locations WHERE country_name = ? AND region = ? AND 1=1"
                    state_params = [country_name, region]
                    if active_only:
                        state_query += " AND is_active = 1"
                    state_query += " ORDER BY state_name"
                    
                    states = sql.execute(state_query, state_params)
                    states_list = []
                    
                    for state_row in states:
                        state_name = state_row["state_name"]
                        
                        # Get cities in this state
                        city_query = """
                        SELECT DISTINCT city_name, operation_type, is_active, MIN(location_id) as location_id
                        FROM dim_electrolux_locations 
                        WHERE country_name = ? AND state_name = ? AND region = ? AND 1=1
                        """
                        city_params = [country_name, state_name, region]
                        if active_only:
                            city_query += " AND is_active = 1"
                        city_query += " GROUP BY city_name, operation_type, is_active ORDER BY city_name"
                        
                        cities = sql.execute(city_query, city_params)
                        cities_list = [{
                            "location_id": c["location_id"],
                            "city_name": c["city_name"],
                            "operation_type": c["operation_type"],
                            "is_active": c["is_active"]
                        } for c in cities]
                        
                        states_list.append({
                            "state_name": state_name,
                            "cities": cities_list
                        })
                    
                    countries_list.append({
                        "country_name": country_name,
                        "states": states_list
                    })
                
                regions_list.append({
                    "region": region,
                    "continent": region_row["continent"],
                    "countries": countries_list
                })
            
            return {"hierarchy": regions_list}
        except Exception as e:
            logger.error(f"Error fetching location hierarchy: {e}")
            raise
