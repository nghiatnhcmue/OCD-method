# Viết results/SUMMARY.xlsx; các bảng tổng hợp là công thức COUNTIFS/AVERAGEIFS trên trang Data và
# Timing_data.

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

FONT = "Arial"
DATA_COLS = [
    ("dataset", None), ("net_id", None), ("topology_id", None), ("regime", None), ("mu", "0.0"), ("mu_w", "0.0"),
    ("on", "0"), ("om", "0"), ("replicate", "0"), ("method", None), ("method_name", None), ("status", None),
    ("seconds", "0.0"), ("n_communities", "0"), ("max_size", "0"), ("coverage", "0.000"), ("mean_memberships", "0.000"),
    ("onmi_mgh", "0.000"), ("onmi_lfk", "0.000"), ("onf1", "0.000"), ("f1", "0.000"), ("omega", "0.000"),
    ("P_O", "0.000"), ("R_O", "0.000"), ("P_mem", "0.000"), ("R_mem", "0.000"), ("labeled_onmi_mgh", "0.000"),
    ("labeled_onmi_lfk", "0.000"), ("labeled_f1", "0.000"), ("labeled_omega", "0.000"), ("labeled_onf1", "0.000"),
    ("labeled_coverage", "0.000"), ("common_set", "0"), ("source", None)]
TIMING_COLS = [("dataset", None), ("net_id", None), ("method", None), ("method_name", None), ("status", None),
               ("wall_seconds", "0.00"), ("cpu_seconds", "0.00"), ("cores", None), ("n_communities", "0"),
               ("common_set", "0"), ("finished", None)]
METRICS = [("onmi_mgh", "ONMI"), ("onmi_lfk", "ONMI-LFK"), ("onf1", "ONF1"), ("f1", "F1"), ("omega", "Omega")]
LABELED = [("labeled_onmi_mgh", "ONMI (đỉnh có nhãn)"), ("labeled_f1", "F1 (đỉnh có nhãn)"),
           ("labeled_omega", "Omega (đỉnh có nhãn)"), ("labeled_coverage", "Độ phủ đỉnh có nhãn")]
QUOTE = chr(34)


def label(dataset):
    return S.DATASETS[dataset].split(":")[0]


def q(v):
    return QUOTE + v + QUOTE if isinstance(v, str) else repr(v)


def _value(v):
    if v is None or v == "" or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def _mark_common_set(rows):
    ok = {}
    for r in rows:
        if r["status"] == "ok":
            ok.setdefault((r["dataset"], r["net_id"]), set()).add(r["method"])
    for r in rows:
        r["common_set"] = 1 if ok.get((r["dataset"], r["net_id"]), set()) >= set(S.METHODS) else 0


class _Style:
    def __init__(self):
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        self.normal = Font(name=FONT, size=10)
        self.bold = Font(name=FONT, size=10, bold=True)
        self.title = Font(name=FONT, size=12, bold=True)
        self.head_font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        self.head_fill = PatternFill("solid", fgColor="1F4E78")
        self.input_fill = PatternFill("solid", fgColor="FFF2CC")
        self.border = Border(bottom=Side(style="thin", color="BFBFBF"))
        self.center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    def text(self, ws, ref, text, font=None):
        ws[ref] = text
        ws[ref].font = font or self.normal

    def header(self, ws, row, col, labels):
        for j, lb in enumerate(labels):
            c = ws.cell(row=row, column=col + j, value=lb)
            c.font, c.fill, c.alignment = self.head_font, self.head_fill, self.center
        ws.row_dimensions[row].height = 30

    def cell(self, ws, row, col, val, fmt=None, font=None):
        c = ws.cell(row=row, column=col, value=val)
        c.font, c.border = font or self.normal, self.border
        if fmt:
            c.number_format = fmt
        return c

    @staticmethod
    def color_scale(ws, ref):
        from openpyxl.formatting.rule import ColorScaleRule
        ws.conditional_formatting.add(ref, ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile",
                                                          mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))


