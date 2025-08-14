LISE 1.0: Project Build Summary
This document outlines the development lifecycle and key technical decisions made during the creation of the Local Incident Simulation Environment (LISE), Version 1.0.

Phase 0: Project Scaffolding & Design
The initial phase focused on establishing a solid and scalable foundation for the project.

Technology Stack Selection: We chose a modern, high-performance, and entirely free stack:

Backend: Python with the FastAPI framework for its speed, automatic data validation, and built-in documentation.

Containerization: Docker and Docker Compose were selected to create isolated, reproducible incident environments.

Frontend: Vanilla JavaScript (ES6+) and Tailwind CSS were chosen to build a clean, lightweight, and modern UI without the overhead of a large framework.

Project Structuring: A logical directory structure was created to separate the Orchestrator and Agent applications, their web assets (static), and the incident definitions (scenarios).

Version Control: The project was initialized as a Git repository to ensure proper change tracking and team collaboration.

Incident Definition: The first incident, "Web Command Injection," was defined using two Dockerfiles (one for the attacker, one for the victim) and a docker-compose.yaml file to orchestrate the services and their isolated network.

Phase 1: Backend Development & Core Logic
This phase involved building the server-side "brains" of the LISE platform.

API Server Implementation: Two separate FastAPI servers were developed: orchestrator/main.py and agent/main.py.

Agent Registration: We implemented the first core interaction. The Agent was programmed to send a POST request with its details to the Orchestrator's /api/agents/register endpoint. The Orchestrator would then store the connected agent's information.

Scenario Orchestration: The central control flow was built:

The Orchestrator was programmed to load all available scenarios from the /scenarios directory on startup.

An endpoint (/api/simulation/start) was created on the Orchestrator to receive a launch command.

Upon receiving the command, the Orchestrator sends a request to the appropriate Agent's /api/scenario/start endpoint.

The Agent was programmed to receive this request and execute the corresponding docker-compose up command using Python's subprocess module, launching the containerized incident.

Asynchronous Task Handling: We identified and fixed a critical bug where the docker-compose command would block the Agent and cause a timeout on the Orchestrator. The fix was to change from subprocess.run to the non-blocking subprocess.Popen, allowing the Agent to respond instantly while the simulation started in the background.

Phase 2: Frontend Integration & Real-Time Features
With the backend logic complete, this phase focused on building the user interfaces.

UI Development: Two distinct web interfaces were created in the static folders for the Orchestrator and Agent.

API Integration: JavaScript code was written to connect the UIs to their respective backend APIs. This allowed the Orchestrator UI to dynamically fetch and display the list of connected agents and available scenarios.

Real-Time Log Streaming: This was the final major feature. We implemented a WebSocket-based system:

The Agent was updated to run docker-compose logs -f in a background thread after starting a scenario.

Each log line captured by the Agent is sent via a POST request to a new /api/log endpoint on the Orchestrator.

The Orchestrator immediately broadcasts any log message it receives to all connected UI clients via its /ws/log-stream WebSocket endpoint.

The Orchestrator's UI was updated with a log viewer panel and the JavaScript code needed to connect to the WebSocket and display the incoming log messages in real-time.

Phase 3: Packaging & Finalization
The final phase focused on turning the project into distributable software.

Pathing Bug Fix: We identified and fixed a RuntimeError that occurred when running the packaged app. The code was updated with a helper function to correctly resolve asset paths (static, scenarios) when running as a bundled executable.

Application Packaging: The PyInstaller tool was used to bundle the Python scripts, dependencies, and all static assets into two standalone executables: LISE_Orchestrator.exe and LISE_Agent.exe.

Documentation: User guides were created for both the Educator (Orchestrator) and the Student (Agent), explaining the prerequisites and steps for using the software.

The result is a complete, functional, and distributable version of the LISE platform, ready for use and future development.