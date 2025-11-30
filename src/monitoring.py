import time
import random
from collections import Counter
from logger import logger
from machine_model import VMInstance
from storage import load_instances

# Simulated failure rate for health checks (10% of the checks will be forced to fail)
FAILURE_RATE = 0.1


def monitor_vm(vm: VMInstance):
    """
    Simulate a health check for a single VM.
    Returns a dict with health, response time and resource usage.
    Does NOT write anything back to JSON, this is per-run only.
    """
    print(f"🧪 Running health check for '{vm.name}'...")
    time.sleep(0.5)

    # Simulate metrics for this VM
    response_time_ms = random.randint(20, 300)
    cpu_percent = random.randint(5, 95)
    memory_percent = random.randint(5, 95)

    # Decide health based on simulated failure and thresholds
    if random.random() < FAILURE_RATE:
        health = "CRIT"
        reason = "Simulated failure"
    elif response_time_ms > 220 or cpu_percent > 85 or memory_percent > 90:
        health = "WARN"
        reason = "High latency or resource usage"
    else:
        health = "OK"
        reason = "Healthy"

    method = vm.check

    # Show what kind of check we are simulating
    if method == "ping":
        print(f"   [SIM] PING {vm.ip} ... {health}")
    elif method == "http":
        target = getattr(vm, "url", "(no URL)")
        print(f"   [SIM] HTTP GET {target} ... {health}")
    else:
        print(f"   [SIM] UNKNOWN METHOD '{method}' ... {health}")

    print(f"   Reason: {reason}")
    print(f"   RT={response_time_ms} ms | CPU={cpu_percent}% | MEM={memory_percent}%\n")

    # Return all simulated data so the caller can aggregate it
    return {
        "name": vm.name,
        "status": vm.status,
        "health": health,
        "method": method,
        "response_time_ms": response_time_ms,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
    }


def validate_all_instances(instances):
    """
    Validate all VM dictionaries using VMInstance.
    For each valid VM, run monitor_vm and collect the result.
    One bad VM or one monitoring error does NOT stop the whole loop.
    At the end, only report machines that did NOT pass the health check.
    """
    logger.info("🔍 Started validating all VM instances from JSON.")
    print("\n🔍 Validating machine configurations...")
    time.sleep(1.0)

    results = []

    for idx, data in enumerate(instances, 1):
        try:
            print(f"⏳ Validating VM #{idx}...")
            time.sleep(0.6)
            vm = VMInstance(**data)
            logger.info(f"Machine '{vm.name}' is valid")
        except Exception as e:
            print(f"❌ VM #{idx} failed validation:")
            print(f"   Error: {e}\n")
            logger.error(f"Machine #{idx} is invalid: {e}")
            time.sleep(0.4)
            continue

        try:
            result = monitor_vm(vm)
            results.append(result)
        except Exception as e:
            print(f"❌ Monitoring failed for VM #{idx} ('{vm.name}'):")
            print(f"   Error: {e}\n")
            logger.error(f"Monitoring failed for machine '{vm.name}': {e}")
            time.sleep(0.4)
            continue

    print("✔️  Validation process completed.\n")

    if not results:
        print("⚠️  No VMs were successfully validated.\n")
        logger.warning("Run finished with no successfully validated VMs")
        return

    failing = [r for r in results if r["health"] != "OK"]

    if failing:
        print("⚠️  The following machines did NOT pass the health check:")
        for r in failing:
            print(f"   - {r['name']} (status={r['status']}, health={r['health']})")
        print()
        logger.info(
            f"Health failures in run: {[r['name'] for r in failing]}"
        )
    else:
        print("✅  All machines passed the health check for this run.\n")
        logger.info("All machines passed health check in this run")


def display_statistics():
    """
    Display long-term statistics based on the data stored in JSON.
    This uses whatever is currently in the config file and does NOT depend
    on the last validate_all_instances() run.
    """
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
    rts = [
        inst.get("response_time_ms")
        for inst in instances
        if isinstance(inst.get("response_time_ms"), (int, float))
    ]
    cpus = [
        inst.get("cpu_percent")
        for inst in instances
        if isinstance(inst.get("cpu_percent"), (int, float))
    ]
    mems = [
        inst.get("memory_percent")
        for inst in instances
        if isinstance(inst.get("memory_percent"), (int, float))
    ]

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
