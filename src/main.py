import json
import os
import shutil
import time
from collections import Counter
from logger import logger
from machine_model import VMInstance

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
        except Exception as e:
            print(f"❌ VM #{idx} failed validation:")
            print(f"   Error: {e}\n")
            logger.error(f"Machine #{vm.name} is invalid: {e}")
        time.sleep(0.8)  # Slight pause between VMs

    print("✔️ Validation process completed.")

def add_new_machine():
    print("\n🆕 Add a New Machine")
    print("--------------------")

    name = input("Enter machine name: ").strip()
    ip = input("Enter IP address: ").strip()
    os_name = input("Enter operating system: ").strip()
    status = input("Enter status (UP/DOWN): ").strip().upper()

    data = {
        "name": name,
        "ip": ip,
        "os": os_name,
        "status": status
    }
   
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
        logger.warning(f"Machine '{name}' does not exist")
        return "added"
    
    except Exception as e:
        print(f"Error: Failed to save machine: {e}\n")
        return "cancel"

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

        for i, inst in enumerate(instances, 1):
            print(f"\nMachine #{i}")
            print(f"Name   : {inst.get('name')}")
            print(f"IP     : {inst.get('ip')}")
            print(f"OS     : {inst.get('os')}")
            print(f"Status : {inst.get('status')}")
            print("------------------------------")
            time.sleep(1.8)
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

    print("\n📊 VM Summary:")
    print(f"- Total machines: {total}")
    print(f"- Machines UP  : {up}")
    print(f"- Machines DOWN: {down}\n")
    time.sleep(1)
    print("-----------------------------")
    time.sleep(0.8)
    print("🖥️ By OS:")
    for os_name, count in os_counter.items():
        print(f"• {os_name.capitalize()}: {count}")
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
        choice = input("Choose an option (1, 2, 3, 4, 5, 6, 7 or 8): ").strip()

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
                        break  # User chose not to continue → return to main menu
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
            print("❗ Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7 or 8.\n")
            time.sleep(1)

            # Entry point
if __name__ == "__main__":
     main()