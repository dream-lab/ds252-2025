import pandas as pd
import matplotlib.pyplot as plt
import re, os, glob
from datetime import datetime

# ---------- Parsers ----------
def parse_cpu(x):
    if x is None:
        return 0.0
    x_str = str(x).strip().replace("%", "")
    return float(x_str) if x_str else 0.0

def parse_mem(x):
    x = str(x)
    part = x.split("/")[0].strip()
    match = re.match(r"([\d\.]+)([KMG]iB)", part)
    if not match:
        return 0.0
    val, unit = float(match.group(1)), match.group(2)
    factor = {"KiB":1/1024, "MiB":1, "GiB":1024}
    return val * factor[unit]

def parse_io(x):
    if not x:
        return (0.0, 0.0)
    rx, tx = x.split("/")
    def to_mb(val):
        match = re.match(r"([\d\.]+)([KMG]?B)", val.strip())
        if not match:
            return 0.0
        num, unit = float(match.group(1)), match.group(2)
        factor = {"B":1/1024/1024, "KB":1/1024, "MB":1, "GB":1024}
        return num * factor[unit]
    return to_mb(rx), to_mb(tx)

# ---------- Environments and Folders ----------
ENV_FOLDERS = {"vm": "vm_logs", "docker": "docker_logs", "baremetal": "baremetal_logs"}
ENV_FOLDERS = {"baremetal": "baremetal_logs","docker": "docker_logs","vm": "vm_logs"  }
# Add net workload mapping
FILENAME_TO_WORKLOAD = {"cpu": "cpu", "hdd": "IO", "vm": "mem", "net": "net"}
PLOT_WORKLOADS = ["cpu", "mem", "IO", "net"]
# ---------- Helper to extract timestamp ----------
def extract_timestamp(filename):
    match = re.search(r"_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.csv$", filename)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d_%H-%M-%S")

# ---------- Load latest files ----------
all_dfs = {}

for env, folder in ENV_FOLDERS.items():
    print(f"Looking for logs in {folder}/")
    all_files = glob.glob(os.path.join(folder, "stats_*.csv"))
    if not all_files:
        continue
    workloads_in_folder = {}
    for f in all_files:
        base = os.path.basename(f)
        match = re.match(r"stats_([a-zA-Z0-9]+)_.*\.csv", base)
        if not match:
            continue
        prefix = match.group(1)
        wl_name = FILENAME_TO_WORKLOAD.get(prefix)
        if wl_name is None:
            continue
        ts = extract_timestamp(base)
        if ts is None:
            continue
        if wl_name not in workloads_in_folder or ts > workloads_in_folder[wl_name][1]:
            workloads_in_folder[wl_name] = (f, ts)

    for wl, (latest_file, ts) in workloads_in_folder.items():
        print(f"  Latest file for workload '{wl}' in {env}: {latest_file}")
        df = pd.read_csv(latest_file, names=["time","cpu","mem","net_io","block_io"], keep_default_na=False)
        df = df[(df["cpu"].astype(str).str.strip()!="") & (df["mem"].astype(str).str.strip()!="")]
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["time"])
        if df.empty:
            print(f"    WARNING: empty DataFrame, skipping")
            continue
        start_time = df["time"].iloc[0]
        df["rel_time"] = (df["time"] - start_time).dt.total_seconds()

        df["cpu"] = df["cpu"].apply(parse_cpu)
        df["mem_used_MiB"] = df["mem"].apply(parse_mem)
        df[["net_rx_MB","net_tx_MB"]] = df["net_io"].apply(lambda x: pd.Series(parse_io(x)))
        df[["block_read_MB","block_write_MB"]] = df["block_io"].apply(lambda x: pd.Series(parse_io(x)))

        all_dfs[(env, wl)] = df

# ---------- Compute total global ranges ----------
global_ranges = {"cpu":[float("inf"), float("-inf")], "mem":[float("inf"), float("-inf")],
                 "net":[float("inf"), float("-inf")], "blk":[float("inf"), float("-inf")]}

