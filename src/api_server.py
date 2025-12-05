from flask import Flask, jsonify, request
import json
from pathlib import Path
from machine_model import VMInstance
from logger import logger
from storage import backup_instances_file

app = Flask(__name__)

# Path to the instances JSON file
INSTANCES_FILE = Path("configs/instances.json")


@app.get("/instances")
def get_instances():
    """
    Return all VM instances in a normalized structure:
    {"instances": [...]}
    """
    if not INSTANCES_FILE.exists():
        return jsonify({"instances": []})

    with INSTANCES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to ensure "instances" is always a list
    if isinstance(data, dict) and "instances" in data:
        instances = data["instances"]
    elif isinstance(data, list):
        instances = data
    else:
        instances = []

    return jsonify({"instances": instances})


@app.post("/instances")
def add_instance():
    """
    Add a new VM instance:
    - Validate using Pydantic model
    - Prevent duplicate names
    - Write to JSON file with backup
    """
    payload = request.get_json(silent=True) or {}

    # Step 1: Validate using Pydantic model
    try:
        vm = VMInstance(**payload)
    except Exception as e:
        logger.error(f"Invalid VM payload: {e}")
        return jsonify({"error": str(e)}), 400

    # Step 2: Load existing instances
    if INSTANCES_FILE.exists():
        with INSTANCES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "instances" in data:
            instances = data["instances"]
        elif isinstance(data, list):
            instances = data
        else:
            instances = []
    else:
        instances = []

    # Step 3: Prevent duplicate VM names
    if any(inst.get("name") == vm.name for inst in instances):
        return jsonify({"error": f"Machine '{vm.name}' already exists"}), 409

    # Step 4: Append new machine and save file
    instances.append(payload)
    full_data = {"instances": instances}

    backup_instances_file()

    with INSTANCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)

    logger.info(f"Machine '{vm.name}' added via API")
    return jsonify({"status": "ok"}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
