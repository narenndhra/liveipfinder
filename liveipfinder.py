#!/usr/bin/env python3
"""
Live-IP Finder: ICMP discovery with optional TCP/UDP dead-host rescue.

- Phase 1 (always): ICMP ping to find alive hosts quickly.
- Phase 2 (optional): For *ICMP-dead* hosts only, try TCP and/or UDP probes to
  "rescue" hosts that block ICMP but have reachable services.

Console output: CSV header + rows
CSV file: live_ips.csv with columns: IP, Ping_Status, Rescue_Source, Open_Details
"""

import argparse
import concurrent.futures
import csv
import ipaddress
import os
import platform
import random
import re
import socket
import subprocess
import time

from tqdm import tqdm

# =========================================================
# Defaults / Config
# =========================================================
LIVE_ONLY_CSV = "live_ips.csv"

BEST_DEFAULT_PROBE_TCP = "22,80,443,3389"
BEST_DEFAULT_PROBE_UDP = "53,123,161,500"

DEFAULT_THREADS = 80
DEFAULT_TIMEOUT = 2.0
DEFAULT_DELAY = 0.0

# UDP timing defaults
DEFAULT_UDP_RETRIES = 2
DEFAULT_UDP_SEND_DELAY = 0.05   # seconds between sends
DEFAULT_UDP_WAIT = 0.30         # seconds receive window after send
DEFAULT_UDP_JITTER = 0.02       # +/- jitter


# =========================================================
# Utilities
# =========================================================
def parse_port_spec(spec):
    """
    Parse '22,80,443,1000-1005' (commas/semicolon/space separated) into a sorted unique list of ints.
    Ignores invalid tokens and out-of-range ports.
    """
    ports = set()
    if not spec:
        return []
    for token in re.split(r"[,\s;]+", spec.strip()):
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            if a.isdigit() and b.isdigit():
                lo, hi = int(a), int(b)
                if 1 <= lo <= 65535 and 1 <= hi <= 65535 and lo <= hi:
                    ports.update(range(lo, hi + 1))
        elif token.isdigit():
            p = int(token)
            if 1 <= p <= 65535:
                ports.add(p)
    return sorted(ports)


def expand_input_file(file_path):
    """
    Expands IPs and CIDR ranges from a given file into a de-duplicated list of IP addresses (strings).
    Accepts plain IPv4 addresses and CIDRs (no dash-ranges/hostnames).
    """
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
    # De-duplicate
    return list(set(all_ips))


# =========================================================
# Discovery (ICMP)
# =========================================================
def ping_host(ip, timeout):
    """ICMP ping; returns True if host responds."""
    try:
        system = platform.system().lower()
        if system == "windows":
            # -n 1 (one echo), -w timeout_ms
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
        else:
            # -c 1 (one echo), -W timeout_sec
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


# =========================================================
# Dead-host rescue: TCP
# =========================================================
def tcp_rescue_ports(ip, ports, timeout):
    """Try TCP connect on each port; return list of ports that connected."""
    hits = []
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((ip, port)) == 0:
                    hits.append(port)
        except Exception:
            pass
    return hits


# =========================================================
# Dead-host rescue: UDP (timed, with minimal payloads)
# =========================================================
def _udp_payload_for(port):
    """
    Minimal protocol-aware probes to coax replies.
    """
    if port == 53:   # DNS: query A record for "example.com"
        return (b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
                b'\x07example\x03com\x00\x00\x01\x00\x01')
    if port == 123:  # NTP: client request (mode 3)
        pkt = bytearray(48)
        pkt[0] = 0x1b  # LI=0, VN=3, Mode=3 (client)
        return bytes(pkt)
    if port == 161:  # SNMP v1 GET for 1.3.6.1.2.1.1.1.0 (community "public")
        return bytes.fromhex(
            "30 26 02 01 00 04 06 70 75 62 6C 69 63 A0 19 02 04 00 00 00 01"
            "02 01 00 02 01 00 30 0B 30 09 06 05 2B 06 01 02 01 05 00"
            .replace(" ", "")
        )
    if port == 500:  # IKEv2 very small initiator blob (not spec-accurate, but often triggers response)
        return os.urandom(28)
    return b"\x00"   # default minimal datagram


