# agent/main.py
# The main application for the LISE Agent.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests # To send HTTP requests to the orchestrator
import socket   # To get the local IP address
import subprocess # To run docker-compose commands
import os # To handle file paths

# --- Pydantic Models ---
class ConnectionRequest(BaseModel):
    display_name: str
    orchestrator_ip: str

class ScenarioStartRequest(BaseModel):
    compose_file_path: str

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
    "status_message": "Disconnected",
    "active_process": None # To hold the running subprocess
}

# --- Helper Functions ---
def get_local_ip():
    """Gets the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
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
    Receives connection info and attempts to register with the orchestrator.
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
        response.raise_for_status()
        
        state["is_connected"] = True
        state["status_message"] = f"Connected to {state['orchestrator_ip']}"
        print(f"--- Successfully registered with orchestrator at {state['orchestrator_ip']} ---")
        return {"status": "success", "message": state["status_message"]}

    except requests.exceptions.RequestException as e:
        state["is_connected"] = False
        state["status_message"] = f"Failed to connect to orchestrator: {e}"
        print(f"--- ERROR: Could not connect to orchestrator at {orchestrator_url} ---")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenario/start", tags=["Simulation Control"])
async def start_scenario(request: ScenarioStartRequest):
    """Receives a command from the orchestrator to start a Docker Compose scenario."""
    compose_file = request.compose_file_path
    if not os.path.exists(compose_file):
        raise HTTPException(status_code=404, detail=f"Compose file not found: {compose_file}")

    if state.get("active_process"):
        raise HTTPException(status_code=400, detail="A scenario is already running.")

    command = ["docker-compose", "-f", compose_file, "up", "--build", "-d"]
    
    try:
        print(f"--- Starting scenario: {' '.join(command)} ---")
        # We run this in the background ('-d' flag)
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        state["current_scenario"] = compose_file
        state["status_message"] = f"Running scenario: {os.path.basename(compose_file)}"
        print(f"--- Scenario '{os.path.basename(compose_file)}' started successfully. ---")
        return {"status": "success", "message": state["status_message"], "output": process.stdout}
    except subprocess.CalledProcessError as e:
        print(f"--- ERROR starting scenario: {e.stderr} ---")
        raise HTTPException(status_code=500, detail=f"Docker Compose failed: {e.stderr}")

@app.post("/api/scenario/stop", tags=["Simulation Control"])
async def stop_scenario():
    """Stops the currently running Docker Compose scenario."""
    if not state.get("current_scenario"):
        raise HTTPException(status_code=400, detail="No scenario is currently running.")
        
    compose_file = state["current_scenario"]
    command = ["docker-compose", "-f", compose_file, "down"]
    
    try:
        print(f"--- Stopping scenario: {' '.join(command)} ---")
        subprocess.run(command, check=True, capture_output=True, text=True)
        state["current_scenario"] = None
        state["status_message"] = "Idle"
        print(f"--- Scenario '{os.path.basename(compose_file)}' stopped successfully. ---")
        return {"status": "success", "message": "Scenario stopped."}
    except subprocess.CalledProcessError as e:
        print(f"--- ERROR stopping scenario: {e.stderr} ---")
        raise HTTPException(status_code=500, detail=f"Docker Compose 'down' failed: {e.stderr}")


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Agent Server ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)
