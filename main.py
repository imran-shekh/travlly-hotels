import asyncio
import traceback
import httpx
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi import FastAPI, Request, Form, HTTPException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

AMADEUS_API_KEY = "AMADEUS_API_KEY"
AMADEUS_API_SECRET = "AMADEUS_API_SECRET"

access_token = None
token_expiry = 0


async def get_amadeus_token():
    global access_token, token_expiry
    if access_token and token_expiry > asyncio.get_event_loop().time():
        return access_token
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data["access_token"]
        token_expiry = asyncio.get_event_loop().time() + \
            token_data["expires_in"] - 10
        return access_token


@app.get("/", response_class=HTMLResponse)
def index():
    here = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(here, "templates", "index.html"))


@app.get("/api/search_hotels")
async def search_hotels(city: str):
    print("🧪 Requested city:", city.lower())
    try:
        token = await get_amadeus_token()

        # Step 1: Get cityCode
        async with httpx.AsyncClient() as client:
            loc_url = "https://test.api.amadeus.com/v1/reference-data/locations"
            loc_params = {
                "keyword": city,
                "subType": "CITY",
                "view": "FULL"
            }
            loc_headers = {"Authorization": f"Bearer {token}"}
            loc_res = await client.get(loc_url, headers=loc_headers, params=loc_params)
            loc_res.raise_for_status()
            loc_data = loc_res.json()
            city_data = loc_data.get("data", [])

            if not city_data:
                raise HTTPException(status_code=404, detail="City not found")

            city_code = city_data[0]["iataCode"]
            print("✅ Found cityCode:", city_code)

        # Step 2: Get hotelIds from city
        hotel_ids_url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
        hotel_ids_params = {
            "cityCode": city_code
        }
        async with httpx.AsyncClient() as client:
            hotel_ids_res = await client.get(hotel_ids_url, headers={"Authorization": f"Bearer {token}"}, params=hotel_ids_params)
            hotel_ids_res.raise_for_status()
            hotels_list = hotel_ids_res.json().get("data", [])

            if not hotels_list:
                raise HTTPException(
                    status_code=404, detail="No hotels found for this city")

            hotel_ids = ",".join([h["hotelId"]
                                 for h in hotels_list[:10]])  # limit to 10
            print("🏨 Found hotelIds:", hotel_ids)

        # Step 3: Get hotel offers using hotelIds
        hotel_offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
        hotel_offers_params = {
            "hotelIds": hotel_ids,
            "adults": 1
        }
        async with httpx.AsyncClient() as client:
            offers_res = await client.get(hotel_offers_url, headers={"Authorization": f"Bearer {token}"}, params=hotel_offers_params)
            offers_res.raise_for_status()
            hotels_data = offers_res.json()
            print("📦 Hotel data JSON:", hotels_data)

        # Format response
            hotels = []
        for offer in hotels_data.get("data", []):
            hotel = offer.get("hotel", {})
            offers = offer.get("offers", [])
            first_offer = offers[0] if offers else {}

            image_url = ""
            if "media" in hotel and hotel["media"]:
                image_url = hotel["media"][0].get("uri", "")
            # DEFAULT_IMAGE = image_url if image_url else "https://via.placeholder.com/150"
            DEFAULT_IMAGE = "https://via.placeholder.com/200x120?text=No+Image"
            hotels.append({
                "id": hotel.get("hotelId", "NA"),
                "name": hotel.get("name", "Hotel"),
                "address": hotel.get("address", {}).get("lines", [""])[0],
                "roomType": first_offer.get("room", {}).get("typeEstimated", {}).get("category", "Room"),
                "price": first_offer.get("price", {}).get("total", "N/A"),
                "currency": first_offer.get("price", {}).get("currency", "USD"),
                "image": DEFAULT_IMAGE
            })
        return {"hotels": hotels}

    except Exception as e:
        print("❌ Exception:", repr(e))
    traceback.print_exc()
    return {"hotels": []}


@app.post("/api/book_hotel")
async def book_hotel(hotel_id: str = Form(...), user_name: str = Form(...), email: str = Form(...)):
    return JSONResponse({"success": True, "message": f"Hotel booking simulated for {user_name}!"})