def udp_rescue_ports_timed(ip, ports, per_port_timeout, retries=2, inter_send_delay=0.05,
                           wait_after_send=0.30, jitter=0.02):
    """
    Probe UDP ports with timing discipline:
      - For each port, send up to `retries` probes.
      - After each send, wait up to `wait_after_send` to receive a reply.
      - Add small delay between sends (with jitter) to avoid bursting patterns.
      - `per_port_timeout` acts as an upper bound socket timeout.

    Returns list of ports that actually produced a UDP reply from `ip`.
    """
    responsive = []
    if not ports:
        return responsive

    for port in ports:
        got_reply = False
        payload = _udp_payload_for(port)

        for _ in range(max(1, int(retries))):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(per_port_timeout)

                    # Send the probe
                    s.sendto(payload, (ip, port))

                    # Pace a bit between sends
                    if inter_send_delay > 0:
                        time.sleep(max(0.0, inter_send_delay + random.uniform(-jitter, jitter)))

                    # Short receive window to catch replies
                    end_by = time.time() + max(0.0, wait_after_send)
                    while time.time() < end_by:
                        try:
                            data, addr = s.recvfrom(2048)
                            if addr and addr[0] == ip:
                                got_reply = True
                                break
                        except socket.timeout:
                            # keep waiting in this small window
                            pass

                if got_reply:
                    responsive.append(port)
                    break  # stop retrying this port once responsive

            except Exception:
                # swallow UDP socket errors; many targets are silent or filtered
                pass

        # Optional politeness delay between ports:
        # time.sleep(0.01)

    return responsive


# =========================================================
# CSV
# =========================================================
def write_csv(rows, filename=LIVE_ONLY_CSV):
    """Writes results to CSV with correct quoting."""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "Ping_Status", "Rescue_Source", "Open_Details"])
        writer.writerows(rows)


