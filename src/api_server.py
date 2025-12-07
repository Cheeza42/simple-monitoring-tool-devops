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

@app.put("/instances/<string:name>")
def update_instance(name):
    # Get payload from client (partial updates allowed)
    payload = request.get_json(silent=True) or {}

    # If file doesn't exist, nothing to update
    if not INSTANCES_FILE.exists():
        return jsonify({"error": "No instances file found"}), 404

    # Load current instances
    with INSTANCES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize structure to always work with "instances" list
    if isinstance(data, dict) and "instances" in data:
        instances = data["instances"]
    elif isinstance(data, list):
        instances = data
    else:
        instances = []

    # Find machine by its unique name
    index = None
    for i, inst in enumerate(instances):
        if inst.get("name") == name:
            index = i
            break

    # If machine is not found — cannot update
    if index is None:
        return jsonify({"error": f"Machine '{name}' not found"}), 404

    # Merge existing fields with new fields (partial update)
    merged = {**instances[index], **payload}

    # Validate updated data using Pydantic model
    try:
        vm = VMInstance(**merged)
    except Exception as e:
        logger.error(f"Invalid VM update for '{name}': {e}")
        return jsonify({"error": str(e)}), 400

    # Save the updated instance back into the list
    instances[index] = merged
    full_data = {"instances": instances}

    # Create backup before writing (safety mechanism)
    backup_instances_file()

    # Write updated data to disk
    with INSTANCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)

    logger.info(f"Machine '{name}' updated via API")

    # PUT successful
    return jsonify({"status": "ok"}), 200

@app.delete("/instances/<string:name>")
def delete_instance(name):
    # If there is no JSON file, nothing to delete
    if not INSTANCES_FILE.exists():
        return jsonify({"error": "No instances file found"}), 404

    # Load current instances
    with INSTANCES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize structure
    if isinstance(data, dict) and "instances" in data:
        instances = data["instances"]
    elif isinstance(data, list):
        instances = data
    else:
        instances = []

    # Find machine by name
    index = None
    for i, inst in enumerate(instances):
        if inst.get("name") == name:
            index = i
            break

    # If machine doesn't exist — cannot delete
    if index is None:
        return jsonify({"error": f"Machine '{name}' not found"}), 404

    # Remove the machine from the list
    deleted_instance = instances.pop(index)
    full_data = {"instances": instances}

    # Backup before writing
    backup_instances_file()

    # Write updated list back to JSON file
    with INSTANCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)

    logger.info(f"Machine '{name}' deleted via API")

    # Successful deletion
    return jsonify({"deleted": deleted_instance}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
