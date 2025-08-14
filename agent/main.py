# agent/main.py
# The main application for the LISE Agent.

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests # To send HTTP requests to the orchestrator
import socket   # To get the local IP address

# --- Pydantic Models ---
class ConnectionRequest(BaseModel):
    display_name: str
    orchestrator_ip: str

# Create the FastAPI application instance
app = FastAPI(
    title="LISE Agent API",
    description="The agent application that runs on student machines to manage simulation containers.",
    version="1.0.0"
)

# --- AGENT STATE ---
state = {
    "is_connected": False,
    "orchestrator_ip": None,
    "display_name": None,
    "current_scenario": None,
    "status_message": "Disconnected"
}

# --- Helper Functions ---
def get_local_ip():
    """Gets the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- API ENDPOINTS ---

@app.get("/", tags=["Root"])
async def read_root():
    """A simple root endpoint to confirm the agent server is running."""
    return {"message": "LISE Agent is running.", "state": state}

@app.post("/api/connect", tags=["Connection Management"])
async def connect_to_orchestrator(conn_request: ConnectionRequest):
    """
    Receives connection info (from its own UI later) and attempts to
    register with the orchestrator.
    """
    state["display_name"] = conn_request.display_name
    state["orchestrator_ip"] = conn_request.orchestrator_ip
    
    orchestrator_url = f"http://{state['orchestrator_ip']}:8080/api/agents/register"
    agent_payload = {
        "display_name": state["display_name"],
        "ip_address": get_local_ip()
    }
    
    try:
        response = requests.post(orchestrator_url, json=agent_payload, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        state["is_connected"] = True
        state["status_message"] = f"Connected to {state['orchestrator_ip']}"
        print(f"--- Successfully registered with orchestrator at {state['orchestrator_ip']} ---")
        return {"status": "success", "message": state["status_message"]}

    except requests.exceptions.RequestException as e:
        state["is_connected"] = False
        state["status_message"] = f"Failed to connect to orchestrator: {e}"
        print(f"--- ERROR: Could not connect to orchestrator at {orchestrator_url} ---")
        return {"status": "error", "message": state["status_message"]}


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Agent Server ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)
