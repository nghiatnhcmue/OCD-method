# OCD-method

Mã thực nghiệm của luận văn "Phát hiện cộng đồng chồng lấp trong mạng dựa trên phân cụm". Phương pháp đề xuất là
DOT-CCM: phát hiện cộng đồng chồng lấn trên mạng có trọng số, so với wGHAC (phương pháp gốc) và 8 phương pháp khác trên
162 mạng chính, 6 mạng N = 5000 và 3 mạng ứng dụng.

## Phương pháp đề xuất

DOT-CCM có hai pha. Pha I dựng cây gộp từ hồ sơ PageRank cá nhân hóa với khoảng cách vận tải tối ưu, rồi chọn lõi cộng
đồng trên cây. Pha II thêm mức thuộc ở biên bằng kiểm định so với mô hình cấu hình liên tục (CCM).

| Cấu hình | Tệp | Dùng cho |
|---|---|---|
| v3 (mặc định) | `methods/proposed/config.json` | phương pháp chính: bao đơn điệu cho độ cao gộp; p-value compound Poisson (đệ quy Panjer) ở Pha II; Benjamini–Hochberg theo từng đỉnh trên các lõi không chứa đỉnh, q = 0,05. Chọn trên tập chọn, khóa ở tag `v3-frozen` |
| v2 | `methods/proposed/config_v2.json` | cấu hình của bản thảo trước (xấp xỉ chuẩn, q = 0,001); giữ để tái lập số cũ |

Mã: `methods/proposed/algorithm.py`, `lib/methods/dothac.py`, `lib/wom_v1.py`, `lib/wom_dot.py`, `lib/ccm_tail.py`.

## Thư mục

Thống kê đầy đủ (số tệp, số mạng, số lượt chạy theo từng khối kết quả): `results/INVENTORY.md`, sinh bằng
`python3 audit/inventory.py`.

| Thư mục | Nội dung |
|---|---|
| `methods/` | một thư mục cho mỗi phương pháp |
| `lib/` | cài đặt DOT-CCM, wGHAC và các độ đo |
| `common/` | nạp dữ liệu, chạy phương pháp, chấm điểm |
| `data/`, `data_extra/` | dữ liệu chính (niêm phong); tập chọn và tập khóa của đợt C |
| `timing/`, `ablation/`, `applications/` | đo thời gian, bóc tách v2, mạng ứng dụng |
| `revision/` | đợt sửa và đợt C: bộ đệm Pha I, lưới Pha II, chấm lại, bóc tách v3, thời gian v3 |
| `audit/` | kiểm toán và thống kê thư mục |
| `results/` | kết quả và nhật ký |
| `tests/` | kiểm thử |

## Môi trường

Ubuntu 22.04 (WSL2), Python 3.10.12, Java 17 (cho ClusterONE), gói `libgomp1` (cho các tệp trong `tools/`).

```
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

## Chạy

```
bash run_all.sh
python3 methods/<phương pháp>/run_test<k>.py [net_id ...] [--rerun]
python3 timing/run_timing.py [--set n5000]
python3 timing/score_n5000.py
python3 ablation/run.py
python3 ablation/summarize.py
python3 applications/prepare.py
python3 applications/run.py
python3 applications/summarize.py
```

Kết quả: `results/SUMMARY.md`, `results/ablation/SUMMARY.md`, `results/applications/SUMMARY.md`. Hai lệnh `ablation/`
chạy cấu hình v2 của bản thảo trước.

## Đợt C: chọn cấu hình v3 và đo lại

Giao thức: `results/round_c/PROTOCOL.md`. Kết quả chính: `results/round_c/REPORT.md`.

```
python3 revision/gen_extra.py tune && python3 revision/gen_extra.py locked   # sinh data_extra/ (đã có, không sinh lại)
python3 revision/trees.py                                  # bộ đệm Pha I cho 162 mạng, N = 5000, mạng ứng dụng
python3 revision/trees.py --sets tune1 tune2               # tập chọn
python3 revision/phase2.py                                 # lưới Pha II trên bộ đệm
python3 revision/phase2.py --sets tune1 tune2
python3 revision/trees.py --sets lock1 lock2               # tập khóa, chạy một lần
python3 revision/phase2.py --sets lock1 lock2 --configs cp_node_0.05
python3 -c "from common.runner import run_dataset; run_dataset('lock1', 'oslom', [])"   # OSLOM trên tập khóa; lock2 tương tự
bash revision/true_k.sh bigclam_k 2                       # BigCLAM với K thật trên 162 mạng
bash revision/true_k.sh danmf_k 2                         # DANMF với K thật
python3 revision/rescore_c.py --v3-config cp_node_0.05     # hai quy ước cho đỉnh không được gán, MMR/Acc/Frac
python3 revision/round_c_report.py                         # results/round_c/REPORT.md
```

Đo v3 theo cùng giao thức với v2. `RUN_TAG=round_c` ghi sang `results/round_c/`, không đụng số đo cũ.

```
RUN_TAG=round_c python3 timing/run_timing.py --set all --methods proposed   # 32 mạng và 6 mạng N = 5000
RUN_TAG=round_c python3 applications/run.py --methods proposed              # 3 mạng ứng dụng, 10 bản bỏ 5% cạnh mỗi mạng
python3 revision/ablation_v3.py                                             # bóc tách v3, 158 mạng
python3 revision/ablation_v3.py summary                                     # results/round_c/ablation/SUMMARY.md
python3 revision/timing_v3.py                                               # results/round_c/timing_v3.md
RUN_TAG=round_c python3 applications/summarize.py                           # results/round_c/applications/SUMMARY.md
```

## Kiểm tra nhanh

```
python3 tests/make_smoke_fixture.py   # chỉ cần khi tests/fixtures/ chưa có
python3 tests/smoke.py                # 9 phương pháp trên một mạng LFR N = 200, kèm so phiên bản gói
python3 -m pytest -q tests
```

## Dữ liệu

- `data/`: 108 mạng LFR, 50 mạng LFR có trọng số, 4 mạng protein của nấm men (nhãn CYC2008), 6 mạng N = 5000.
- `data_extra/`: 52 mạng tập chọn và 52 mạng tập khóa, sinh bằng cùng bộ sinh với Kiểm tra 1 và 2, không dùng chung hạt
  giống.
- `applications/data/`: nơ-ron C. elegans (Varshney và cộng sự, 2011), đồng tác giả khoa học mạng (Newman, 2006),
  vùng não người (Crossley và cộng sự, 2013).

## Nguồn

`lib/wghac/` và tệp nhị phân khoảng cách CT trong `tools/` dựa trên mã của Prokop, Dráždilová và Platoš (PLoS ONE,
2024, doi:10.1371/journal.pone.0312596). Nguồn tải dữ liệu và công cụ: `tools/SOURCES.tsv`, `applications/data/SOURCES.tsv`.
