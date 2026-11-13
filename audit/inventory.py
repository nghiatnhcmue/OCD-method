from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import datasets

OUT = S.RESULTS / "INVENTORY.md"
FOLDERS = {
    "(gốc)": "README, requirements.txt, run_all.sh, settings.py",
    "ablation": "bóc tách v2 đã công bố (ablation/run.py, variants.py, summarize.py)",
    "applications": "ba mạng ứng dụng: chuẩn bị dữ liệu, chạy, tổng hợp, độ ổn định",
    "audit": "kiểm toán: chạy lại, đối chiếu bảng của bản thảo, thống kê thư mục",
    "common": "nạp dữ liệu, chạy phương pháp, chấm điểm, độ đo phức hợp protein",
    "data": "dữ liệu chính (niêm phong, kiểm tra bằng manifest)",
    "data_extra": "tập chọn và tập khóa của đợt C (LFR sinh mới)",
    "lib": "cài đặt DOT-CCM (dothac, wom_v1, wom_dot, ccm_tail), wGHAC, độ đo",
    "methods": "một thư mục cho mỗi phương pháp: method.py và run_test*.py",
    "results": "kết quả: raw, scores, timing, ablation, applications, revision, round_c, logs",
    "revision": "đợt sửa: bao đơn điệu, p-value hợp lệ, đợt C (chọn cấu hình, chấm lại, bóc tách v3, thời gian v3)",
    "tests": "kiểm thử pytest và kiểm tra nhanh",
    "timing": "giao thức đo thời gian",
    "tools": "tệp nhị phân: OSLOM, BigCLAM, ClusterONE, khoảng cách vết kín",
}


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=S.ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def mb(n):
    return "%.1f" % (n / 1e6)


def read_json(p):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def statuses(paths):
    c = Counter(read_json(p).get("status", "?") for p in paths)
    return "%d / %d / %d" % (c["ok"], c["timeout"], sum(v for k, v in c.items() if k not in ("ok", "timeout")))


def folder_section(L):
    files = tracked()
    count, size = Counter(), Counter()
    for f in files:
        top = f.split("/", 1)[0] if "/" in f else "(gốc)"
        count[top] += 1
        size[top] += (S.ROOT / f).stat().st_size
    L += ["## Thư mục", "", "Số tệp được git theo dõi và dung lượng trên đĩa.", "",
          "| Thư mục | Số tệp | Dung lượng (MB) | Nội dung |", "|---|---:|---:|---|"]
    for top in sorted(count, key=lambda t: (t != "(gốc)", t)):
        L.append("| `%s` | %d | %s | %s |" % (top, count[top], mb(size[top]), FOLDERS.get(top, "")))
    L += ["| Tổng | %d | %s | |" % (sum(count.values()), mb(sum(size.values()))), ""]


def dataset_section(L):
    from applications import networks
    rows = [(ds, S.DATASETS.get(ds, "")) for ds in ("test1", "test2", "test3")]
    rows += [(datasets.LARGE, "6 mạng LFR có trọng số, N = 5000 (μ_t = μ_w = 0,3)")]
    rows += [(ds, "tập chọn của đợt C" if ds in datasets.TUNE else "tập khóa của đợt C") for ds in datasets.EXTRA_DIRS]
    L += ["## Dữ liệu", "", "| Bộ | Số mạng | Mô tả |", "|---|---:|---|"]
    for ds, text in rows:
        L.append("| `%s` | %d | %s |" % (ds, len(datasets.list_networks(ds)), text))
    L.append("| mạng ứng dụng | %d | %s |" % (len(networks.NETS), ", ".join(networks.NETS)))
    L += ["", "`data/` được niêm phong: mọi tệp phải có trong manifest, không thêm tệp mới.", ""]


def method_section(L):
    L += ["## Phương pháp", "", "| Khóa | Tên | Dùng trọng số |", "|---|---|:---:|"]
    for m, name in S.ALL_METHODS.items():
        text = (S.ROOT / "methods" / m / "method.py").read_text()
        w = re.search(r"^USES_WEIGHTS\s*=\s*(True|False)", text, re.M)
        L.append("| `%s` | %s | %s |" % (m, name, {"True": "có", "False": "không"}.get(w.group(1) if w else "", "?")))
    cfg = json.loads((S.ROOT / "methods" / "proposed" / "config.json").read_text())
    old = json.loads((S.ROOT / "methods" / "proposed" / "config_v2.json").read_text())
    keys = [k for k in cfg if cfg.get(k) != old.get(k)]
    L += ["", "Phương pháp đề xuất dùng `methods/proposed/config.json` (phiên bản %d). Khác với `config_v2.json` "
          "(cấu hình đã công bố) ở: %s." % (cfg["version"], ", ".join("`%s` %s → %s" % (k, old.get(k, "không có"), cfg[k])
                                                                    for k in keys)), ""]


