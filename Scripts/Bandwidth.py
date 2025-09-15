import paramiko

def RunSSHCmd(host, user, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    ssh.close()
    return output

def GetIntIP(RemoteIP, host, user, password):
    # Command to list interfaces and their IPs
    cmd = "ip -o -4 addr show | awk '{print $2, $4}'"
    output = RunSSHCmd(host, user, password, cmd)
    for line in output.splitlines():
        iface, ip_cidr = line.split()
        ip = ip_cidr.split('/')[0]
        if ip == RemoteIP:
            return iface
    return None

def GetIntSpeed(Interface, host, user, password):
    cmd = f"ethtool {Interface}"
    output = RunSSHCmd(host, user, password, cmd)
    for line in output.splitlines():
        if "Speed:" in line:
            speed_str = line.split(":")[1].strip()
            if speed_str.endswith("Mb/s"):
                return int(speed_str.replace("Mb/s", ""))
    return None

def run(IP):
    host = IP
    user = "asda"
    password = "asda"

    iface = GetIntIP(IP, host, user, password)
    if iface:
        speed = GetIntSpeed(iface, host, user, password)
        if speed:
            print(f"Interface '{iface}' with IP {IP} has speed {speed} Mb/s")
        else:
            print(f"Could not determine speed for interface '{iface}'")
    else:
        print(f"No interface found with IP {IP}")

    return speed