def _table_sheet(wb, st, title, cols, rows, freeze):
    from openpyxl.utils import get_column_letter as L
    ws = wb.create_sheet(title)
    st.header(ws, 1, 1, [c for c, _ in cols])
    letter = {c: L(j) for j, (c, _) in enumerate(cols, 1)}
    for i, r in enumerate(rows, 2):
        for j, (c, fmt) in enumerate(cols, 1):
            cell = ws.cell(row=i, column=j, value=_value(r.get(c)))
            cell.font = st.normal
            if fmt:
                cell.number_format = fmt
    n = max(len(rows) + 1, 2)
    ws.freeze_panes = freeze
    ws.auto_filter.ref = "A1:%s%d" % (L(len(cols)), n)
    for c in letter:
        ws.column_dimensions[letter[c]].width = 40 if c in ("net_id", "source") else (20 if c == "method_name" else 12)
    return lambda c: "%s!$%s$2:$%s$%d" % (title, letter[c], letter[c], n)


def _completion_sheet(wb, st, R, totals):
    from openpyxl.utils import get_column_letter as L
    ws = wb.create_sheet("Completion")
    st.text(ws, "A1", "Mức độ hoàn thành: số lượt chạy theo trạng thái", st.title)
    st.cell(ws, 3, 2, "Số mạng của bộ", font=st.bold)
    st.header(ws, 4, 1, ["Mã", "Phương pháp"] + sum([[label(ds) + ": ok", "quá giờ", "lỗi", "chưa chạy"] for ds in S.DATASETS], []))
    for b, ds in enumerate(S.DATASETS):
        st.cell(ws, 3, 3 + 4 * b, totals[ds], "0", st.bold).fill = st.input_fill
    for i, m in enumerate(S.METHODS, 5):
        st.cell(ws, i, 1, m)
        st.cell(ws, i, 2, S.METHODS[m], font=st.bold)
        for b, ds in enumerate(S.DATASETS):
            c0 = 3 + 4 * b
            for k, status in enumerate(("ok", "timeout", "error")):
                st.cell(ws, i, c0 + k, "=COUNTIFS(%s,%s,%s,$A%d,%s,%s)"
                        % (R("dataset"), q(ds), R("method"), i, R("status"), q(status)), "0")
            st.cell(ws, i, c0 + 3, "=%s$3-SUM(%s%d:%s%d)" % (L(c0), L(c0), i, L(c0 + 2), i), "0")
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 22
    for j in range(3, 3 + 4 * len(S.DATASETS)):
        ws.column_dimensions[L(j)].width = 11
    ws.freeze_panes = "C5"


def _means_sheet(wb, st, R, name, common_only):
    from openpyxl.utils import get_column_letter as L
    ws = wb.create_sheet(name)
    st.text(ws, "A1", "Điểm trung bình trên " + ("các mạng mà cả 9 phương pháp đều ok" if common_only
                                               else "các lượt ok của từng phương pháp"), st.title)
    st.text(ws, "A2", "Ô trống: không có lượt ok, hoặc độ đo không xác định (ONF1 khi nhãn chuẩn không có đỉnh chồng lấn).")
    row = 4
    for ds in S.DATASETS:
        st.text(ws, "A%d" % row, S.DATASETS[ds], st.bold)
        row += 1
        metrics = METRICS + (LABELED if ds == "test3" else [])
        st.header(ws, row, 1, ["Mã", "Phương pháp", "Số mạng"] + [t for _, t in metrics] + ["Hạng ONMI"])
        r0, r1 = row + 1, row + len(S.METHODS)
        for i, m in enumerate(S.METHODS, r0):
            cond = "%s,%s,%s,$A%d,%s,%s" % (R("dataset"), q(ds), R("method"), i, R("status"), q("ok"))
            if common_only:
                cond += ",%s,1" % R("common_set")
            st.cell(ws, i, 1, m)
            st.cell(ws, i, 2, S.METHODS[m], font=st.bold)
            st.cell(ws, i, 3, "=COUNTIFS(%s)" % cond, "0")
            for j, (col, _) in enumerate(metrics, 4):
                st.cell(ws, i, j, "=IFERROR(AVERAGEIFS(%s,%s),%s)" % (R(col), cond, q("")), "0.000")
            st.cell(ws, i, 4 + len(metrics), "=IF(ISNUMBER(D%d),RANK(D%d,$D$%d:$D$%d),%s)" % (i, i, r0, r1, q("")), "0")
        for j in range(4, 4 + len(metrics)):
            st.color_scale(ws, "%s%d:%s%d" % (L(j), r0, L(j), r1))
        row = r1 + 2
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 22
    for j in range(3, 15):
        ws.column_dimensions[L(j)].width = 12


