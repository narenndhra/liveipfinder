# 💡 liveipfinder --- Live Host Finder (ICMP) with TCP/UDP Dead-Host Rescue

`liveipfinder` is a fast, thread-safe **live IP discovery tool** for
enterprise networks.

It helps penetration testers, sysadmins, and network engineers
**identify live hosts quickly**, even when ICMP is blocked.

------------------------------------------------------------------------

## 🚀 Features at a Glance

-   **Input handling**
    -   Accepts both individual IPs and CIDR subnets
    -   Expands subnets automatically
    -   Deduplicates overlapping IPs
-   **Host discovery**
    -   ICMP-first for fast liveness checks
    -   Cross-platform ping handling (Windows/Linux)
-   **Dead-host rescue (automatic, configurable)**
    -   If ICMP fails, the scanner rescues using TCP/UDP probes
    -   Defaults included (`22,80,443,3389` for TCP and `53,123,161,500`
        for UDP)
    -   Custom probe ports supported (e.g., `--probe-tcp "22,80"`)
    -   UDP with retries, delays, jitter, and payloads for
        DNS/NTP/SNMP/IKE
-   **Output**
    -   CSV format (console + `live_ips.csv`)
    -   `Ping_Status` shows Alive/Dead
    -   `Rescue_Source` indicates ICMP/TCP/UDP/TCP+UDP
    -   `Open_Details` shows ports or ICMP reason
-   **Performance**
    -   Multithreaded scanning with adjustable `--threads`
    -   Tunable timeouts, delays, and UDP jitter
-   **Safety & usability**
    -   ICMP-only mode available
    -   Smart defaults make it easy to run out-of-the-box
    -   Legal disclaimer included

------------------------------------------------------------------------

## 🛠 Installation

``` bash
git clone https://github.com/narenndhra/liveipfinder
cd liveipfinder
pip install -r requirements.txt
```

> Only dependency: `tqdm`

------------------------------------------------------------------------

## ▶️ Usage

Prepare `targets.txt` with IPs and/or subnets:

``` text
192.168.1.10
192.168.1.0/30
10.0.0.5
10.0.1.0/29
```

### Example runs

**ICMP only (fast discovery):**

``` bash
python3 liveipfinder.py targets.txt --probe-tcp "" --probe-udp ""
```

**ICMP + default TCP+UDP rescue (recommended):**

``` bash
python3 liveipfinder.py targets.txt
```

**ICMP + custom TCP rescue:**

``` bash
python3 liveipfinder.py targets.txt --probe-tcp "22,80,443,3389"
```

**ICMP + custom UDP rescue:**

``` bash
python3 liveipfinder.py targets.txt --probe-udp "53,123,161,500"
```

**ICMP + custom TCP+UDP rescue:**

``` bash
python3 liveipfinder.py targets.txt --probe-tcp "22,443" --probe-udp "53,161"
```

------------------------------------------------------------------------

## ⚙️ Command-Line Options

  -----------------------------------------------------------------------
  Option                  Description             Default
  ----------------------- ----------------------- -----------------------
  `input_file`            File with IPs and/or    (required)
                          CIDRs                   

  `--threads`             Worker threads for      `80`
                          ping/probes             

  `--timeout`             Timeout (s) for         `2.0`
                          ping/TCP/UDP ops        

  `--delay`               Pause (s) before rescue `0.0`
                          phase                   

  `--probe-tcp`           TCP ports for dead-host `22,80,443,3389`
                          rescue (supports        
                          ranges)                 

  `--probe-udp`           UDP ports for dead-host `53,123,161,500`
                          rescue (supports        
                          ranges)                 

  `--udp-retries`         UDP retries per port    `2`

  `--udp-send-delay`      Delay (s) between UDP   `0.05`
                          sends                   

  `--udp-wait`            Receive window (s)      `0.30`
                          after UDP send          

  `--udp-jitter`          ±Jitter for UDP send    `0.02`
                          delay  
                          
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📊 Output Example

    IP, Ping_Status, Rescue_Source, Open_Details
    192.168.1.1, Alive, ICMP, ICMP
    192.168.1.2, Dead, TCP, 22,80
    192.168.1.3, Dead, UDP, 161
    192.168.1.4, Dead, TCP+UDP, TCP:22,443 | UDP:161

------------------------------------------------------------------------

## 🔍 Workflow

1.  Expand targets (IPs + subnets → unique IPs)\
2.  ICMP sweep → Alive/Dead classification\
3.  Dead-host rescue via TCP/UDP probes\
4.  Results stored in console + CSV

------------------------------------------------------------------------

## ✅ Best Practices

-   Run ICMP + TCP+UDP rescue for best coverage\
-   Reduce `--threads` and add `--delay` for low-bandwidth links\
-   Remember: UDP may be silent without correct payloads\
-   Use results as input to `nmap` for deeper service enumeration

------------------------------------------------------------------------

## 🔒 Legal

Use only on networks where you have **explicit permission**. The author
is not responsible for misuse.

------------------------------------------------------------------------

## 👨‍💻 Author

Developed by Narendra Reddy (Entersoft Security)
