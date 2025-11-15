# scripts/test_smoke_routing.py
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_route_details(stops: list[dict], expected_status: int = 200, log_response: bool = False):
    url = "http://127.0.0.1:8111/api/tour/route-details"
    payload = {
        "stops": stops,
        "overview": "full",
        "geometries": "polyline6",
        "profile": "driving"
    }
    
    logger.info(f"Teste POST {url} mit {len(stops)} Stopps...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            logger.info(f"Antwort Status: {response.status_code}")
            
            if log_response:
                logger.info(f"Antwort Body: {response.json()}")
                
            assert response.status_code == expected_status, f"Erwarteter Status {expected_status}, bekam {response.status_code}"
            data = response.json()
            
            if expected_status == 200:
                assert "geometry_polyline6" in data, "Antwort enthält keine 'geometry_polyline6'"
                assert "total_distance_m" in data, "Antwort enthält keine 'total_distance_m'"
                assert "total_duration_s" in data, "Antwort enthält keine 'total_duration_s'"
                assert "source" in data, "Antwort enthält keine 'source'"
                logger.info("Routendetails-Endpoint erfolgreich getestet.")
            else:
                logger.info(f"Fehler-Szenario erfolgreich getestet: {data.get('detail', data.get('error'))}")
                
            return response
            
        except httpx.ConnectError as e:
            logger.error(f"Verbindungsfehler zum Server: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout beim Warten auf Serverantwort: {e}")
            raise
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Fehler-Response: {e.response.json()}")
            raise

async def main():
    # Normale Route
    await test_route_details(
        stops=[
            {"lat": 51.0493, "lon": 13.7381},
            {"lat": 51.0639, "lon": 13.7522},
            {"lat": 51.0772, "lon": 13.7303}
        ],
        log_response=True
    )

    # Fehlerfall: Weniger als 2 Stopps
    await test_route_details(
        stops=[
            {"lat": 51.0493, "lon": 13.7381}
        ],
        expected_status=400,
        log_response=True
    )
    
    # Fehlerfall: Ungültige Koordinaten
    await test_route_details(
        stops=[
            {"lat": 51.0493, "lon": 13.7381},
            {"lat": 999.0, "lon": 999.0} # Ungültige Koordinate
        ],
        expected_status=500, # Abhängig von der Validierung im Backend
        log_response=True
    )

if __name__ == "__main__":
    asyncio.run(main())
