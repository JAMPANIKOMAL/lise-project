# orchestrator/main.py
# The main application for the LISE Orchestrator.

from fastapi import FastAPI
import uvicorn

# Create the FastAPI application instance
app = FastAPI(
    title="LISE Orchestrator API",
    description="The central command server for the Local Incident Simulation Environment.",
    version="1.0.0"
)

# --- IN-MEMORY DATABASE ---
# A simple dictionary to store the state of connected agents.
# In a real-world scenario, you might use a more robust database.
db = {
    "agents": {},  # e.g., {"Komal-PC": "192.168.1.10"}
    "scenarios": []
}

# --- API ENDPOINTS ---

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the server is running.
    """
    return {"message": "Welcome to the LISE Orchestrator!"}


# This block allows us to run the server directly from the script
if __name__ == "__main__":
    print("--- Starting LISE Orchestrator Server ---")
    # Uvicorn is the server that runs our FastAPI application.
    # We run it on host "0.0.0.0" to make it accessible on the local network.
    uvicorn.run(app, host="0.0.0.0", port=8080)