def _by_mu_sheet(wb, st, R, rows):
    from openpyxl.utils import get_column_letter as L
    from common import datasets
    methods = list(S.METHODS)
    nets = datasets.list_networks()
    ws = wb.create_sheet("By_mu")
    st.text(ws, "A1", "ONMI trung bình theo mức nhiễu và chế độ trọng số (các lượt ok)", st.title)

    def table(row, title, first, groups):
        st.text(ws, "A%d" % row, title, st.bold)
        st.header(ws, row + 1, 1, [first] + [S.METHODS[m] for m in methods] + ["Số mạng"])
        for j, m in enumerate(methods, 2):
            st.cell(ws, row + 2, j, m)
        ws.row_dimensions[row + 2].hidden = True
        for i, (name, conds) in enumerate(groups, row + 3):
            st.cell(ws, i, 1, name, font=st.bold)
            cond = ",".join("%s,%s" % (R(c), q(v)) for c, v in conds)
            for j in range(2, 2 + len(methods)):
                st.cell(ws, i, j, "=IFERROR(AVERAGEIFS(%s,%s,%s,%s$%d,%s,%s),%s)"
                        % (R("onmi_mgh"), cond, R("method"), L(j), row + 2, R("status"), q("ok"), q("")), "0.000")
            n = sum(all(str(d[c]) == str(v) for c, v in conds) for d in nets)
            st.cell(ws, i, 2 + len(methods), n, "0").fill = st.input_fill
        st.color_scale(ws, "B%d:%s%d" % (row + 3, L(1 + len(methods)), row + 2 + len(groups)))
        return row + 4 + len(groups)

    mu1 = sorted({r["mu"] for r in rows if r["dataset"] == "test1" and r["mu"] not in ("", None)})
    mu2 = sorted({(r["mu"], r["mu_w"]) for r in rows if r["dataset"] == "test2" and r["mu"] not in ("", None)})
    row = table(3, "Kiểm tra 1, theo μ", "μ", [("%g" % m, [("dataset", "test1"), ("mu", m)]) for m in mu1])
    row = table(row, "Kiểm tra 1, theo chế độ trọng số", "Chế độ",
                [(reg, [("dataset", "test1"), ("regime", reg)]) for reg in ("INJ", "FLAT", "PERM")])
    table(row, "Kiểm tra 2, theo (μ_t, μ_w)", "μ_t / μ_w",
          [("%g / %g" % (a, b), [("dataset", "test2"), ("mu", a), ("mu_w", b)]) for a, b in mu2])
    ws.column_dimensions["A"].width = 16
    for j in range(2, 3 + len(methods)):
        ws.column_dimensions[L(j)].width = 13


def _test3_sheet(wb, st, R):
    from openpyxl.utils import get_column_letter as L
    from common import datasets
    nets = [d["net_id"] for d in datasets.list_networks("test3")]
    ws = wb.create_sheet("Test3")
    st.text(ws, "A1", "Kiểm tra 3: ONMI từng mạng protein", st.title)
    row = 3
    for col, title in (("onmi_mgh", "ONMI trên toàn mạng"), ("labeled_onmi_mgh", "ONMI trên các đỉnh có nhãn CYC2008")):
        st.text(ws, "A%d" % row, title, st.bold)
        st.header(ws, row + 1, 1, ["Mã", "Phương pháp"] + nets + ["Trung bình"])
        for i, m in enumerate(S.METHODS, row + 2):
            st.cell(ws, i, 1, m)
            st.cell(ws, i, 2, S.METHODS[m], font=st.bold)
            for j, n in enumerate(nets, 3):
                st.cell(ws, i, j, "=IFERROR(AVERAGEIFS(%s,%s,%s,%s,%s,%s,$A%d,%s,%s),%s)"
                        % (R(col), R("dataset"), q("test3"), R("net_id"), q(n), R("method"), i, R("status"), q("ok"), q("")),
                        "0.000")
            a, b = L(3), L(2 + len(nets))
            st.cell(ws, i, 3 + len(nets), "=IF(COUNT(%s%d:%s%d)=0,%s,AVERAGE(%s%d:%s%d))" % (a, i, b, i, q(""), a, i, b, i), "0.000")
        st.color_scale(ws, "C%d:%s%d" % (row + 2, L(3 + len(nets)), row + 1 + len(S.METHODS)))
        row += len(S.METHODS) + 4
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 22
    for j in range(3, 4 + len(nets)):
        ws.column_dimensions[L(j)].width = 18


