import json
import os
import shutil
import time
from collections import Counter
from logger import logger
from machine_model import VMInstance
from colorama import init, Fore, Style

init()

COLOR_RESET = Style.RESET_ALL
COLOR_GREEN = Fore.GREEN
COLOR_YELLOW = Fore.YELLOW
COLOR_RED = Fore.RED

def backup_instances_file():
    """Creates a backup copy of the instances.json file."""
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

def monitor_vm(vm: VMInstance):
    print(f"🧪 Running health check for '{vm.name}'...")
    time.sleep(0.8)

    if vm.check == "ping":
        print(f"   [SIM] PING {vm.ip} ... OK")
    elif vm.check == "http":
        print(f"   [SIM] HTTP GET {vm.url} ... OK")

    print()


# Validate all VM dictionaries against the VMInstance model
def validate_all_instances(instances):
    logger.info("🔍 Started validating all VM instances from JSON.")
    print("\n🔍 Validating machine configurations...")
    time.sleep(1.5)

    for idx, data in enumerate(instances, 1):
        try:
            # Simulate processing delay
            print(f"⏳ Validating VM #{idx}...")
            time.sleep(1.2)

            # Attempt to create a VMInstance object from the dictionary
            vm = VMInstance(**data)
            print(f"✅ VM #{idx} ('{vm.name}') is valid.\n")
            logger.info(f"Machine #{vm.name} is valid")
            monitor_vm(vm)
        except Exception as e:
            print(f"❌ VM #{idx} failed validation:")
            print(f"   Error: {e}\n")
            logger.error(f"Machine #{idx} is invalid: {e}")
        time.sleep(0.8)  # Slight pause between VMs

    print("✔️ Validation process completed.")

def add_new_machine():
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

    # Step 1: Validate input using Pydantic
    try:
        vm = VMInstance(**data)
    except Exception as e:
        print(f"❌ Invalid machine configuration: {e}\n")
        logger.error(f"Validation failed for new machine: {e}")
        retry = input("Would you like to try again? (y/n): ").strip().lower()
        if retry == 'y':
            return "retry"
        else:
            print("🔄 Returning to main menu...\n")
            return "cancel"

      

    # Step 2: Check for duplicate name
    instances = load_instances()
    if any(inst.get("name") == name for inst in instances):
        print(f"Error: Machine with name '{name}' already exists. Please choose a unique name.\n")
        logger.warning(f"Attempted to add duplicate machine name: '{name}'")
        retry = input("Would you like to try again? (y/n): ").strip().lower()
        if retry == 'y':
            return "retry"
        else:
            print("🔄 Returning to main menu...\n")
            return "cancel"

    # Step 3: Confirm before saving
    print("\nPlease confirm the machine details:")
    time.sleep(0.8)
    print(json.dumps(data, indent=4))
    time.sleep(1)
    confirm = input("Save this machine? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Machine not saved.\n")
        logger.info(f"User canceled saving machine '{name}'")
        return "cancel"

    # Step 4: Save to file
    instances.append(data)
    full_data = {"instances": instances}
    path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
    
    # Backup before writing
    backup_instances_file()

    try:
        with open(path, 'w') as file:
            json.dump(full_data, file, indent=4)
        time.sleep(1.5)
        print("Machine saved successfully!\n")
        logger.info(f"Machine '{name}' was added successfully")
        return "added"
    
    except Exception as e:
        print(f"Error: Failed to save machine: {e}\n")
        return "cancel"

# Displays the UP/DOWN status's color according to their status.
def color_status(status: str) -> str:
    s = status.upper()
    if s == "UP":
        return COLOR_GREEN + status + COLOR_RESET
    if s == "DOWN":
        return COLOR_RED + status + COLOR_RESET 
    return status

# Displays the health status's color according to their status.
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
    path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')
    try:
        print("📦 Displaying machines...")
        time.sleep(3)

        with open(path, 'r') as file:
            data = json.load(file)
            instances = data.get("instances", [])

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


# Display summary statistics about the VM instances
def display_statistics():
    logger.info("User requested VM statistics.")
    print(" 📊 Gathering VM statistics...")
    time.sleep(1.5)
    instances = load_instances()

    if not instances:
        print("📭 No machines found.\n")
        return

    total = len(instances)
    up = sum(1 for inst in instances if inst.get("status") == "UP")
    down = total - up

    os_counter = Counter()
    for inst in instances:
        os_value = inst.get("os", "unknown").strip().split()[0].lower()
        os_counter[os_value] += 1
    
    health_counter = Counter()
    for inst in instances:
        health_value = str(inst.get("health", "UNKNOWN")).upper()
        health_counter[health_value] += 1

    rts = [inst.get("response_time_ms") for inst in instances if isinstance(inst.get("response_time_ms"), (int, float))]
    cpus = [inst.get("cpu_percent") for inst in instances if isinstance(inst.get("cpu_percent"), (int, float))]
    mems = [inst.get("memory_percent") for inst in instances if isinstance(inst.get("memory_percent"), (int, float))]

    avg_rt = sum(rts) / len(rts) if rts else 0
    avg_cpu = sum(cpus) / len(cpus) if cpus else 0
    avg_mem = sum(mems) / len(mems) if mems else 0

    print("\n📊 VM Summary:")
    print(f"- Total machines: {total}")
    print(f"- Machines UP  : {up}")
    print(f"- Machines DOWN: {down}\n")
    time.sleep(1)
    print("-----------------------------")
    time.sleep(0.5)
    print("🖥️  By OS:")
    for os_name, count in os_counter.items():
        print(f"• {os_name.capitalize()}: {count}")
    time.sleep(1)
    print("-----------------------------")
    time.sleep(0.5)
    print("\n❤️  Health status:")
    for health_value, count in health_counter.items():
        print(f"• {health_value}: {count}")
    time.sleep(1)
    print("-----------------------------")
    time.sleep(0.5)
    print("\n📈 Performance (averages):")
    print(f"- Avg response time: {avg_rt:.1f} ms")
    print(f"- Avg CPU usage    : {avg_cpu:.1f} %")
    print(f"- Avg memory usage : {avg_mem:.1f} %")
    time.sleep(1.5)
    print("\n")
    
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
        # Option 3: Return to main manu after finishing validation
        elif choice == '3':
            instances = load_instances()
            validate_all_instances(instances)
            input("\nValidation complete, press Enter to return to menu...")
       # Option 4: Asking the user if he wants to add more VMs - if not, he will return to main manu
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
                     continue  # User chose not to continue → return to main menu
                 if result == "added":
                     again = input("Would you like to add another machine? (y/n): ").strip().lower()
                     if again != 'y':
                         print("🔄 Returning to main menu...\n")
                         time.sleep(1)
                         adding = False
       
        elif choice == '5':
            display_all_instances()
            input("\nDisplay complete, press Enter to return to menu...")
        
        elif choice == '6':
            display_statistics()
            input("\nDisplay complete, press Enter to return to menu...")
        
        elif choice == '7':
             edit_existing_machine()
             input("\nEdit complete, press Enter to return to menu...")
        
        elif choice == '8':
             remove_machine()
             input("\nDeletion complete, press Enter to return to menu...")

        else:
            print("❗ Invalid choice. Please enter an option between 1-8.\n")
            time.sleep(1)

            # Entry point
if __name__ == "__main__":
     main()