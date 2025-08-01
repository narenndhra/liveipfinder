# liveipfinder - Enterprise IP & Port Scanner

liveipfinder is a stealthy, enterprise-ready network scanner that:
- **Pings hosts first**
- **Scans ports only on hosts that did not respond to ping**
- Minimizes network noise while giving accurate results.

---

## ✅ Features
- **Stealth Scanning**: ICMP + selective port scanning
- **Enterprise Port List**: Covers common infra devices (F5, Barracuda, Citrix, VPNs)
- **Multi-threaded**: Speed with configurable threads
- **Clean Output**:
  - Progress bars during scan
  - Summary table after completion
- **CSV Export**: Saves results to `live_ips.csv`

---

## 🔍 Default Enterprise Port List
```
21,22,25,80,110,143,443,465,587,993,995,
8080,8443,9443,10443,2222,4353,4433,
500,1701,4500,1194,1494,2598,17777,17778,
161,162
```

---

## 🛠 Installation
Clone the repository:
```bash
git clone https://github.com/narenndhra/liveipfinder
cd liveipfinder
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## ▶️ Usage
Prepare an input file (e.g., `targets.txt`) with IPs and/or subnets:
```
192.168.1.10
192.168.1.0/30
10.0.0.5
10.0.1.0/29
```

Run the scanner:
```bash
python3 liveipfinder.py targets.txt --threads 100 --timeout 3 --delay 0.5
```

---

## ⚙️ Options
| Switch        | Description                                    | Default |
|--------------|-----------------------------------------------|---------|
| `input_file` | File with IPs and/or subnets (mandatory)      |   -     |
| `--threads`  | Number of concurrent threads                 |   50    |
| `--timeout`  | Timeout (in seconds) per ping/port check     |   2     |
| `--delay`    | Delay (in seconds) between scans (stealth)   |   0.0   |

---

## 📊 Output
**Summary:**
```
[+] Total targets: 254
[+] Threads: 50 | Timeout: 2s | Ports: 28 ports

[+] Phase 1: Pinging targets...
Pinging: 100%|████████████████████████████████████████████████████| 254/254 [00:08<00:00, 29.42it/s]

[+] Ping complete! Alive (Ping): 73 | Dead: 181

[+] Phase 2: Scanning ports on dead IPs (181)...
Port Scan: 100%|██████████████████████████████████████████████████| 181/181 [03:44<00:00,  1.24s/it]

[+] Scan complete!
Alive from Ping: 73
Alive from Ports: 1
Total Live Hosts: 74
```

**Final Table:**
```
IP, Ping_Status, Port_Status, Open_Ports
65.123.29.29, Alive, Skipped, -
65.123.29.50, Dead, Open, 443,8443
```

---

## ✅ Best Practices
- Use fewer threads and add delay in production for stealth
- Requires elevated privileges for ICMP on some systems
- For large scans, split targets into smaller files

---

## 🔒 Disclaimer
This tool is for **authorized security testing only**. Do not use without permission.

---

## 👨‍💻 Author
Developed by Your Name
