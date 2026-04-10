from csv import DictReader
from math import sqrt
from pathlib import Path
from statistics import mean, median

from scipy.stats import rankdata, t, wilcoxon


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


def parse_float_sv(value: str) -> float:
	"""Parse numbers that may use Swedish decimal comma."""

	return float(value.strip().replace(",", "."))


def sample_std(values: list[float]) -> float:
	"""Return sample standard deviation with n-1 in the denominator."""

	if len(values) < 2:
		return 0.0
	mu = mean(values)
	return sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def percentile(values: list[float], p: float) -> float:
	"""Compute percentile with linear interpolation between sorted neighbors."""

	if not values:
		raise ValueError("Cannot compute percentile of empty list")

	sorted_values = sorted(values)
	if len(sorted_values) == 1:
		return sorted_values[0]

	idx = (len(sorted_values) - 1) * p
	lower = int(idx)
	upper = min(lower + 1, len(sorted_values) - 1)
	fraction = idx - lower
	return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def mean_ci95(values: list[float]) -> tuple[float, float]:
	"""Return 95% confidence interval for the mean using Student's t."""

	n = len(values)
	if n < 2:
		mu = mean(values) if values else 0.0
		return mu, mu

	mu = float(mean(values))
	s = float(sample_std(values))
	se = s / sqrt(n)
	t_crit = float(t.ppf(0.975, n - 1))
	margin = t_crit * se
	return float(mu - margin), float(mu + margin)


def rank_biserial_paired(seq: list[float], par: list[float]) -> float:
	"""Rank-biserial correlation for paired samples (compatible with Wilcoxon signed-rank)."""

	if len(seq) != len(par):
		raise ValueError(f"Pair length mismatch: {len(seq)} vs {len(par)}")

	diffs = [s - p for s, p in zip(seq, par)]
	nonzero = [d for d in diffs if d != 0]
	if not nonzero:
		return 0.0

	abs_diffs = [abs(d) for d in nonzero]
	ranks = rankdata(abs_diffs, method="average")
	w_pos = sum(r for d, r in zip(nonzero, ranks) if d > 0)
	w_neg = sum(r for d, r in zip(nonzero, ranks) if d < 0)
	total = w_pos + w_neg
	if total == 0:
		return 0.0

	return float((w_pos - w_neg) / total)


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

	for csv_path in sorted(data_dir.glob("[0-9]*_*.csv")):
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


def load_network_metrics(csv_path: Path) -> dict[str, dict[str, list[float]]]:
	"""Load ping/upload/download grouped by db size from the extra measurements CSV."""

	metrics: dict[str, dict[str, list[float]]] = {}

	with csv_path.open(encoding="utf-8", newline="") as handle:
		reader = DictReader(handle)
		for row in reader:
			db_size = row["db-storlek (users)"].strip()
			entry = metrics.setdefault(db_size, {"ping": [], "upload": [], "download": []})

			entry["ping"].append(parse_float_sv(row["ping (ms)"]))
			entry["upload"].append(parse_float_sv(row["uppladdning (Mbps)"]))
			entry["download"].append(parse_float_sv(row["nedladdning (Mbps)"]))

	return metrics


def network_summary(network_metrics: dict[str, dict[str, list[float]]], db_size: str) -> dict[str, float]:
	"""Summarize network metrics for one database size."""

	if db_size not in network_metrics:
		raise ValueError(f"Missing network metrics for db size {db_size}")

	entry = network_metrics[db_size]
	return {
		"ping_mean": mean(entry["ping"]),
		"ping_std": sample_std(entry["ping"]),
		"upload_mean": mean(entry["upload"]),
		"download_mean": mean(entry["download"]),
	}


def run_analysis(
	db_size: str,
	page: str,
	seq: list[float],
	par: list[float],
	network_metrics: dict[str, dict[str, list[float]]],
) -> None:
	"""Run paired analysis and print values suitable for results/discussion tables."""

	if len(seq) != len(par):
		raise ValueError(f"Mismatch between sequential and parallel counts for db={db_size} {page}: {len(seq)} vs {len(par)}")

	seq_mean = mean(seq)
	par_mean = mean(par)
	seq_std = sample_std(seq)
	par_std = sample_std(par)

	seq_median = median(seq)
	par_median = median(par)
	seq_p95 = percentile(seq, 0.95)
	par_p95 = percentile(par, 0.95)
	seq_ki_low, seq_ki_high = mean_ci95(seq)
	par_ki_low, par_ki_high = mean_ci95(par)

	abs_improvement = seq_mean - par_mean
	rel_improvement = (abs_improvement / seq_mean) * 100

	net = network_summary(network_metrics, db_size)

	label = f"db={db_size} page={page}"
	print(f"{label} - antal par: {len(seq)}")
	print(f"{label} - network ping mean±std (ms): {net['ping_mean']:.2f} ± {net['ping_std']:.2f}")
	print(f"{label} - mean seq/par (ms): {seq_mean:.2f} / {par_mean:.2f}")
	print(f"{label} - std seq/par (ms): {seq_std:.2f} / {par_std:.2f}")
	print(f"{label} - 95% KI seq (ms): {seq_ki_low:.2f} till {seq_ki_high:.2f}")
	print(f"{label} - 95% KI par (ms): {par_ki_low:.2f} till {par_ki_high:.2f}")
	print(f"{label} - median seq/par (ms): {seq_median:.2f} / {par_median:.2f}")
	print(f"{label} - p95 seq/par (ms): {seq_p95:.2f} / {par_p95:.2f}")
	print(f"{label} - improvement abs/rel: {abs_improvement:.2f} ms / {rel_improvement:.2f}%")

	stat, p_value = wilcoxon(seq, par, alternative="greater", zero_method="wilcox")
	r_rb = rank_biserial_paired(seq, par)
	print(f"{label} - W-statistik: {stat:.2f}")
	print(f"{label} - p-värde: {p_value:.6g}")
	print(f"{label} - rank-biserial (r_rb): {r_rb:.3f}")

	# LaTeX row for a compact result table that includes network context.
	latex_row = (
		f"{db_size} & {page} & {len(seq)} & "
		f"{net['ping_mean']:.1f} $\\pm$ {net['ping_std']:.1f} & "
		f"{seq_mean:.1f} & {seq_ki_low:.1f}--{seq_ki_high:.1f} & "
		f"{par_mean:.1f} & {par_ki_low:.1f}--{par_ki_high:.1f} & "
		f"{abs_improvement:.1f} & {rel_improvement:.1f}\\% & "
		f"{seq_p95:.1f} & {par_p95:.1f} & {r_rb:.3f} & {p_value:.2e} \\\\"
	)
	print(f"{label} - LaTeX-rad:")
	print(latex_row)
	print()


# Each CSV file is one session with interleaved sequential and parallel rows.
path_to_data = Path(__file__).with_name("csv-garb")
print("Data loaded from:", path_to_data)

grouped_data = load_all_sessions(path_to_data)
network_csv = path_to_data / "Garb extra mätvärden.csv"
network_metrics = load_network_metrics(network_csv)

# The samples are paired, so Wilcoxon can compare the two conditions directly.
for db_size in sorted(grouped_data, key=int):
	for page in ("profile", "leaderboard"):
		if page not in grouped_data[db_size]:
			continue

		seq, par = grouped_data[db_size][page]
		run_analysis(db_size, page, seq, par, network_metrics)