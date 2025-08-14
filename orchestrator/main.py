# orchestrator/main.py
# The main application for the LISE Orchestrator.

from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import yaml # We'll need this to load scenarios later
import os   # To build file paths

# --- Pydantic Models ---
# These models define the structure of the data we expect to receive.
# FastAPI uses them to validate incoming requests.
class AgentRegistration(BaseModel):
    display_name: str
    ip_address: str

# Create the FastAPI application instance
app = FastAPI(
    title="LISE Orchestrator API",
    description="The central command server for the Local Incident Simulation Environment.",
    version="1.0.0"
)

# --- IN-MEMORY DATABASE ---
db = {
    "agents": {},  # e.g., {"Komal-PC": {"ip_address": "192.168.1.10"}}
    "scenarios": []
}

# --- API ENDPOINTS ---

@app.get("/", tags=["Root"])
async def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"message": "Welcome to the LISE Orchestrator!"}

@app.post("/api/agents/register", tags=["Agent Management"])
async def register_agent(agent: AgentRegistration, request: Request):
    """
    Endpoint for agents to register themselves with the orchestrator.
    """
    # agent.ip_address is the IP the agent *thinks* it has.
    # request.client.host is the IP the orchestrator *sees*. We'll trust the client for now.
    db["agents"][agent.display_name] = {"ip_address": agent.ip_address}
    print(f"--- Agent Registered: {agent.display_name} at {agent.ip_address} ---")
    return {"status": "success", "message": f"Agent '{agent.display_name}' registered."}

@app.get("/api/agents", tags=["Agent Management"])
async def get_registered_agents():
    """Returns a list of all currently registered agents."""
    return {"agents": db["agents"]}


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Orchestrator Server ---")
    uvicorn.run(app, host="0.0.0.0", port=8080)
