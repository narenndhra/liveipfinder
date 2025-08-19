# 💡 liveipfinder --- Live Host Finder (ICMP) with TCP/UDP Dead-Host Rescue

`liveipfinder` is a fast, thread-safe **live IP discovery tool**. It:

-   ✅ Uses **ICMP** for primary host discovery (fast + low noise)
-   ✅ Automatically attempts to **rescue ICMP-dead hosts** using
    TCP/UDP ports (default or custom)
-   ✅ Prints **CSV-style** to console **and** writes results to
    `live_ips.csv`
-   ✅ Includes **smart UDP** probing (payloads + retries + delays) for
    better accuracy

------------------------------------------------------------------------

## ✅ Key Features

-   **Always ICMP-first** --- discovery begins with ICMP pings
-   **Automatic rescue** --- dead hosts are rechecked via TCP/UDP probes
-   **Customizable** --- choose your own probe ports or use the defaults
-   **Structured output** --- explicit detection reasons (`ICMP`, `TCP`,
    `UDP`, or `TCP+UDP`) with open port details

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

Create a `targets.txt` file with IPs and/or CIDRs:

``` text
192.168.1.10
192.168.1.0/30
10.0.0.5
10.0.1.0/29
```

### Quick runs

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
                          rescue (supports ranges 
                          like `22,80,1000-1005`) 

  `--probe-udp`           UDP ports for dead-host `53,123,161,500`
                          rescue (supports        
                          ranges)                 

  `--udp-retries`         UDP retries per port    `2`

  `--udp-send-delay`      Delay (s) between UDP   `0.05`
                          sends (per port)        

  `--udp-wait`            Receive window (s)      `0.30`
                          after each UDP send     

  `--udp-jitter`          ±Jitter for UDP send    `0.02`
                          delay                   
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📊 Output

### Console (CSV-style) and `live_ips.csv`

    IP, Ping_Status, Rescue_Source, Open_Details
    192.168.1.1, Alive, ICMP, ICMP
    192.168.1.2, Dead, TCP, 22,80
    192.168.1.3, Dead, UDP, 161
    192.168.1.4, Dead, TCP+UDP, TCP:22,443 | UDP:161

**Columns**

-   **IP** --- target host
-   **Ping_Status** --- `Alive` (ICMP replied) or `Dead` (ICMP failed
    but rescued)
-   **Rescue_Source** --- `ICMP`, `TCP`, `UDP`, or `TCP+UDP`
-   **Open_Details** --- `ICMP` for ICMP-alive rows, or the actual ports
    that replied on rescue

------------------------------------------------------------------------

## 🔍 How it works

1.  **Phase 1 --- ICMP discovery:** ping each target with a thread pool
2.  **Phase 2 --- Dead-host rescue (automatic):** for ICMP-dead IPs
    only, the scanner uses your TCP/UDP probe lists (or defaults)
    -   **TCP**: marks alive if any port connects
    -   **UDP**: sends protocol-aware payloads (DNS/NTP/SNMP/IKE), uses
        retries, delays, and wait windows; marks alive only if a packet
        is received from the target

------------------------------------------------------------------------

## ✅ Best Practices

-   Use fewer threads + a small `--delay` to reduce load on networks
-   ICMP may require admin/root privileges on some OSes
-   UDP services may remain silent unless the right payload is used;
    results vary
-   For deeper service enumeration, run `nmap` on the final live host
    list

------------------------------------------------------------------------

## 🔒 Legal

Use only on networks where you have **explicit permission**. The author
is not responsible for misuse.

------------------------------------------------------------------------

## 👨‍💻 Author

Developed by Narendra Reddy (Entersoft Security)
