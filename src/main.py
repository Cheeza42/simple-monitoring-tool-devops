import json
import os
import time
import requests
from logger import logger
from machine_model import VMInstance
from colorama import init, Fore, Style
from storage import load_instances, backup_instances_file
from monitoring import validate_all_instances, display_statistics

API_BASE_URL = "http://127.0.0.1:5000"

init()

COLOR_RESET = Style.RESET_ALL
COLOR_GREEN = Fore.GREEN
COLOR_YELLOW = Fore.YELLOW
COLOR_RED = Fore.RED

# Checks whether a given machine name exists in the loaded instances
def check_machine_exists(instances, name):
    return any(instance.get("name") == name for instance in instances)

# Prints the main menu to the user
def print_intro():
    print("\n🛠️  Simple DevOps Monitoring Tool")
    print("-----------------------------------")
    print("1. Check if a machine exists")
    print("2. Exit")
    print("3. Validate all the VMs")
    print("4. Add a new machine")
    print("5. Display all machines")
    print("6. Display VMs statistics")
    print("7. Edit an exsisting machine")
    print("8. Remove a machine")

# Handles interactive flow for adding a new VM
def add_new_machine():
    # Step 0: Collect user input
    print("\n🆕 Add a New Machine")
    print("--------------------")

    name = input("Enter machine name: ").strip()
    ip = input("Enter IP address: ").strip()
    os_name = input("Enter operating system: ").strip()
    status = input("Enter status (UP/DOWN): ").strip().upper()
    check = input("Enter check type (ping/http) [ping]: ").strip().lower()
    if check == "":
        check = "ping"
    url = None
    if check == "http":
        url = input("Enter health-check URL: ").strip()

    data = {
        "name": name,
        "ip": ip,
        "os": os_name,
        "status": status,
        "check": check
    }

    if url:
        data["url"] = url

    # Step 1: Local validation using Pydantic model
    try:
        vm = VMInstance(**data)
    except Exception as e:
        print(f"❌ Invalid machine configuration: {e}\n")
        logger.error(f"Validation failed for new machine: {e}")
        retry = input("Would you like to try again? (y/n): ").strip().lower()
        if retry == "y":
            return "retry"
        else:
            print("🔄 Returning to main menu...\n")
            return "cancel"

    # Step 2: Fetch existing machines from API (instead of local file)
    try:
        resp = requests.get(f"{API_BASE_URL}/instances", timeout=3)
        existing_data = resp.json()
        instances = existing_data.get("instances", [])
    except Exception as e:
        print(f"❌ Failed to fetch machines from server: {e}\n")
        logger.error(f"Failed to fetch machines from server: {e}")
        return "cancel"

    # Step 3: Check for duplicate name
    if any(inst.get("name") == name for inst in instances):
        print(f"Error: Machine with name '{name}' already exists. Please choose a unique name.\n")
        logger.warning(f"Attempted to add duplicate machine name: '{name}'")
        retry = input("Would you like to try again? (y/n): ").strip().lower()
        if retry == "y":
            return "retry"
        else:
            print("🔄 Returning to main menu...\n")
            return "cancel"

    # Step 4: Ask user to confirm before sending to server
    print("\nPlease confirm the machine details:")
    time.sleep(0.8)
    print(json.dumps(data, indent=4))
    time.sleep(1)
    confirm = input("Save this machine? (y/n): ").strip().lower()
    if confirm != "y":
        print("Machine not saved.\n")
        logger.info(f"User canceled saving machine '{name}'")
        return "cancel"

    # Step 5: Send new machine to API (server will persist to JSON)
    try:
        resp = requests.post(f"{API_BASE_URL}/instances", json=data, timeout=3)
        if resp.status_code == 201:
            time.sleep(1.5)
            print("Machine saved successfully!\n")
            logger.info(f"Machine '{name}' was added successfully via API")
            return "added"
        else:
            print(f"Error: Failed to save machine: {resp.text}\n")
            logger.error(f"Failed to save machine '{name}' via API: {resp.text}")
            return "cancel"
    except Exception as e:
        print(f"Error: Failed to save machine: {e}\n")
        logger.error(f"Error during API save for machine '{name}': {e}")
        return "cancel"

