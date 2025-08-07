
# 💡 liveipfinder - Enterprise IP & Port Scanner

`liveipfinder` is a stealthy, enterprise-ready network scanner that:

- ✅ **Pings hosts first**
- ✅ **Scans ports only on hosts that did not respond to ping**
- ✅ Supports **ping-only** or **ping+port scan** modes
- ✅ Minimizes network noise while giving accurate results

---

## ✅ Features
- **Stealth Scanning**: ICMP + selective TCP port scanning
- **Two Scan Modes**:
  - `ping`: Just check if hosts are alive
  - `full`: Ping + port scan on "dead" hosts
- **Enterprise Port List**: Covers common infra devices (F5, Barracuda, Citrix, VPNs, etc.)
- **Multi-threaded**: Fast, customizable thread count
- **Clean Output**:
  - Progress bars for each phase
  - CSV with confirmed live hosts
  - Terminal summary table
- **Input Flexibility**: Accepts individual IPs or CIDR ranges

---

## 🔍 Default Enterprise Port List
```text
21,22,25,80,110,143,443,465,587,993,995,
8080,8443,9443,10443,2222,4353,4433,
500,1701,4500,1194,1494,2598,17777,17778,
161,162
```

---

## 🛠 Installation

```bash
git clone https://github.com/narenndhra/liveipfinder
cd liveipfinder
pip install -r requirements.txt
```

> 🔹 Note: `tqdm` is the only dependency.

---

## ▶️ Usage

Prepare a file `targets.txt`:
```text
192.168.1.10
192.168.1.0/30
10.0.0.5
10.0.1.0/29
```

### 🟢 Ping-only mode:
```bash
python3 liveipfinder.py targets.txt --mode ping
```

### 🟡 Full scan mode (ping + port scan on dead hosts):
```bash
python3 liveipfinder.py targets.txt --mode full
```

---

## ⚙️ Command-Line Options

| Option        | Description                                         | Default            |
|---------------|-----------------------------------------------------|--------------------|
| `input_file`  | File with IPs and/or CIDRs                         | (required)         |
| `--mode`      | `ping` or `full` (ping + port scan)               | `full`             |
| `--threads`   | Number of concurrent threads                       | 50                 |
| `--timeout`   | Timeout per ping/port check (in seconds)           | 2                  |
| `--delay`     | Delay between port scans (stealth mode)            | 0.0                |
| `--ports`     | Comma-separated list of ports to scan (in full mode) | Enterprise default |

---

## 📊 Output

### ✅ Summary
```
[+] Total targets: 254
[+] Threads: 50 | Timeout: 2s | Ports: 28 ports | Mode: full

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

### ✅ CSV Output (`live_ips.csv`)
```csv
IP, Ping_Status, Port_Status, Open_Ports
65.123.29.29, Alive, Skipped, -
65.123.29.50, Dead, Open, 443,8443
```

---

## ✅ Best Practices

- Use fewer threads and add delay (`--delay`) for production/stealth scans.
- Requires **admin/root** privileges for ping on some systems.
- For large networks, split into smaller CIDR/IP batches.
- Use `--mode ping` for safe, quick discovery without touching ports.

---

## 🔒 Disclaimer
This tool is for **authorized internal or client-side testing only**. Never use without permission. Always follow local laws and company policy.

---

## 👨‍💻 Author

Developed by Narendra Reddy (Entersoft Security)
