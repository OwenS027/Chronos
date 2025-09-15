import paramiko
import sys
import time
import traceback
from kubernetes import client, config

SSH_USER = "asda"
SSH_PASSWORD = "asda"  # or use key auth if preferred

# Kubernetes client
try:
    config.load_incluster_config()
except:
    config.load_kube_config()
v1 = client.CoreV1Api()


def GetPodInfo(namespace, PodLabel):
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={PodLabel}")
    running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]

    if not running_pods:
        print(f"❌ No running pods found with label app={PodLabel} in {namespace}")
        sys.exit(1)

    pod = running_pods[0]
    return pod.status.pod_ip, pod.spec.node_name


def GetNodeIP(node_name):
    node = v1.read_node(name=node_name)
    for addr in node.status.addresses:
        if addr.type == "InternalIP":
            return addr.address
    print(f"❌ Could not find InternalIP for node {node_name}")
    sys.exit(1)


def ResolveIP(ip):
    pods = v1.list_pod_for_all_namespaces(watch=False)
    for pod in pods.items:
        if pod.status.pod_ip == ip:
            return f"{pod.metadata.namespace}/{pod.metadata.name}/{ip}", "Pod"
    return ip, "IP"


def StripPort(ip_port):
    if ":" in ip_port:
        return ip_port.split(":")[0]
    return ip_port

def RunSSHCmd(host, user, password, command, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, look_for_keys=False, allow_agent=False)

    # Start command
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

    StartTime = time.time()
    try:
        while True:
            # Check if timeout reached
            if time.time() - StartTime > timeout:
                break

            # Read line if available
            if stdout.channel.recv_ready():
                line = stdout.readline()
                if line:
                    yield line.strip()
            else:
                time.sleep(0.1)  # prevent busy-wait
    finally:
        ssh.close()


def Monitor(Namespace, PodName, PodLabel):
    PodIP, NodeName = GetPodInfo(Namespace, PodLabel)
    NodeIP = GetNodeIP(NodeName)

    print(f"📡 Monitoring traffic for Pod {PodLabel} "
          f"(IP: {PodIP}, Node: {NodeName} @ {NodeIP})")

    UniquePods = set()
    StartTime = time.time()

    # Run tcpdump over SSH via Paramiko
    TCPCmd = f"sudo tcpdump -i any -n host {PodIP}"
    try:
        while time.time() - StartTime < 30:
            for line in RunSSHCmd(NodeIP, SSH_USER, SSH_PASSWORD, TCPCmd):

                if ">" not in line or "IP" not in line:
                    continue

                parts = line.split()
                try:
                    idx = parts.index("IP")
                    src = StripPort(parts[idx + 1])
                    dst = StripPort(parts[idx + 3].rstrip(":"))
                except Exception:
                    continue

                PeerIP = dst if src == PodIP else src
                PeerName, type = ResolveIP(PeerIP)
                if type == "Pod":
                    UniquePods.add(PeerName)

                print(f"➡️ {PodName} ({PodIP}) is talking to {PeerName}", flush=True)
            time.sleep(1)
    except Exception as e:
        return e
    finally:
        print("📋 Unique pods seen in 15s:")
        for p in sorted(UniquePods):
            print("   -", p)
    return UniquePods


def run(Namespace, PodName, PodLabel):
    results = Monitor(Namespace, PodName, PodLabel)
    return results
