import httpx
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DC Used Tesla FSD Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TESLA_API_URL = "https://www.tesla.com/inventory/api/v1/inventory-results"

@app.get("/api/teslas")
async def get_used_fsd_teslas():
    query_params = {
        "query": json.dumps({
            "query": {
                "model": "m3",
                "condition": "used",
                "options": {},
                "arrangeby": "Price",
                "order": "asc",
                "market": "US",
                "language": "en",
                "super_region": "north america",
                "zip": "20001",
                "radius": 100
            },
            "offset": 0,
            "count": 50
        })
    }
    
    # Crucial Headers to prevent Tesla from blocking Render
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Authority": "www.tesla.com"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(TESLA_API_URL, params=query_params, headers=headers, timeout=15.0)
            
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Tesla API returned status {response.status_code}")
            
        data = response.json()
        results = data.get("results", [])
        filtered_cars = []
        
        for car in results:
            option_codes = car.get("OptionCodeList", [])
            autopilot_meta = car.get("AUTOPILOT", [])
            
            is_fsd = "ADFSD" in option_codes or any("FSD" in str(opt) or "Full Self-Driving" in str(opt) for opt in autopilot_meta)
            
            if is_fsd:
                filtered_cars.append({
                    "vin": car.get("VIN"),
                    "year": car.get("Year"),
                    "model": car.get("Model", "").upper(),
                    "trim": car.get("TrimName"),
                    "price": car.get("Price"),
                    "mileage": car.get("Odometer"),
                    "location": car.get("Location"),
                    "url": f"https://tesla.com{car.get('VIN')}"
                })
                
        return {"total_found": len(filtered_cars), "cars": filtered_cars}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
