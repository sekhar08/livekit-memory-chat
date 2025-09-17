import os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# LiveKit server-side token API
from livekit import api

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")


app = FastAPI()

@app.get("token")
def get_token(identity: str = Query(...), room: str = Query("default")):
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return JSONResponse(status_code=500, content={"error": "Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET"})

    grant = api.VideoGrant(room_join=True, room=room)
    at = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    at.identity = identity
    at.add_grant(grant)

    token = at.to_jwt()
    return {"identity": identity, "room": room, "token": token}

if __name__ == '__main__':
    port = int(os.getenv('TOKEN_SERVER_PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)