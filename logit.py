import pandas as pd
import matplotlib.pyplot as plt

# Define the log file location
log_file = "storage.log"

def parse_logs(log_file):
    data = []
    with open(log_file, "r") as f:
        for line in f:
            parts = line.split("|")
            time = float(parts[-1].split(":")[1].strip())
            uploader = parts[1].split(":")[1].strip()
            downloader = parts[2].split(":")[1].strip()
            block_id = int(parts[3].split(":")[1].strip())
            data.append((time, uploader, downloader, block_id))
    return pd.DataFrame(data, columns=["Time", "Uploader", "Downloader", "Block ID"])

# Parse logs
df = parse_logs(log_file)
print(df.head())

utilization = df.groupby("Uploader")["Block ID"].count() / df["Time"].max()
utilization.plot(kind="bar", figsize=(10, 6), color="orange")
plt.title("Node Upload Utilization")
plt.xlabel("Node")
plt.ylabel("Transfers per Unit Time")
plt.show()

