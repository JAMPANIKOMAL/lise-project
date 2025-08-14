# orchestrator/main.py
# The main application for the LISE Orchestrator.

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import yaml # To load scenarios
import os   # To build file paths
import requests # To send commands to agents

# --- Pydantic Models ---
class AgentRegistration(BaseModel):
    display_name: str
    ip_address: str

class SimulationRequest(BaseModel):
    agent_name: str
    scenario_name: str

# Create the FastAPI application instance
app = FastAPI(
    title="LISE Orchestrator API",
    description="The central command server for the Local Incident Simulation Environment.",
    version="1.0.0"
)

# --- IN-MEMORY DATABASE ---
db = {
    "agents": {},  # e.g., {"Komal-PC": {"ip_address": "192.168.1.10"}}
    "scenarios": [] # This will be populated on startup
}

# --- Helper Functions ---
def load_scenarios():
    """Finds and loads all scenario YAML files from the scenarios directory."""
    scenarios_dir = "scenarios"
    for filename in os.listdir(scenarios_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            filepath = os.path.join(scenarios_dir, filename)
            with open(filepath, 'r') as f:
                # We'll just store the raw compose file path for now
                db["scenarios"].append({
                    "name": filename,
                    "compose_file_path": filepath
                })
    print(f"--- Loaded {len(db['scenarios'])} scenarios. ---")

# --- FastAPI Events ---
@app.on_event("startup")
async def startup_event():
    """This function runs when the server starts up."""
    load_scenarios()

# --- API ENDPOINTS ---

@app.get("/", tags=["Root"])
async def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"message": "Welcome to the LISE Orchestrator!"}

@app.post("/api/agents/register", tags=["Agent Management"])
async def register_agent(agent: AgentRegistration):
    """Endpoint for agents to register themselves with the orchestrator."""
    db["agents"][agent.display_name] = {"ip_address": agent.ip_address}
    print(f"--- Agent Registered: {agent.display_name} at {agent.ip_address} ---")
    return {"status": "success", "message": f"Agent '{agent.display_name}' registered."}

@app.get("/api/agents", tags=["Agent Management"])
async def get_registered_agents():
    """Returns a list of all currently registered agents."""
    return {"agents": db["agents"]}

@app.get("/api/scenarios", tags=["Scenario Management"])
async def get_scenarios():
    """Returns a list of all loaded scenarios."""
    return {"scenarios": db["scenarios"]}

@app.post("/api/simulation/start", tags=["Simulation Control"])
async def start_simulation(sim_request: SimulationRequest):
    """Tells a specific agent to start a specific scenario."""
    agent_info = db["agents"].get(sim_request.agent_name)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent '{sim_request.agent_name}' not found.")

    # Find the scenario details
    scenario_info = next((s for s in db["scenarios"] if s["name"] == sim_request.scenario_name), None)
    if not scenario_info:
        raise HTTPException(status_code=404, detail=f"Scenario '{sim_request.scenario_name}' not found.")

    agent_ip = agent_info["ip_address"]
    agent_url = f"http://{agent_ip}:8000/api/scenario/start"
    payload = {"compose_file_path": scenario_info["compose_file_path"]}

    try:
        print(f"--- Sending start command for '{sim_request.scenario_name}' to {sim_request.agent_name} at {agent_ip} ---")
        response = requests.post(agent_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send command to agent: {e}")


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Orchestrator Server ---")
    uvicorn.run(app, host="0.0.0.0", port=8080)
