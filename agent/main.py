# agent/main.py
# The main application for the LISE Agent.

from fastapi import FastAPI
import uvicorn

# Create the FastAPI application instance
app = FastAPI(
    title="LISE Agent API",
    description="The agent application that runs on student machines to manage simulation containers.",
    version="1.0.0"
)

# --- AGENT STATE ---
# A simple dictionary to store the agent's current state.
state = {
    "is_connected": False,
    "orchestrator_ip": None,
    "display_name": None,
    "current_scenario": None,
    "status_message": "Disconnected"
}

# --- API ENDPOINTS ---

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the agent server is running.
    """
    return {"message": "LISE Agent is running.", "state": state}


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Agent Server ---")
    # We run the agent on a different port (e.g., 8000) to avoid conflicts
    # with the orchestrator if they were run on the same machine.
    uvicorn.run(app, host="0.0.0.0", port=8000)
