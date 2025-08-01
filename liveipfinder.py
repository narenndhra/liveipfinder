# enterprise_ip_scanner.py
# Final script for PingPortRecon
# See README.md for usage instructions

import subprocess
import platform
import ipaddress
import concurrent.futures
import csv
import time
from tqdm import tqdm
import socket
import re
import argparse

LIVE_ONLY_CSV = "live_ips.csv"

PORTS = [
    21,22,25,80,110,143,443,465,587,993,995,
    8080,8443,9443,10443,2222,4353,4433,
    500,1701,4500,1194,1494,2598,17777,17778,
    161,162
]

def ping_host(ip, timeout):
    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), str(ip)]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), str(ip)]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False

def check_ports(ip, timeout):
    open_ports = []
    for port in PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            if sock.connect_ex((str(ip), port)) == 0:
                open_ports.append(port)
            sock.close()
        except Exception:
            continue
    return open_ports

def expand_input_file(file_path):
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

def scan_dead_ip(ip, timeout, delay):
    time.sleep(delay)
    open_ports = check_ports(ip, timeout)
    if open_ports:
        return (ip, "Dead", "Open", ",".join(map(str, open_ports)))
    return None

def main():
    parser = argparse.ArgumentParser(description="PingPortRecon: Enterprise IP Scanner")
    parser.add_argument("input_file", help="File with IPs and/or subnets")
    parser.add_argument("--threads", type=int, default=50, help="Number of threads (default: 50)")
    parser.add_argument("--timeout", type=int, default=2, help="Timeout per ping/port check (seconds)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between scans (seconds)")
    args = parser.parse_args()

    ip_list = expand_input_file(args.input_file)
    if not ip_list:
        print("[!] No valid IPs or subnets found in input file.")
        return

    print(f"\n[+] Total targets: {len(ip_list)}")
    print(f"[+] Threads: {args.threads} | Timeout: {args.timeout}s | Ports: {len(PORTS)} ports\n")

    print("[+] Phase 1: Pinging targets...")
    alive_ips = []
    dead_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=len(ip_list), desc="Pinging", ncols=100) as pbar:
            future_to_ip = {executor.submit(ping_host, ip, args.timeout): ip for ip in ip_list}
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                if future.result():
                    alive_ips.append(ip)
                else:
                    dead_ips.append(ip)
                pbar.update(1)

    print(f"\n[+] Ping complete! Alive (Ping): {len(alive_ips)} | Dead: {len(dead_ips)}")

    print(f"\n[+] Phase 2: Scanning ports on dead IPs ({len(dead_ips)})...")
    live_ips_details = [(ip, "Alive", "Skipped", "-") for ip in alive_ips]

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=len(dead_ips), desc="Port Scan", ncols=100) as pbar:
            futures = [executor.submit(scan_dead_ip, ip, args.timeout, args.delay) for ip in dead_ips]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    live_ips_details.append(result)
                pbar.update(1)

    alive_from_ping = len(alive_ips)
    alive_from_ports = len(live_ips_details) - alive_from_ping
    total_live = len(live_ips_details)

    print(f"\n[+] Scan complete!")
    print(f"Alive from Ping: {alive_from_ping}")
    print(f"Alive from Ports: {alive_from_ports}")
    print(f"Total Live Hosts: {total_live}\n")

    print("IP, Ping_Status, Port_Status, Open_Ports")
    for ip, ping_status, port_status, open_ports in live_ips_details:
        print(f"{ip}, {ping_status}, {port_status}, {open_ports}")

    if live_ips_details:
        with open(LIVE_ONLY_CSV, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["IP", "Ping_Status", "Port_Status", "Open_Ports"])
            writer.writerows(live_ips_details)

    print(f"\n[✔] Live IP details saved to {LIVE_ONLY_CSV}")

if __name__ == "__main__":
    main()
