import paramiko
import re

SSH_USER = "asda"
SSH_PASSWORD = "asda"  # or use key-based auth if preferred

def RunSSHCmd(host, user, password, command):
    """Run SSH command using Paramiko and return stdout as string."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # auto-accept unknown host keys
    ssh.connect(hostname=host, username=user, password=password, look_for_keys=False, allow_agent=False)
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    ssh.close()
    return output

def Ping(host, remote, count):
    try:
        cmd = f"ping -c {count} {remote}"
        output = RunSSHCmd(host, SSH_USER, SSH_PASSWORD, cmd)

        # Extract average latency (Linux/macOS ping)
        match = re.search(r"= [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms", output)
        if match:
            avg_latency = match.group(1)
            print(f"Average latency to {remote} from {host}: {avg_latency} ms", flush=True)
            return float(avg_latency)
        else:
            print(f"Could not parse ping output from {host}:\n{output}", flush=True)
            return None
    except Exception as e:
        print(f"Ping failed from {host} to {remote}: {e}", flush=True)
        return None

def run(host, remote):
    latency = Ping(host, remote, count=3)
    return latency
