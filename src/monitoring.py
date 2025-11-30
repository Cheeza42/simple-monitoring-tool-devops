import time
from collections import Counter
from logger import logger
from machine_model import VMInstance
from storage import load_instances

# Simulates a basic health check for a single VM
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

    # Count OS usage
    os_counter = Counter()
    for inst in instances:
        os_value = inst.get("os", "unknown").strip().split()[0].lower()
        os_counter[os_value] += 1
    
    # Count health status distribution
    health_counter = Counter()
    for inst in instances:
        health_value = str(inst.get("health", "UNKNOWN")).upper()
        health_counter[health_value] += 1

    # Collect numeric metrics for averages
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
