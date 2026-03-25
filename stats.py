import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

improve_data = np.genfromtxt(
	"page_load_times_utf8.csv",
	delimiter=",",
	names=True,
	dtype=None,
	encoding="utf-8",
)

old_csv_path = Path("page_load_times_utf8_old.csv")
old_data = None
if old_csv_path.exists():
	old_data = np.genfromtxt(
		old_csv_path,
		delimiter=",",
		names=True,
		dtype=None,
		encoding="utf-8",
	)
else:
	print("Optional file page_load_times_utf8_old.csv not found; skipping old-data load.")

trace_names = improve_data["trace_name"]
iterations = improve_data["iteration"]
load_ms = improve_data["load_ms"]

profile_load_ms = load_ms[0:31]
leaderboard_load_ms = load_ms[31:62]

timestamps = improve_data["timestamp"]

print(f"Loaded {len(improve_data)} rows from page_load_times_utf8.csv")
print("Columns:", improve_data.dtype.names)
print("Coldboots: ")
print(f"First load time (ms): {load_ms[0]}")
print(f"30th load time (ms): {load_ms[30]}")
print(f"Profile load time (ms): {profile_load_ms} {len(profile_load_ms)} entries")
print(f"Leaderboard load time (ms): {leaderboard_load_ms} {len(leaderboard_load_ms)} entries")

print(f"p95 profile load time (ms): {np.percentile(profile_load_ms, 95)}")
print(f"median profile load time (ms): {np.median(profile_load_ms)}")
print(f"p95 leaderboard load time (ms): {np.percentile(leaderboard_load_ms, 95)}")
print(f"median leaderboard load time (ms): {np.median(leaderboard_load_ms)}")

show = input("Show plots? (y/n): ")
if show.lower() != "y":
	exit()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

ax1.plot(iterations[:31], profile_load_ms, marker="o", linestyle="-")
ax1.set_title("Profile Load Times")
ax1.set_xlabel("Iteration")
ax1.set_ylabel("Load Time (ms)")
ax1.grid()

ax2.plot(iterations[31:62], leaderboard_load_ms, marker="o", linestyle="-")
ax2.set_title("Leaderboard Load Times")
ax2.set_xlabel("Iteration")
ax2.set_ylabel("Load Time (ms)")
ax2.grid()

plt.show()

save = input("Save plots? (y/n): ")
if save.lower() == "y":
	fig.savefig("page_load_times.png")
	print("Plots saved as page_load_times.png")