LISE Educator's Guide (Orchestrator)
Welcome to the Local Incident Simulation Environment! This guide will help you set up and run a cybersecurity simulation for your class.

Prerequisites
A Windows computer.

Docker Desktop must be installed and running.

The LISE_Orchestrator.exe file.

Running a Simulation
Step 1: Start the Orchestrator

Double-click the LISE_Orchestrator.exe file.

A terminal window will appear (this is the server), and the Orchestrator dashboard will open in your web browser at http://localhost:8080.

Step 2: Have Students Connect

Provide your computer's IP address to the students.

As students run their LISE_Agent.exe and connect, their chosen names will appear in the "1. Connected Agents" panel on your dashboard.

Step 3: Set Up the Mission

From the "Select Incident" dropdown, choose the scenario you want to run (e.g., web-injection-scenario.yaml).

Click on a student's name in the "Connected Agents" panel to assign them to the Blue Team.

Step 4: Launch the Simulation

Click the "Launch Simulation" button.

The command will be sent to the student's machine to start the containers.

Step 5: Monitor the Live Log

Watch the "Live Event Log" panel on the right. You will see the real-time output from the containers running on the student's machine, allowing you to monitor the progress of the simulation.