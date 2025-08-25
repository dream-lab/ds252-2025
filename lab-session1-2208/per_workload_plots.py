import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re

def parse_mem(mem_str):
    if '/' in mem_str:
        return float(mem_str.split('/')[0].replace('MiB','').strip())
    return 0.0
def parse_mem(mem_str):
    """
    Converts Docker Memory usage strings like '1.009GiB / 2GiB' or '512MiB / 2GiB' to MiB.
    """
    used_str = mem_str.split('/')[0].strip()

    def to_mib(s):
        s = s.strip()
        if s.endswith('GiB'):
            return float(s[:-3].strip()) * 1024
        elif s.endswith('MiB'):
            return float(s[:-3].strip())
        elif s.endswith('kB'):
            return float(s[:-2].strip()) / 1024
        elif s.endswith('B'):
            return float(s[:-1].strip()) / (1024**2)
        else:
            return float(s)  # fallback for plain numbers

    return to_mib(used_str)

def parse_io(io_str):
    if '/' in io_str:
        rx, tx = io_str.split('/')
        rx = rx.replace('MB','').strip()
        tx = tx.replace('MB','').strip()
        return float(rx), float(tx)
    return 0.0, 0.0
# Existing parse_io function
def parse_io(io_str):
    """
    Converts Docker Net I/O strings like '93.6kB / 12.3MB' to floats in bytes.
    """
    rx_str, tx_str = io_str.split('/')
    
    def to_bytes(s):
        s = s.strip()
        if s.endswith('GB'):
            return float(s[:-2].strip()) * 1024**3
        elif s.endswith('MB'):
            return float(s[:-2].strip()) * 1024**2
        elif s.endswith('kB'):
            return float(s[:-2].strip()) * 1024
        elif s.endswith('B'):
            return float(s[:-1].strip())
        else:  # fallback for plain numbers
            return float(s)

    rx = to_bytes(rx_str)
    tx = to_bytes(tx_str)
    return rx, tx

def plot_log(csv_file, out_dir):
    df = pd.read_csv(csv_file)

    # Parse memory and IO columns
    if 'Memory(RAM)' in df.columns:
        df['Memory'] = df['Memory(RAM)'].apply(parse_mem)
    if 'Net I/O(RX/Tx)' in df.columns:
        df['Net_RX'], df['Net_TX'] = zip(*df['Net I/O(RX/Tx)'].apply(parse_io))
    if 'Block I/O(Read/Write)' in df.columns:
        df['Blk_Read'], df['Blk_Write'] = zip(*df['Block I/O(Read/Write)'].apply(parse_io))

    # Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Create 2x2 plot
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(os.path.basename(csv_file), fontsize=16)

    # CPU
    if 'CPU(%)' in df.columns:
        axs[0,0].plot(df['Timestamp'], df['CPU(%)'], color='tab:blue')
        axs[0,0].set_title('CPU Usage (%)')
        axs[0,0].set_ylabel('CPU (%)')
        axs[0,0].tick_params(axis='x', rotation=45)
        axs[0,0].grid(True)  # <-- Grid added

    # Memory
    if 'Memory' in df.columns:
        axs[0,1].plot(df['Timestamp'], df['Memory'], color='tab:green')
        axs[0,1].set_title('Memory Usage (MiB)')
        axs[0,1].set_ylabel('Memory (MiB)')
        axs[0,1].tick_params(axis='x', rotation=45)
        axs[0,1].grid(True)  # <-- Grid added

    # Network I/O
    if 'Net_RX' in df.columns and 'Net_TX' in df.columns:
        axs[1,0].plot(df['Timestamp'], df['Net_RX'], label='RX', color='tab:orange')
        axs[1,0].plot(df['Timestamp'], df['Net_TX'], label='TX', color='tab:red')
        axs[1,0].set_title('Network I/O (MB)')
        axs[1,0].set_ylabel('MB')
        axs[1,0].legend()
        axs[1,0].tick_params(axis='x', rotation=45)
        axs[1,0].grid(True)  # <-- Grid added

    # Block I/O
    if 'Blk_Read' in df.columns and 'Blk_Write' in df.columns:
        axs[1,1].plot(df['Timestamp'], df['Blk_Read'], label='Read', color='tab:purple')
        axs[1,1].plot(df['Timestamp'], df['Blk_Write'], label='Write', color='tab:brown')
        axs[1,1].set_title('Block I/O (MB)')
        axs[1,1].set_ylabel('MB')
        axs[1,1].legend()
        axs[1,1].tick_params(axis='x', rotation=45)
        axs[1,1].grid(True)  # <-- Grid added

    plt.tight_layout(rect=[0,0,1,0.95])

    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, os.path.basename(csv_file).replace('.csv','.png'))
    plt.savefig(out_file)
    plt.close()
    print(f"Saved plot: {out_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot newest logs per type")
    parser.add_argument("log_folder", help="Folder containing CSV log files")
    parser.add_argument("--out", default="plots", help="Folder to save plots")
    args = parser.parse_args()

    csv_files = glob.glob(os.path.join(args.log_folder, "*.csv"))
    if not csv_files:
        print("No CSV files found!")
        exit(1)

    # Group files by type (cpu, hdd, vm)
    file_types = {}
    type_pattern = r'stats_(\w+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv'
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'

    for f in csv_files:
        m = re.match(type_pattern, os.path.basename(f))
        if m:
            log_type = m.group(1)
            ts_match = re.search(timestamp_pattern, f)
            ts = ts_match.group(1) if ts_match else ''
            file_types.setdefault(log_type, []).append((ts, f))

    # Pick newest file per type
    newest_files = [max(files, key=lambda x: x[0])[1] for files in file_types.values()]

    print(f"Plotting newest file per type: {newest_files}")
    for f in newest_files:
        plot_log(f, args.out)

