# agent/main.py
# The main application for the LISE Agent.

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import requests
import socket
import subprocess
import os
import threading
import time

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

# --- Mount Static Files ---
app.mount("/static", StaticFiles(directory="agent/static"), name="static")

# --- AGENT STATE ---
state = {
    "is_connected": False,
    "orchestrator_ip": None,
    "display_name": None,
    "current_scenario": None,
    "status_message": "Disconnected",
    "log_thread": None # To hold the running log thread
}

# --- Helper Functions ---
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def stream_logs(compose_file, agent_name, orchestrator_ip):
    """A function to be run in a background thread to stream logs."""
    log_url = f"http://{orchestrator_ip}:8080/api/log"
    
    # Give Docker a moment to start the containers before streaming logs
    time.sleep(3) 
    
    command = ["docker-compose", "-f", compose_file, "logs", "-f", "--no-log-prefix"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    print(f"--- Starting log stream for {agent_name} ---")
    
    for line in iter(process.stdout.readline, ''):
        if not line:
            break
        try:
            log_entry = {"agent_name": agent_name, "log_line": line.strip()}
            requests.post(log_url, json=log_entry, timeout=2)
        except requests.exceptions.RequestException:
            # If we can't send logs, we just print an error and continue trying
            print(f"--- WARN: Could not send log line to orchestrator at {log_url} ---")
            
    process.stdout.close()
    process.wait()
    print(f"--- Log stream for {agent_name} ended. ---")


# --- API ENDPOINTS ---

@app.get("/", response_class=FileResponse, tags=["UI"])
async def read_index():
    return "agent/static/index.html"

@app.post("/api/connect", tags=["Connection Management"])
async def connect_to_orchestrator(conn_request: ConnectionRequest):
    state["display_name"] = conn_request.display_name
    state["orchestrator_ip"] = conn_request.orchestrator_ip
    orchestrator_url = f"http://{state['orchestrator_ip']}:8080/api/agents/register"
    agent_payload = {"display_name": state["display_name"], "ip_address": get_local_ip()}
    try:
        response = requests.post(orchestrator_url, json=agent_payload, timeout=5)
        response.raise_for_status()
        state["is_connected"] = True
        state["status_message"] = f"Connected to {state['orchestrator_ip']}"
        print(f"--- Successfully registered with orchestrator at {state['orchestrator_ip']} ---")
        return {"status": "success", "message": state["status_message"]}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenario/start", tags=["Simulation Control"])
async def start_scenario(request: ScenarioStartRequest, background_tasks: BackgroundTasks):
    compose_file = request.compose_file_path
    if not os.path.exists(compose_file):
        raise HTTPException(status_code=404, detail=f"Compose file not found: {compose_file}")
    if state.get("current_scenario"):
        raise HTTPException(status_code=400, detail="A scenario is already running.")

    command = ["docker-compose", "-f", compose_file, "up", "--build", "-d"]
    try:
        print(f"--- Starting scenario: {' '.join(command)} ---")
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        state["current_scenario"] = compose_file
        state["status_message"] = f"Running scenario: {os.path.basename(compose_file)}"
        
        # Start the log streaming in a background thread
        log_thread = threading.Thread(
            target=stream_logs,
            args=(compose_file, state["display_name"], state["orchestrator_ip"]),
            daemon=True
        )
        state["log_thread"] = log_thread
        log_thread.start()

        print(f"--- Scenario '{os.path.basename(compose_file)}' started successfully. ---")
        return {"status": "success", "message": "Scenario started."}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Docker Compose failed: {e.stderr}")

@app.post("/api/scenario/stop", tags=["Simulation Control"])
async def stop_scenario():
    if not state.get("current_scenario"):
        raise HTTPException(status_code=400, detail="No scenario is currently running.")
    compose_file = state["current_scenario"]
    command = ["docker-compose", "-f", compose_file, "down"]
    try:
        print(f"--- Stopping scenario: {' '.join(command)} ---")
        subprocess.run(command, check=True, capture_output=True, text=True)
        state["current_scenario"] = None
        state["status_message"] = "Idle"
        if state.get("log_thread") and state["log_thread"].is_alive():
             # The thread will stop on its own as the 'logs -f' command ends
             state["log_thread"] = None
        print(f"--- Scenario '{os.path.basename(compose_file)}' stopped successfully. ---")
        return {"status": "success", "message": "Scenario stopped."}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Docker Compose 'down' failed: {e.stderr}")

# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Agent Server ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)
