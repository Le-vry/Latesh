import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

improve_data = np.genfromtxt(
	BASE_DIR / "improved_page_load_times_utf8.csv",
	delimiter=",",
	names=True,
	dtype=None,
	encoding="utf-8",
)

old_csv_path = BASE_DIR / "old_page_load_times_utf8.csv"
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
	print("Optional file old_page_load_times_utf8.csv not found; skipping old-data load.")

trace_names = improve_data["trace_name"]
iterations = improve_data["iteration"]
load_ms = improve_data["load_ms"]

old_trace_names = old_data["trace_name"] if old_data is not None else None
old_iterations = old_data["iteration"] if old_data is not None else None
old_load_ms = old_data["load_ms"] if old_data is not None else None

old_profile_load_ms = old_load_ms[0:31] if old_data is not None else None
old_leaderboard_load_ms = old_load_ms[31:62] if old_data is not None else None

old_timestamps = old_data["timestamp"] if old_data is not None else None

profile_load_ms = load_ms[0:31]
leaderboard_load_ms = load_ms[31:62]

timestamps = improve_data["timestamp"]

print(f"Loaded {len(improve_data)} rows from improved_page_load_times_utf8.csv")
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

print("----------------------------------------")

print(f"old median profile load time (ms): {np.median(old_profile_load_ms)}" if old_data is not None else "No old data for profile load times.", "|", f"old median leaderboard load time (ms): {np.median(old_leaderboard_load_ms)}" if old_data is not None else "No old data for leaderboard load times.")
print(f"improve median profile load time (ms): {np.median(profile_load_ms)}", "|", f"improve median leaderboard load time (ms): {np.median(leaderboard_load_ms)}")
print(f"old p95 profile load time (ms): {np.percentile(old_profile_load_ms, 95)}" if old_data is not None else "No old data for profile load times.", "|", f"old p95 leaderboard load time (ms): {np.percentile(old_leaderboard_load_ms, 95)}" if old_data is not None else "No old data for leaderboard load times.")
print(f"improve p95 profile load time (ms): {np.percentile(profile_load_ms, 95)}", "|", f"improve p95 leaderboard load time (ms): {np.percentile(leaderboard_load_ms, 95)}")

procent_improvement_median_profile = (np.median(profile_load_ms)/np.median(old_profile_load_ms) - 1) * 100 if old_data is not None else None
procent_improvement_p95_profile = (np.percentile(profile_load_ms, 95)/np.percentile(old_profile_load_ms, 95) - 1) * 100 if old_data is not None else None
procent_improvement_median_leaderboard = (np.median(leaderboard_load_ms)/np.median(old_leaderboard_load_ms) - 1) * 100 if old_data is not None else None
procent_improvement_p95_leaderboard = (np.percentile(leaderboard_load_ms, 95)/np.percentile(old_leaderboard_load_ms, 95) - 1) * 100 if old_data is not None else None

print(f"Percentage improvement in median profile load time: {procent_improvement_median_profile:.2f}%" if procent_improvement_median_profile is not None else "No old data to calculate percentage improvement for median profile load time.", "|", f"Percentage improvement in median leaderboard load time: {procent_improvement_median_leaderboard:.2f}%" if procent_improvement_median_leaderboard is not None else "No old data to calculate percentage improvement for median leaderboard load time.")
print(f"Percentage improvement in p95 profile load time: {procent_improvement_p95_profile:.2f}%" if procent_improvement_p95_profile is not None else "No old data to calculate percentage improvement for p95 profile load time.", "|", f"Percentage improvement in p95 leaderboard load time: {procent_improvement_p95_leaderboard:.2f}%" if procent_improvement_p95_leaderboard is not None else "No old data to calculate percentage improvement for p95 leaderboard load time.")
show = input("Show plots? (y/n): ")
if show.lower() != "y":
	exit()

fig, axes = plt.subplots(2, 2, figsize=(10, 6))
ax1, ax2, ax3, ax4 = axes.flatten()

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

ax3.plot(iterations[:31], old_profile_load_ms, marker="o", linestyle="-") if old_data is not None else None
ax3.set_title("Old Profile Load Times")
ax3.set_xlabel("Iteration")
ax3.set_ylabel("Load Time (ms)")
ax3.grid()

ax4.plot(iterations[31:62], old_leaderboard_load_ms, marker="o", linestyle="-") if old_data is not None else None
ax4.set_title("Old Leaderboard Load Times")
ax4.set_xlabel("Iteration")
ax4.set_ylabel("Load Time (ms)")
ax4.grid()

plt.show()

save = input("Save plots? (y/n): ")
if save.lower() == "y":
	fig.savefig("page_load_times.png")
	print("Plots saved as page_load_times.png")