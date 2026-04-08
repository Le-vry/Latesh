from csv import DictReader
from pathlib import Path
from statistics import mean

from scipy.stats import wilcoxon


def trace_to_group(trace_name: str) -> tuple[str, str] | None:
	"""Map a trace name to its page group and condition."""

	if trace_name.endswith("_cold"):
		return None

	if trace_name.startswith("profile_page_"):
		page = "profile"
	elif trace_name.startswith("leaderboard_page_"):
		page = "leaderboard"
	else:
		return None

	if "_sequential_" in trace_name or "_sekventiell_" in trace_name:
		condition = "sequential"
	elif "_parallel_" in trace_name:
		condition = "parallel"
	else:
		return None

	return page, condition


def parse_db_size(csv_path: Path) -> str:
	"""Extract the database size prefix from a session filename."""

	db_size = csv_path.stem.split("_", 1)[0]
	if not db_size.isdigit():
		raise ValueError(f"Unable to extract database size from {csv_path.name}")
	return db_size


def load_session(csv_path: Path) -> dict[str, dict[str, tuple[list[float], list[float]]]]:
	"""Load one session file and split it into db-size and page-specific paired runs."""

	db_size = parse_db_size(csv_path)
	rows_by_page: dict[str, dict[int, dict[str, float]]] = {}

	with csv_path.open(encoding="utf-16", newline="") as handle:
		reader = DictReader(handle)
		for row in reader:
			trace_name = row["trace_name"].strip()

			group = trace_to_group(trace_name)
			if group is None:
				continue

			page, condition = group

			iteration = int(row["iteration"])
			load_ms = float(row["load_ms"])

			rows_by_page.setdefault(page, {}).setdefault(iteration, {})[condition] = load_ms

	grouped_data: dict[str, dict[str, tuple[list[float], list[float]]]] = {db_size: {}}

	for page, rows_by_iteration in rows_by_page.items():
		seq: list[float] = []
		par: list[float] = []

		for iteration in sorted(rows_by_iteration):
			pair = rows_by_iteration[iteration]
			if "sequential" not in pair or "parallel" not in pair:
				raise ValueError(
					f"Missing matched row in {csv_path.name} for {page} iteration {iteration}"
				)

			seq.append(pair["sequential"])
			par.append(pair["parallel"])

		grouped_data[db_size][page] = (seq, par)

	return grouped_data


def load_all_sessions(data_dir: Path) -> dict[str, dict[str, tuple[list[float], list[float]]]]:
	"""Load all session files and concatenate the matched measurements per db size and page."""

	grouped_all: dict[str, dict[str, tuple[list[float], list[float]]]] = {}
	page_order = ("profile", "leaderboard")

	for csv_path in sorted(data_dir.glob("*.csv")):
		grouped_session = load_session(csv_path)
		db_size = parse_db_size(csv_path)
		grouped_all.setdefault(db_size, {})
		page_data = grouped_session[db_size]

		for page in page_order:
			if page not in page_data:
				continue

			seq, par = page_data[page]
			if len(seq) != len(par):
				raise ValueError(
					f"Unbalanced data in {csv_path.name} for {db_size} {page}: seq={len(seq)}, par={len(par)}"
				)

			if page not in grouped_all[db_size]:
				grouped_all[db_size][page] = ([], [])

			grouped_all[db_size][page][0].extend(seq)
			grouped_all[db_size][page][1].extend(par)

	return grouped_all


def run_analysis(label: str, seq: list[float], par: list[float]) -> None:
	"""Run the paired Wilcoxon test for one db-size/page group."""

	if len(seq) != len(par):
		raise ValueError(f"Mismatch between sequential and parallel counts for {label}: {len(seq)} vs {len(par)}")

	print(f"{label} - antal par: {len(seq)}")
	print(f"{label} - medel sequential: {mean(seq):.2f}")
	print(f"{label} - medel parallel: {mean(par):.2f}")

	stat, p_value = wilcoxon(seq, par, alternative="greater", zero_method="wilcox")
	print(f"{label} - W-statistik:", stat)
	print(f"{label} - p-värde:", p_value)
	print()


# Each CSV file is one session with interleaved sequential and parallel rows.
path_to_data = Path(__file__).with_name("csv-garb")
print("Data loaded from:", path_to_data)

grouped_data = load_all_sessions(path_to_data)

# The samples are paired, so Wilcoxon can compare the two conditions directly.
for db_size in sorted(grouped_data, key=int):
	for page in ("profile", "leaderboard"):
		if page not in grouped_data[db_size]:
			continue

		seq, par = grouped_data[db_size][page]
		run_analysis(f"db={db_size} {page}", seq, par)