def raw_section(L):
    L += ["## Kết quả lượt chạy chính", "",
          "Mỗi ô: ok / quá giờ / lỗi, đếm trên `results/raw/<bộ>/<phương pháp>/*.json`.", ""]
    sets = sorted(p.name for p in S.RAW.iterdir() if p.is_dir())
    methods = [m for m in S.ALL_METHODS if any((S.RAW / ds / m).is_dir() for ds in sets)]
    L += ["| Phương pháp | " + " | ".join("`%s`" % s for s in sets) + " |", "|---|" + ":---:|" * len(sets)]
    for m in methods:
        cells = [statuses(sorted((S.RAW / ds / m).glob("*.json"))) if (S.RAW / ds / m).is_dir() else "" for ds in sets]
        L.append("| `%s` | %s |" % (m, " | ".join(cells)))
    n_scores = sum(1 for _ in S.SCORES.glob("*/*/*.json"))
    L += ["", "Điểm đã chấm: %d tệp trong `results/scores/`; bảng tổng: `results/scores_all.csv`, `results/SUMMARY.md`."
          % n_scores, ""]


def block(path, pattern="*.json"):
    files = sorted(path.glob(pattern))
    bad = [(p, read_json(p).get("status", "?")) for p in files if read_json(p).get("status") != "ok"]
    return len(files), statuses(files) if files else "-", bad


def other_section(L):
    R = S.RESULTS
    rows, bad = [], []
    for name, path, pattern in (
            ("Đo thời gian v2 (32 mạng)", R / "timing", "*/*/*.json"),
            ("Đo thời gian v2, N = 5000", R / "timing_n5000", "*/*.json"),
            ("Bóc tách v2", R / "ablation", "*/*/*.json"),
            ("Mạng ứng dụng v2, kèm bản nhiễu", R / "applications", "**/*.json"),
            ("Bộ đệm Pha I (đợt sửa)", R / "revision" / "trees", "*/*.json"),
            ("Lưới Pha II trên bộ đệm", R / "revision" / "phase2", "*/*.json"),
            ("Đo thời gian v3", R / "round_c" / "timing", "*/*/*.json"),
            ("Đo thời gian v3, N = 5000", R / "round_c" / "timing_n5000", "*/*.json"),
            ("Bóc tách v3", R / "round_c" / "ablation", "*/*/*.json"),
            ("Mạng ứng dụng v3, kèm bản nhiễu", R / "round_c" / "applications", "**/*.json")):
        n, st, b = block(path, pattern)
        rows.append((name, path.relative_to(S.ROOT), n, st))
        bad += b
    with (R / "round_c" / "rescore" / "runs.csv").open() as fh:
        rescore = sum(1 for _ in csv.reader(fh)) - 1
    L += ["## Các khối kết quả khác", "", "| Khối | Thư mục | Số tệp | ok / quá giờ / lỗi |", "|---|---|---:|:---:|"]
    for name, path, n, st in rows:
        L.append("| %s | `%s` | %d | %s |" % (name, path, n, st))
    L += ["| Chấm lại hai quy ước, MMR/Acc/Frac | `results/round_c/rescore/runs.csv` | %d dòng | |" % rescore, ""]
    notes = {"results/applications/brain_coactivation/wghac.json":
             "wGHAC hết bộ nhớ khi cấp phát ma trận khoảng cách giữa 106 180 clique"}
    if bad:
        L += ["Lượt không ok:", ""]
        for p, st in bad:
            rel = str(p.relative_to(S.ROOT))
            L.append("- `%s` (%s)%s" % (rel, st, ": " + notes[rel] if rel in notes else ""))
        L.append("")
    L += [
          "Bảng tổng hợp: `results/round_c/REPORT.md`, `results/round_c/timing_v3.md`, "
          "`results/round_c/ablation/SUMMARY.md`, `results/round_c/applications/SUMMARY.md`.", ""]


def tests_section(L):
    tests = sorted((S.ROOT / "tests").glob("test_*.py"))
    n = sum(len(re.findall(r"^def test_", p.read_text(), re.M)) for p in tests)
    L += ["## Kiểm thử", "", "%d hàm kiểm thử trong %d tệp (%s); kiểm tra nhanh: `tests/smoke.py`." % (
        n, len(tests), ", ".join("`%s`" % p.name for p in tests)), ""]


def main():
    L = ["# Thống kê thư mục thực nghiệm", "",
         "Sinh bằng `python3 audit/inventory.py`, cập nhật %s." % time.strftime("%Y-%m-%d %H:%M"), ""]
    folder_section(L)
    dataset_section(L)
    method_section(L)
    raw_section(L)
    other_section(L)
    tests_section(L)
    OUT.write_text("\n".join(L))
    print("Đã ghi %s" % OUT)


if __name__ == "__main__":
    main()