def load_timing():
    rows = []
    for p in sorted((S.RESULTS / "timing").glob("*/*/*.json")):
        d = json.loads(p.read_text())
        d["method_name"] = S.METHODS.get(d.get("method"), d.get("method"))
        rows.append(d)
    return rows


def _timing_sheet(wb, st, R):
    from openpyxl.utils import get_column_letter as L
    from timing.subset import timing_subset
    subset = timing_subset()
    ws = wb.create_sheet("Timing")
    st.text(ws, "A1", "Thời gian chạy trên 32 mạng đại diện, đo riêng theo quy trình cố định (timing/run_timing.py)", st.title)
    st.text(ws, "A2", "Trung bình trên các lượt ok. Cùng tập mạng: các mạng mà cả 9 phương pháp đều đo xong; bội số so với "
            "phương pháp đề xuất tính trên tập này.")
    row = 4
    for ds in S.DATASETS:
        st.text(ws, "A%d" % row, "%s: %d mạng" % (label(ds), sum(1 for d in subset if d["dataset"] == ds)), st.bold)
        st.header(ws, row + 1, 1, ["Mã", "Phương pháp", "Số lượt ok", "Quá giờ", "Lỗi", "Giây thực TB", "Giây CPU TB",
                                   "Giây thực lớn nhất", "Số mạng cùng tập", "Giây thực TB (cùng tập mạng)",
                                   "Bội số so với phương pháp đề xuất (cùng tập mạng)"])
        r0 = row + 2
        for i, m in enumerate(S.METHODS, r0):
            d = "%s,%s,%s,$A%d" % (R("dataset"), q(ds), R("method"), i)
            ok = "%s,%s,%s" % (d, R("status"), q("ok"))
            common = "%s,%s,1" % (ok, R("common_set"))
            st.cell(ws, i, 1, m)
            st.cell(ws, i, 2, S.METHODS[m], font=st.bold)
            st.cell(ws, i, 3, "=COUNTIFS(%s)" % ok, "0")
            st.cell(ws, i, 4, "=COUNTIFS(%s,%s,%s)" % (d, R("status"), q("timeout")), "0")
            st.cell(ws, i, 5, "=COUNTIFS(%s,%s,%s)" % (d, R("status"), q("error")), "0")
            st.cell(ws, i, 6, "=IFERROR(AVERAGEIFS(%s,%s),%s)" % (R("wall_seconds"), ok, q("")), "0.0")
            st.cell(ws, i, 7, "=IFERROR(AVERAGEIFS(%s,%s),%s)" % (R("cpu_seconds"), ok, q("")), "0.0")
            st.cell(ws, i, 8, "=IF(C%d=0,%s,_xlfn.MAXIFS(%s,%s))" % (i, q(""), R("wall_seconds"), ok), "0.0")
            st.cell(ws, i, 9, "=COUNTIFS(%s)" % common, "0")
            st.cell(ws, i, 10, "=IFERROR(AVERAGEIFS(%s,%s),%s)" % (R("wall_seconds"), common, q("")), "0.0")
            st.cell(ws, i, 11, "=IF(AND(ISNUMBER(J%d),ISNUMBER($J$%d)),J%d/$J$%d,%s)" % (i, r0, i, r0, q("")), "0.00")
        row = r0 + len(S.METHODS) + 1
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 22
    for j in range(3, 12):
        ws.column_dimensions[L(j)].width = 14


