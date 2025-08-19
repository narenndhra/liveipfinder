# 💡 liveipfinder --- Live Host Finder (ICMP) with TCP/UDP Dead-Host Rescue

`liveipfinder` is a fast, thread-safe **live IP discovery tool**. It:

-   ✅ Uses **ICMP** for primary host discovery (fast + low noise)\
-   ✅ Optionally **rescues ICMP-dead hosts** by probing **TCP/UDP**
    ports you specify\
-   ✅ Prints **CSV-style** to console **and** writes `live_ips.csv`\
-   ✅ Includes **smart UDP** probing (payloads + retries + delays) for
    better responses

------------------------------------------------------------------------

## ✅ What's different now

-   **No scan "modes"** --- discovery is always **ICMP** (simple +
    predictable).\
-   **No `--ports`** --- instead use **`--probe-tcp`** /
    **`--probe-udp`** to *rescue only ICMP-dead* hosts.\
-   **Structured output** with explicit detection reasons (`ICMP`,
    `TCP`, `UDP`, or `TCP+UDP`) and **port details**.

------------------------------------------------------------------------

## 🛠 Installation

``` bash
git clone https://github.com/narenndhra/liveipfinder
cd liveipfinder
pip install -r requirements.txt
```

> Only dependency: `tqdm`.

------------------------------------------------------------------------

## ▶️ Usage

Create `targets.txt` (IPs and/or CIDRs):

``` text
192.168.1.10
192.168.1.0/30
10.0.0.5
10.0.1.0/29
```

### Quick runs

**ICMP only (fast discovery):**

``` bash
python3 liveipfinder.py targets.txt
```

**ICMP + TCP rescue (check these ports only on ICMP-dead IPs):**

``` bash
python3 liveipfinder.py targets.txt --probe-tcp "22,80,443,3389"
```

**ICMP + UDP rescue (try these UDP ports on ICMP-dead IPs):**

``` bash
python3 liveipfinder.py targets.txt --probe-udp "53,123,161,500"
```

**ICMP + TCP+UDP rescue (recommended defaults):**

``` bash
python3 liveipfinder.py targets.txt   --probe-tcp "22,80,443,3389"   --probe-udp "53,123,161,500"
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

  `--probe-tcp`           **TCP ports for         `22,80,443,3389`
                          dead-host rescue**      
                          (supports ranges like   
                          `22,80,1000-1005`)      

  `--probe-udp`           **UDP ports for         `53,123,161,500`
                          dead-host rescue**      
                          (supports ranges)       

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

-   **IP** --- target host\
-   **Ping_Status** --- `Alive` (ICMP replied) or `Dead` (ICMP failed
    but rescued)\
-   **Rescue_Source** --- `ICMP`, `TCP`, `UDP`, or `TCP+UDP`\
-   **Open_Details** --- `ICMP` for ICMP-alive rows, or the **actual
    ports** that replied on rescue (`22,80`, `UDP:161`, or combined
    `TCP:22,443 | UDP:161`)

------------------------------------------------------------------------

## 🔍 How it works (quick)

1)  **Phase 1 --- ICMP discovery:** ping each target with a thread
    pool.\
2)  **Phase 2 --- Dead-host rescue (optional):** for ICMP-dead IPs only,
    try your TCP/UDP probe lists.
    -   **TCP**: marks alive if any port connects.\
    -   **UDP**: sends small **protocol-aware payloads**
        (DNS/NTP/SNMP/IKE), uses **retries**, **inter-send delay**, and
        **wait windows**; marks alive only if a **packet is received**
        from the target.

------------------------------------------------------------------------

## ✅ Best practices

-   Use fewer threads + a small `--delay` if you need to be gentler on
    networks.\
-   ICMP may require admin/root on some OSes.\
-   For UDP, many services are **silent** unless payloads match; our
    payloads improve hit-rate on common ports but results still vary.\
-   If you need **full service enumeration**, run `nmap` on the **final
    live list**.

------------------------------------------------------------------------

## 🔒 Legal

Use only on networks where you have **explicit permission**. You are
responsible for compliance with laws and policies.

------------------------------------------------------------------------

## 👨‍💻 Author

Developed by Narendra Reddy (Entersoft Security)
