import json
import os
import shutil
from logger import logger

# Creates a backup copy of the instances.json file
def backup_instances_file():
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
        backup_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances_backup.json')
        shutil.copyfile(config_path, backup_path)
        logger.info("Backup created successfully.")
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")

# Loads instance data from the JSON configuration file
def load_instances():
    path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
    with open(path, 'r') as file:
        data = json.load(file)
    return data.get('instances', [])
