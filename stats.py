import matplotlib.pyplot as plt
import numpy as np

data = np.genfromtxt(
	"page_load_times_utf8.csv",
	delimiter=",",
	names=True,
	dtype=None,
	encoding="utf-8",
)

trace_names = data["trace_name"]
iterations = data["iteration"]
load_ms = data["load_ms"]

profile_load_ms = load_ms[0:31]
leaderboard_load_ms = load_ms[31:62]

timestamps = data["timestamp"]

print(f"Loaded {len(data)} rows from page_load_times_utf8.csv")
print("Columns:", data.dtype.names)
print("Coldboots: ")
print(f"First load time (ms): {load_ms[0]}")
print(f"30th load time (ms): {load_ms[30]}")
print(f"Profile load time (ms): {profile_load_ms} {len(profile_load_ms)} entries")
print(f"Leaderboard load time (ms): {leaderboard_load_ms} {len(leaderboard_load_ms)} entries")
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