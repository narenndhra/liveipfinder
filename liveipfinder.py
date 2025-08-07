#!/usr/bin/env python3

import subprocess
import platform
import ipaddress
import concurrent.futures
import socket
import csv
import re
import time
import argparse
from tqdm import tqdm

# Constants
LIVE_ONLY_CSV = "live_ips.csv"

DEFAULT_PORTS = [
    21, 22, 25, 80, 110, 143, 443, 465, 587, 993, 995,
    8080, 8443, 9443, 10443, 2222, 4353, 4433,
    500, 1701, 4500, 1194, 1494, 2598, 17777, 17778,
    161, 162
]

# --- Utility Functions ---

def expand_input_file(file_path):
    """Expands IPs and CIDR ranges from a given file into a list of IP addresses."""
    all_ips = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "/" in line:
                try:
                    all_ips.extend([str(ip) for ip in ipaddress.IPv4Network(line, strict=False)])
                except ValueError:
                    continue
            elif re.match(r"^\d{1,3}(\.\d{1,3}){3}$", line):
                all_ips.append(line)
    return list(set(all_ips))


def ping_host(ip, timeout):
    """Returns True if host responds to ping, False otherwise."""
    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


def check_ports(ip, ports, timeout):
    """Checks a list of ports on a given IP. Returns list of open ports."""
    open_ports = []
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
        except Exception:
            continue
    return open_ports


def scan_dead_ip(ip, timeout, delay, ports):
    """Scans ports on an IP marked as 'dead' from ping. Returns result if ports are open."""
    time.sleep(delay)
    open_ports = check_ports(ip, ports, timeout)
    if open_ports:
        return (ip, "Dead", "Open", ",".join(map(str, open_ports)))
    return None


def write_csv(results, filename=LIVE_ONLY_CSV):
    """Writes scan results to CSV."""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "Ping_Status", "Port_Status", "Open_Ports"])
        writer.writerows(results)


# --- Main Function ---

def main():
    parser = argparse.ArgumentParser(description="PingPortRecon: Enterprise IP Scanner")
    parser.add_argument("input_file", help="File with IPs and/or subnets (CIDRs supported)")
    parser.add_argument("--threads", type=int, default=50, help="Max number of threads (default: 50)")
    parser.add_argument("--timeout", type=int, default=2, help="Ping/Port check timeout in seconds (default: 2)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between scans (default: 0)")
    parser.add_argument("--mode", choices=["ping", "full"], default="full",
                        help="Scan mode: 'ping' for ping-only, 'full' for ping + port scan (default: full)")
    parser.add_argument("--ports", help="Comma-separated list of ports to scan in full mode",
                        default=",".join(map(str, DEFAULT_PORTS)))

    args = parser.parse_args()

    # Parse port list
    try:
        port_list = sorted(set(int(p.strip()) for p in args.ports.split(",") if p.strip().isdigit()))
    except ValueError:
        print("[!] Invalid port list. Use comma-separated integers.")
        return

    ip_list = expand_input_file(args.input_file)
    if not ip_list:
        print("[!] No valid IPs or subnets found.")
        return

    print(f"\n[+] Total Targets: {len(ip_list)}")
    print(f"[+] Threads: {args.threads} | Timeout: {args.timeout}s | Mode: {args.mode} | Ports: {len(port_list)}\n")

    # Phase 1: Ping sweep
    print("[+] Phase 1: Pinging targets...")
    alive_ips = []
    dead_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=len(ip_list), desc="Pinging", ncols=100) as pbar:
            future_to_ip = {executor.submit(ping_host, ip, args.timeout): ip for ip in ip_list}
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        alive_ips.append(ip)
                    else:
                        dead_ips.append(ip)
                except Exception:
                    dead_ips.append(ip)
                pbar.update(1)

    print(f"\n[+] Ping Summary: Alive = {len(alive_ips)}, Dead = {len(dead_ips)}")

    # Results store
    results = [(ip, "Alive", "Skipped", "-") for ip in alive_ips]

    # Phase 2: Optional port scan on dead hosts
    if args.mode == "full" and dead_ips:
        print(f"\n[+] Phase 2: Scanning ports on dead IPs ({len(dead_ips)})...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            with tqdm(total=len(dead_ips), desc="Port Scan", ncols=100) as pbar:
                futures = [executor.submit(scan_dead_ip, ip, args.timeout, args.delay, port_list) for ip in dead_ips]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
                    pbar.update(1)

    total_live = len(results)
    from_ping = len(alive_ips)
    from_ports = total_live - from_ping

    # Final Summary
    print(f"\n[+] Scan Complete!")
    print(f"    Alive from Ping:   {from_ping}")
    print(f"    Alive from Ports:  {from_ports}")
    print(f"    Total Live Hosts:  {total_live}\n")

    print("IP, Ping_Status, Port_Status, Open_Ports")
    for row in results:
        print(",".join(row))

    write_csv(results)
    print(f"\n[✔] Results saved to {LIVE_ONLY_CSV}")


if __name__ == "__main__":
    main()
