import json
import os
import time
from machine_model import VMInstance

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

# Validate all VM dictionaries against the VMInstance model
def validate_all_instances(instances):
    print("\n🔍 Validating all VM instances from JSON...\n")
    time.sleep(1)

    for idx, data in enumerate(instances, 1):
        try:
            # Simulate processing delay
            print(f"⏳ Validating VM #{idx}...")
            time.sleep(1.2)

            # Attempt to create a VMInstance object from the dictionary
            vm = VMInstance(**data)
            print(f"✅ VM #{idx} ('{vm.name}') is valid.\n")
        except Exception as e:
            print(f"❌ VM #{idx} failed validation:")
            print(f"   Error: {e}\n")
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
    except Exception:
        print("Invalid machine configuration.\n")
        return "cancel"

    # Step 2: Check for duplicate name
    instances = load_instances()
    if any(inst.get("name") == name for inst in instances):
        print(f"Error: Machine with name '{name}' already exists. Please choose a unique name.\n")
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
        return "cancel"

    # Step 4: Save to file
    instances.append(data)
    full_data = {"instances": instances}
    path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'instances.json')

    try:
        with open(path, 'w') as file:
            json.dump(full_data, file, indent=4)
        time.sleep(1.5)
        print("Machine saved successfully!\n")
        return "added"
    except Exception as e:
        print(f"Error: Failed to save machine: {e}\n")
        return "cancel"
    
# Main function that runs the monitoring tool
def main():
    while True:
        print_intro()
        choice = input("Choose an option (1, 2, 3 or 4): ").strip()

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
                else:
                    print(f"❌ Machine '{machine_name}' does not exist.\n")

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
            input("\nPress Enter to return to menu...")
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

        else:
            print("❗ Invalid choice. Please enter 1, 2, 3 or 4.\n")
            time.sleep(1)

            # Entry point
if __name__ == "__main__":
     main()