for df in all_dfs.values():
    global_ranges["cpu"][0] = min(global_ranges["cpu"][0], df["cpu"].min())
    global_ranges["cpu"][1] = max(global_ranges["cpu"][1], df["cpu"].max())
    global_ranges["mem"][0] = min(global_ranges["mem"][0], df["mem_used_MiB"].min())
    global_ranges["mem"][1] = max(global_ranges["mem"][1], df["mem_used_MiB"].max())
    global_ranges["net"][0] = min(global_ranges["net"][0], df[["net_rx_MB","net_tx_MB"]].min().min())
    global_ranges["net"][1] = max(global_ranges["net"][1], df[["net_rx_MB","net_tx_MB"]].max().max())
    global_ranges["blk"][0] = min(global_ranges["blk"][0], df[["block_read_MB","block_write_MB"]].min().min())
    global_ranges["blk"][1] = max(global_ranges["blk"][1], df[["block_read_MB","block_write_MB"]].max().max())

# ---------- Plot total scaling ----------
fig, axes = plt.subplots(len(ENV_FOLDERS)*2, len(PLOT_WORKLOADS)*2, figsize=(24,18))
fig.subplots_adjust(hspace=0.8, wspace=0.5)

# ---------- Plot total scaling with grid ----------
fig, axes = plt.subplots(len(ENV_FOLDERS)*2, len(PLOT_WORKLOADS)*2, figsize=(24,18))
fig.subplots_adjust(hspace=0.8, wspace=0.5)

for i, env in enumerate(ENV_FOLDERS):
    for j, wl in enumerate(PLOT_WORKLOADS):
        key = (env, wl)
        if key not in all_dfs:
            continue
        df = all_dfs[key]
        row_idx = i*2
        col_idx = j*2
        ax_cpu = axes[row_idx, col_idx]
        ax_mem = axes[row_idx, col_idx+1]
        ax_net = axes[row_idx+1, col_idx]
        ax_blk = axes[row_idx+1, col_idx+1]

        # CPU
        ax_cpu.plot(df["rel_time"], df["cpu"], marker="o", color="blue")
        ax_cpu.set_ylim(global_ranges["cpu"])
        ax_cpu.set_title("CPU %")
        ax_cpu.set_xlabel("Time (s)")
        ax_cpu.grid(True)

        # Memory
        ax_mem.plot(df["rel_time"], df["mem_used_MiB"], marker="o", color="orange")
        ax_mem.set_ylim(global_ranges["mem"])
        ax_mem.set_title("Memory (MiB)")
        ax_mem.set_xlabel("Time (s)")
        ax_mem.grid(True)

        # Network I/O
        ax_net.plot(df["rel_time"], df["net_rx_MB"], label="RX")
        ax_net.plot(df["rel_time"], df["net_tx_MB"], label="TX")
        ax_net.set_ylim(global_ranges["net"])
        ax_net.legend(fontsize=8)
        ax_net.set_title("Network I/O (MB)")
        ax_net.set_xlabel("Time (s)")
        ax_net.grid(True)

        # Block I/O
        ax_blk.plot(df["rel_time"], df["block_read_MB"], label="Read")
        ax_blk.plot(df["rel_time"], df["block_write_MB"], label="Write")
        ax_blk.set_ylim(global_ranges["blk"])
        ax_blk.legend(fontsize=8)
        ax_blk.set_title("Block I/O (MB)")
        ax_blk.set_xlabel("Time (s)")
        ax_blk.grid(True)

# ---------- Column headers ----------
for j, wl in enumerate(PLOT_WORKLOADS):
    col_idx = j*2
    pos = axes[0, col_idx].get_position()
    wl_name = "IO" if wl.lower()=="io" else wl.upper()
    fig.text((pos.x0 + pos.x1)/2, pos.y1 + 0.05, wl_name,
             ha="center", va="bottom", fontsize=18, fontweight="bold")

# ---------- Row headers ----------
for i, env in enumerate(ENV_FOLDERS):
    row_idx = i*2
    pos_top = axes[row_idx,0].get_position()
    pos_bottom = axes[row_idx+1,0].get_position()
    fig.text(pos_top.x0 - 0.08, (pos_bottom.y0 + pos_top.y1)/2,
             env.upper(), ha="right", va="center", rotation=90,
             fontsize=18, fontweight="bold")

plt.suptitle("System Vitals Across Environments (Total Scaling)", fontsize=20, fontweight="bold")
plt.tight_layout(rect=[0.05,0.03,0.95,0.95])
plt.savefig("all_envs_vitals_total_scale_labeled.pdf")
plt.close()