# Displays the UP/DOWN status's color according to their status
def color_status(status: str) -> str:
    s = status.upper()
    if s == "UP":
        return COLOR_GREEN + status + COLOR_RESET
    if s == "DOWN":
        return COLOR_RED + status + COLOR_RESET 
    return status

# Displays the health status's color according to their status
def color_health(health: str) -> str:
    h = health.upper()
    if h == "OK":
        return COLOR_GREEN + health + COLOR_RESET
    if h == "WARN":
        return COLOR_YELLOW + health + COLOR_RESET
    if h == "CRIT":
        return COLOR_RED + health + COLOR_RESET
    return health

# Displays all machines from the configuration file
def display_all_instances():
    logger.info("User requested to display all machine instances.") 
    try:
        print("📦 Displaying machines...")
        time.sleep(3)

        # Fetch from server instead of local file
        try:
            response = requests.get("http://127.0.0.1:5000/instances")
            data = response.json()
            instances = data.get("instances", [])
        except Exception as e:
            print(f"❌ Failed to contact server: {e}")
            return

        if not instances:
            print("📭 No machines found.\n")
            return

        header = (
            f"{'NAME':<12}"
            f"{'IP':<18}"
            f"{'OS(ver)':<15}"
            f"{'STATUS':<10}"
            f"{'HEALTH':<10}"
            f"{'RT(ms)':<10}"
            f"{'CPU%':<8}"
            f"{'MEM%':<8}"
        )
        print()
        print(header)
        print("-" * len(header))

        for inst in instances:
            name = str(inst.get("name"))
            ip = str(inst.get("ip"))
            os_name = str(inst.get("os"))
            status_raw = str(inst.get("status"))
            health_raw = str(inst.get("health"))
            rt = str(inst.get("response_time_ms"))
            cpu = str(inst.get("cpu_percent"))
            mem = str(inst.get("memory_percent"))
            
            status_colored = color_status(status_raw)
            health_colored = color_health(health_raw)

            print(
                f"{name:<12}"
                f"{ip:<18}"
                f"{os_name:<15}"
                f"{status_colored:<18}"
                f"{health_colored:<17}"
                f"{rt:<10}"
                f"{cpu:<8}"
                f"{mem:<8}"
            )

        print()

    except FileNotFoundError:
        print("❌ Configuration file not found.")
    except Exception as e:
        print(f"❌ Failed to load machines: {e}")

# Handles interactive editing of an existing machine
def edit_existing_machine():
    print("\n✏️ Edit Existing Machine")
    print("------------------------")
    instances = load_instances()
    name = input("Enter the machine name to edit: ").strip()
    time.sleep(1.2)

    # Search for machine by name
    for idx, inst in enumerate(instances):
        if inst.get("name") == name:
            # Display current configuration
            print("\nCurrent configuration:")
            time.sleep(0.8)
            print(json.dumps(inst, indent=4))
            print("\nPress Enter to keep existing value.\n")

            # Ask user for new values (optional)
            new_ip = input(f"IP address [{inst['ip']}]: ").strip()
            new_os = input(f"Operating system [{inst['os']}]: ").strip()
            new_status = input(f"Status (UP/DOWN) [{inst['status']}]: ").strip().upper()

            # Create updated data (keep original if input is empty)
            updated_data = {
                "name": name,  # name is not editable
                "ip": new_ip if new_ip else inst["ip"],
                "os": new_os if new_os else inst["os"],
                "status": new_status if new_status else inst["status"]
            }

            # Validate using Pydantic model
            try:
                updated_vm = VMInstance(**updated_data)
            except Exception as e:
                print(f"\n❌ Invalid configuration: {e}")
                logger.error(f"Validation failed while editing '{name}': {e}")
                return

            # Confirm before saving
            confirm = input("\nSave changes? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Changes discarded.\n")
                logger.info(f"User cancelled editing for machine '{name}'")
                return
            
            # Backup before writing
            backup_instances_file()

            # Save the updated data back to file
            instances[idx] = updated_data
            path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
            with open(path, 'w') as file:
                json.dump({"instances": instances}, file, indent=4)
            
            print("💾 Saving changes...")
            time.sleep(1.3)
            print("✅ Machine updated successfully.\n")
            time.sleep(0.8)
            logger.info(f"Machine '{name}' was updated.")
            return

    # If machine was not found
    print(f"❌ Machine '{name}' not found.\n")
    logger.warning(f"Attempted to edit non-existing machine '{name}'")