# =========================================================
# Main
# =========================================================
def main():
    parser = argparse.ArgumentParser(
        description="Live-IP Finder: ICMP discovery with optional TCP/UDP dead-host rescue"
    )
    parser.add_argument("input_file", help="File with IPs and/or subnets (CIDRs supported)")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS,
                        help=f"Max number of threads (default: {DEFAULT_THREADS})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Timeout in seconds for ICMP/TCP/UDP operations (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help=f"Delay between discovery and rescue (default: {DEFAULT_DELAY})")

    # Dead-host rescue probes (ranges supported). If empty => skip that protocol.
    parser.add_argument("--probe-tcp", default=BEST_DEFAULT_PROBE_TCP,
                        help=f"TCP ports used ONLY for dead-host rescue (supports ranges). Default: '{BEST_DEFAULT_PROBE_TCP}'")
    parser.add_argument("--probe-udp", default=BEST_DEFAULT_PROBE_UDP,
                        help=f"UDP ports used ONLY for dead-host rescue (supports ranges). Default: '{BEST_DEFAULT_PROBE_UDP}'")

    # UDP timing knobs
    parser.add_argument("--udp-retries", type=int, default=DEFAULT_UDP_RETRIES,
                        help=f"UDP retries per port (default: {DEFAULT_UDP_RETRIES})")
    parser.add_argument("--udp-send-delay", type=float, default=DEFAULT_UDP_SEND_DELAY,
                        help=f"Delay between UDP sends per port in seconds (default: {DEFAULT_UDP_SEND_DELAY})")
    parser.add_argument("--udp-wait", type=float, default=DEFAULT_UDP_WAIT,
                        help=f"Receive window after each UDP send in seconds (default: {DEFAULT_UDP_WAIT})")
    parser.add_argument("--udp-jitter", type=float, default=DEFAULT_UDP_JITTER,
                        help=f"+/- jitter added to UDP send delay (default: {DEFAULT_UDP_JITTER})")

    args = parser.parse_args()

    probe_tcp_ports = parse_port_spec(args.probe_tcp)
    probe_udp_ports = parse_port_spec(args.probe_udp)

    ip_list = expand_input_file(args.input_file)
    if not ip_list:
        print("[!] No valid IPs or subnets found.")
        return

    print(f"\n[+] Total Targets: {len(ip_list)}")
    print(f"[+] Threads: {args.threads} | Timeout: {args.timeout:.2f}s | Delay: {args.delay:.2f}s\n")

    # ---------------- Phase 1: ICMP discovery ----------------
    print("[+] Phase 1: ICMP discovery...")
    alive_icmp = []
    dead_icmp = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=len(ip_list), desc="ICMP", ncols=100) as pbar:
            future_to_ip = {executor.submit(ping_host, ip, args.timeout): ip for ip in ip_list}
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        alive_icmp.append(ip)
                    else:
                        dead_icmp.append(ip)
                except Exception:
                    dead_icmp.append(ip)
                pbar.update(1)

    print(f"\n[+] Discovery Summary: Alive(ICMP) = {len(alive_icmp)}, Dead(ICMP) = {len(dead_icmp)}")

    # Build results for alive (ICMP)
    results = [(ip, "Alive", "ICMP", "ICMP") for ip in sorted(alive_icmp)]

    # ---------------- Phase 2: Dead-host rescue (optional) ----------------
    do_tcp = len(probe_tcp_ports) > 0
    do_udp = len(probe_udp_ports) > 0

    if dead_icmp and (do_tcp or do_udp):
        print(f"\n[+] Phase 2: Dead-host rescue on {len(dead_icmp)} targets "
              f"(TCP: {len(probe_tcp_ports)} ports | UDP: {len(probe_udp_ports)} ports)")
        if args.delay > 0:
            time.sleep(args.delay)

        def rescue_one(ip):
            tcp_hits = tcp_rescue_ports(ip, probe_tcp_ports, args.timeout) if do_tcp else []
            udp_hits = udp_rescue_ports_timed(
                ip,
                probe_udp_ports,
                per_port_timeout=args.timeout,
                retries=args.udp_retries,
                inter_send_delay=args.udp_send_delay,
                wait_after_send=args.udp_wait,
                jitter=args.udp_jitter,
            ) if do_udp else []

            if tcp_hits or udp_hits:
                if tcp_hits and udp_hits:
                    parts = []
                    if tcp_hits:
                        parts.append("TCP:" + ",".join(map(str, tcp_hits)))
                    if udp_hits:
                        parts.append("UDP:" + ",".join(map(str, udp_hits)))
                    return (ip, "Dead", "TCP+UDP", " | ".join(parts))
                elif tcp_hits:
                    return (ip, "Dead", "TCP", ",".join(map(str, tcp_hits)))
                else:
                    return (ip, "Dead", "UDP", ",".join(map(str, udp_hits)))
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            with tqdm(total=len(dead_icmp), desc="Rescue", ncols=100) as pbar:
                futures = [executor.submit(rescue_one, ip) for ip in dead_icmp]
                for future in concurrent.futures.as_completed(futures):
                    row = future.result()
                    if row:
                        results.append(row)
                    pbar.update(1)

    # Sort results by IP string for consistency (simple lexicographic sort)
    results.sort(key=lambda r: r[0])

    # ---------------- Final Summary + Console CSV ----------------
    total_live = len(results)
    rescued_tcp = sum(1 for r in results if r[1] == "Dead" and r[2] == "TCP")
    rescued_udp = sum(1 for r in results if r[1] == "Dead" and r[2] == "UDP")
    rescued_both = sum(1 for r in results if r[1] == "Dead" and r[2] == "TCP+UDP")

    print(f"\n[+] Complete!")
    print(f"    Alive via ICMP        : {len(alive_icmp)}")
    print(f"    Rescued via TCP       : {rescued_tcp}")
    print(f"    Rescued via UDP       : {rescued_udp}")
    print(f"    Rescued via TCP+UDP   : {rescued_both}")
    print(f"    Total Live Hosts      : {total_live}\n")

    # Console output in CSV-like style (as requested)
    print("IP, Ping_Status, Rescue_Source, Open_Details")
    for row in results:
        # Join safely; all elements are strings
        print(",".join(row))

    # Write CSV file
    write_csv(results)
    print(f"\n[✔] Results saved to {LIVE_ONLY_CSV}")


if __name__ == "__main__":
    main()
