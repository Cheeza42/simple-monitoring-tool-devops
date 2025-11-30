import time
import random
import subprocess
import platform
from collections import Counter
import requests
from logger import logger
from machine_model import VMInstance
from storage import load_instances

def run_ping(ip, timeout=1):
    """
    Run a single ping to the given IP.
    Returns (success: bool, elapsed_ms: int).
    """
    system = platform.system().lower()

    # Use OS-specific flags for ping
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), ip]

    start = time.time()
    completed = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    elapsed_ms = int((time.time() - start) * 1000)
    success = completed.returncode == 0

    return success, elapsed_ms


def run_http(url, timeout=2):
    """
    Send an HTTP GET request to the given URL.
    Returns (success: bool, status_code: Optional[int], elapsed_ms: int).
    """
    start = time.time()

    try:
        response = requests.get(url, timeout=timeout)
        elapsed_ms = int((time.time() - start) * 1000)
        return True, response.status_code, elapsed_ms
    except requests.RequestException:
        elapsed_ms = int((time.time() - start) * 1000)
        return False, None, elapsed_ms


def monitor_vm(vm: VMInstance):
    """
    Runs health check for a single VM.

    Steps:
    1. Read CPU and memory metrics from the VM instance (assumed to come from an external source).
    2. For 'ping': run a real ICMP ping and decide health based on success + latency.
    3. For 'http': send a real HTTP request and decide health based on status code + latency.
    4. For unsupported methods: mark as WARN without any simulated checks.
    5. Print a human-readable summary and return a dict with all metrics.
    """
    print(f"🧪 Running health check for '{vm.name}'...")
    time.sleep(0.5)

    # CPU and memory metrics are not simulated here.
    # They are used only if provided on the VMInstance (from an external monitoring source).
    cpu_percent = getattr(vm, "cpu_percent", None)
    memory_percent = getattr(vm, "memory_percent", None)

    response_time_ms = None
    health = "OK"
    reason = "Healthy"
    method = vm.check

    # Network check based on method type
    if method == "ping":
        # Real ICMP ping to the configured IP
        success, rt = run_ping(vm.ip)
        response_time_ms = rt

        if not success:
            health = "CRIT"
            reason = "Ping failed"
        elif rt > 250:
            health = "WARN"
            reason = "High latency"

    elif method == "http":
        # Real HTTP GET to the configured URL
        url = getattr(vm, "url", None)

        if not url:
            # Configuration error: HTTP check without URL
            health = "CRIT"
            reason = "Missing URL for HTTP check"
            response_time_ms = 0
        else:
            success, status_code, rt = run_http(url)
            response_time_ms = rt

            if not success:
                health = "CRIT"
                reason = "HTTP request failed"
            elif status_code >= 500:
                health = "CRIT"
                reason = f"HTTP {status_code}"
            elif status_code >= 400 or rt > 400:
                # Client error or slow response → treat as WARN
                health = "WARN"
                reason = f"HTTP {status_code} or slow response"

    else:
        # In the real mode, only 'ping' and 'http' are fully supported.
        # Any other method is marked as WARN without running a simulated check.
        health = "WARN"
        reason = "Unsupported check method"
        response_time_ms = None

    # Prepare display values for CPU/MEM (external-only metrics)
    cpu_display = f"{cpu_percent}%" if isinstance(cpu_percent, (int, float)) else "N/A"
    mem_display = f"{memory_percent}%" if isinstance(memory_percent, (int, float)) else "N/A"

    # Human-readable output for the current VM
    if method == "ping":
        print(f"   [REAL] PING {vm.ip} ... {health}")
    elif method == "http":
        target = getattr(vm, "url", "(no URL)")
        print(f"   [REAL] HTTP GET {target} ... {health}")
    else:
        print(f"   [NO-CHECK] METHOD '{method}' ... {health}")

    print(f"   Reason: {reason}")
    print(f"   RT={response_time_ms} ms | CPU={cpu_display} | MEM={mem_display}\n")

    # Structured result for aggregation in validate_all_instances()
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