# Handles interactive deletion of a machine
def remove_machine():
    print("\n🗑️ Remove a Machine")
    print("--------------------")
    instances = load_instances()
    name = input("Enter the machine name to remove: ").strip()

    print("🔍 Searching for machine...")
    time.sleep(1)

    for idx, inst in enumerate(instances):
        if inst.get("name") == name:
            print("\nMachine found:")
            print(json.dumps(inst, indent=4))
            time.sleep(0.8)

            confirm = input("\nAre you sure you want to delete this machine? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❎ Deletion canceled.\n")
                logger.info(f"User canceled deletion of machine '{name}'")
                return

            # Remove and save
            del instances[idx]
            
            # Backup before writing
            backup_instances_file()

            path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
            with open(path, 'w') as file:
                json.dump({"instances": instances}, file, indent=4)

            time.sleep(1.3)
            print("✅ Machine deleted successfully.\n")
            logger.warning(f"Machine '{name}' was deleted.")
            return

    print(f"❌ Machine '{name}' not found.\n")
    logger.warning(f"Attempted to delete non-existing machine '{name}'")

# Main function that runs the monitoring tool
def main():
    while True:
        print_intro()
        choice = input("Choose an option (from 1-8): ").strip()

        # Option 1: Check if a machine exists
        if choice == '1':
            instances = load_instances()
            checking = True

            while checking:
                machine_name = input("Enter machine name to check: ").strip()

                if not machine_name:
                    print("⚠️  Machine name cannot be empty.\n")
                    time.sleep(1)
                    continue

                # Simulate a loading/checking delay
                print("🔍 Checking machine status...")
                time.sleep(1.5)

                if check_machine_exists(instances, machine_name):
                    print(f"✅ Machine '{machine_name}' exists.\n")
                    logger.info(f"Machine '{machine_name}' exists")

                else:
                    print(f"❌ Machine '{machine_name}' does not exist.\n")
                    logger.warning(f"Machine '{machine_name}' does not exist")
                time.sleep(1)

                # Ask user if they want to check another machine
                again = input("Would you like to check another machine? (y/n): ").strip().lower()
                if again != 'y':
                    print("🔄 Returning to main menu.\n")
                    time.sleep(1.5)
                    checking = False

        # Option 2: Exit the tool
        elif choice == '2':
            print("👋 Exiting. Goodbye!")
            time.sleep(1)
            break

        # Option 3: Validate all VMs and return to main menu
        elif choice == '3':
            instances = load_instances()
            validate_all_instances(instances)
            input("\nValidation complete, press Enter to return to menu...")

        # Option 4: Add new machines (loop until user stops)
        elif choice == '4':
            adding = True
            while adding:
                result = add_new_machine()
                if result == "retry":
                    continue  # Try adding a machine again
                if result == "cancel":
                    print("🔄 Returning to main menu...\n")
                    time.sleep(1)
                    adding = False
                    continue
                if result == "added":
                    again = input("Would you like to add another machine? (y/n): ").strip().lower()
                    if again != 'y':
                        print("🔄 Returning to main menu...\n")
                        time.sleep(1)
                        adding = False
       
        # Option 5: Display all machines
        elif choice == '5':
            display_all_instances()
            input("\nDisplay complete, press Enter to return to menu...")
        
        # Option 6: Display statistics summary
        elif choice == '6':
            display_statistics()
            input("\nDisplay complete, press Enter to return to menu...")
        
        # Option 7: Edit an existing machine
        elif choice == '7':
            edit_existing_machine()
            input("\nEdit complete, press Enter to return to menu...")
        
        # Option 8: Remove a machine
        elif choice == '8':
            remove_machine()
            input("\nDeletion complete, press Enter to return to menu...")

        else:
            print("❗ Invalid choice. Please enter an option between 1-8.\n")
            time.sleep(1)

# Entry point
if __name__ == "__main__":
    main()