def _guide_sheet(wb, st, n_rows):
    ws = wb.create_sheet("Guide", 0)
    T, B = st.normal, st.bold
    lines = [
        ("Tổng hợp kết quả thực nghiệm", st.title),
        ("Cập nhật %s; %d lượt chạy trong Data. Tệp do common/summarize.py sinh lại, không sửa tay."
         % (time.strftime("%Y-%m-%d %H:%M"), n_rows), T),
        ("", T), ("Các trang", B),
        ("Data: một dòng cho một lượt chạy (một phương pháp trên một mạng). Timing_data: một dòng cho một lượt đo thời gian.", T),
        ("Completion: số lượt ok, quá giờ, lỗi, chưa chạy. Summary: trung bình trên các lượt ok; Common_set: trung bình trên "
         "các mạng mà cả 9 phương pháp đều ok.", T),
        ("By_mu: ONMI theo mức nhiễu và chế độ trọng số. Test3: ONMI từng mạng protein. Timing: thời gian chạy đo riêng; "
         "dùng trang này khi so thời gian.", T),
        ("", T), ("Bộ dữ liệu", B)]
    lines += [(S.DATASETS[ds], T) for ds in S.DATASETS]
    lines += [
        ("", T), ("Cột", B),
        ("status: ok; timeout (vượt %d giây cho một mạng); error (lỗi khi chạy)." % S.TIME_LIMIT, T),
        ("onmi_mgh: ONMI bản McDaid-Greene-Hurley (độ đo chính). onmi_lfk: ONMI bản Lancichinetti-Fortunato-Kertész.", T),
        ("onf1: F1 trên tập đỉnh chồng lấn; P_O, R_O: độ chính xác, độ phủ của tập đó. Để trống khi nhãn chuẩn không có "
         "đỉnh chồng lấn (on = 0).", T),
        ("f1: F1 trung bình hai phía (Yang-Leskovec). omega: chỉ số Omega; đỉnh không thuộc cộng đồng nào coi là cộng đồng "
         "một đỉnh.", T),
        ("P_mem, R_mem: độ chính xác, độ phủ của các mức thuộc sau khi ghép một-một cộng đồng theo Dice.", T),
        ("labeled_*: Kiểm tra 3, tính trên đồ thị con gồm các đỉnh có nhãn CYC2008, mỗi cộng đồng chiếu lên tập đỉnh đó.", T),
        ("coverage: tỉ lệ đỉnh thuộc ít nhất một cộng đồng. mean_memberships: số cộng đồng trung bình của một đỉnh (tính "
         "trên mọi đỉnh). max_size: cỡ cộng đồng lớn nhất.", T),
        ("seconds: thời gian ở lượt chạy chính, khi máy chạy nhiều tiến trình cùng lúc; không dùng để so thời gian.", T),
        ("common_set: 1 nếu cả 9 phương pháp đều ok trên mạng đó. source: Thuc_Nghiem = chạy bằng bộ mã này; imported = "
         "đầu ra của lượt chạy cũ (mã phương pháp không đổi), chấm lại bằng bộ mã này.", T),
        ("", T), ("Lưu ý", B),
        ("SLPA không dùng trọng số; BigCLAM chỉ dùng trọng số khi ước lượng số cộng đồng. Infomap cho phân hoạch. ASLPAw "
         "không tất định giữa các lần chạy.", T)]
    for i, (text, font) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = font
    ws.column_dimensions["A"].width = 140


def write_workbook(rows, path=None):
    from openpyxl import Workbook
    from common import datasets
    path = Path(path or S.RESULTS / "SUMMARY.xlsx")
    rows = [dict(r) for r in rows]
    _mark_common_set(rows)
    timing_rows = [dict(r) for r in load_timing()]
    _mark_common_set(timing_rows)
    st = _Style()
    wb = Workbook()
    wb.remove(wb.active)
    wb.calculation.fullCalcOnLoad = True
    R = _table_sheet(wb, st, "Data", DATA_COLS, rows, "C2")
    _completion_sheet(wb, st, R, {ds: len(datasets.list_networks(ds)) for ds in S.DATASETS})
    _means_sheet(wb, st, R, "Summary", False)
    _means_sheet(wb, st, R, "Common_set", True)
    _by_mu_sheet(wb, st, R, rows)
    _test3_sheet(wb, st, R)
    RT = _table_sheet(wb, st, "Timing_data", TIMING_COLS, timing_rows, "B2")
    _timing_sheet(wb, st, RT)
    _guide_sheet(wb, st, len(rows))
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = ws.title in ("Data", "Timing_data")
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


if __name__ == "__main__":
    from common import summarize
    print("Đã ghi", write_workbook(summarize.load_rows()))
