# Thống kê thư mục thực nghiệm

Sinh bằng `python3 audit/inventory.py`, cập nhật 2026-11-14 01:33.

## Thư mục

Số tệp được git theo dõi và dung lượng trên đĩa.

| Thư mục | Số tệp | Dung lượng (MB) | Nội dung |
|---|---:|---:|---|
| `(gốc)` | 5 | 0.0 | README, requirements.txt, run_all.sh, settings.py |
| `ablation` | 4 | 0.0 | bóc tách v2 đã công bố (ablation/run.py, variants.py, summarize.py) |
| `applications` | 17 | 1.5 | ba mạng ứng dụng: chuẩn bị dữ liệu, chạy, tổng hợp, độ ổn định |
| `audit` | 8 | 0.0 | kiểm toán: chạy lại, đối chiếu bảng của bản thảo, thống kê thư mục |
| `common` | 10 | 0.0 | nạp dữ liệu, chạy phương pháp, chấm điểm, độ đo phức hợp protein |
| `data` | 495 | 119.8 | dữ liệu chính (niêm phong, kiểm tra bằng manifest) |
| `data_extra` | 344 | 61.4 | tập chọn và tập khóa của đợt C (LFR sinh mới) |
| `lib` | 19 | 0.1 | cài đặt DOT-CCM (dothac, wom_v1, wom_dot, ccm_tail), wGHAC, độ đo |
| `methods` | 42 | 0.0 | một thư mục cho mỗi phương pháp: method.py và run_test*.py |
| `results` | 9655 | 150.1 | kết quả: raw, scores, timing, ablation, applications, revision, round_c, logs |
| `revision` | 14 | 0.1 | đợt sửa: bao đơn điệu, p-value hợp lệ, đợt C (chọn cấu hình, chấm lại, bóc tách v3, thời gian v3) |
| `tests` | 9 | 0.0 | kiểm thử pytest và kiểm tra nhanh |
| `timing` | 4 | 0.0 | giao thức đo thời gian |
| `tools` | 19 | 14.9 | tệp nhị phân: OSLOM, BigCLAM, ClusterONE, khoảng cách vết kín |
| Tổng | 10645 | 348.2 | |

## Dữ liệu

| Bộ | Số mạng | Mô tả |
|---|---:|---|
| `test1` | 108 | Kiểm tra 1: 108 mạng LFR (N = 1000), 36 cấu trúc x 3 chế độ trọng số INJ/FLAT/PERM |
| `test2` | 50 | Kiểm tra 2: 50 mạng LFR có trọng số của Lancichinetti-Fortunato (N = 1000) |
| `test3` | 4 | Kiểm tra 3: 4 mạng tương tác protein của nấm men, nhãn phức hợp CYC2008 |
| `test2_n5000` | 6 | 6 mạng LFR có trọng số, N = 5000 (μ_t = μ_w = 0,3) |
| `tune1` | 27 | tập chọn của đợt C |
| `tune2` | 25 | tập chọn của đợt C |
| `lock1` | 27 | tập khóa của đợt C |
| `lock2` | 25 | tập khóa của đợt C |
| mạng ứng dụng | 3 | celegans_varshney, netscience, brain_coactivation |

`data/` được niêm phong: mọi tệp phải có trong manifest, không thêm tệp mới.

## Phương pháp

| Khóa | Tên | Dùng trọng số |
|---|---|:---:|
| `proposed` | Phương pháp đề xuất | có |
| `wghac` | wGHAC | có |
| `oslom` | OSLOM | có |
| `slpa` | SLPA | không |
| `infomap` | Infomap | có |
| `bigclam` | BigCLAM | không |
| `danmf` | DANMF | có |
| `clusterone` | ClusterONE | có |
| `aslpaw` | ASLPAw | có |
| `bigclam_k` | BigCLAM (K thật) | không |
| `danmf_k` | DANMF (K thật) | có |
| `aslpaw_seeded` | ASLPAw (có seed) | có |

Phương pháp đề xuất dùng `methods/proposed/config.json` (phiên bản 3). Khác với `config_v2.json` (cấu hình đã công bố) ở: `version` 2 → 3, `monotone_heights` False → True, `q_bh` 0.001 → 0.05, `phase2_pvalue` normal → cpoisson, `phase2_family` node_all → node.

## Kết quả lượt chạy chính

Mỗi ô: ok / quá giờ / lỗi, đếm trên `results/raw/<bộ>/<phương pháp>/*.json`.

| Phương pháp | `lock1` | `lock2` | `test1` | `test2` | `test3` |
|---|:---:|:---:|:---:|:---:|:---:|
| `proposed` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `wghac` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `oslom` | 27 / 0 / 0 | 25 / 0 / 0 | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `slpa` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `infomap` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `bigclam` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `danmf` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `clusterone` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `aslpaw` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `bigclam_k` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |
| `danmf_k` |  |  | 108 / 0 / 0 | 50 / 0 / 0 | 4 / 0 / 0 |

Điểm đã chấm: 1834 tệp trong `results/scores/`; bảng tổng: `results/scores_all.csv`, `results/SUMMARY.md`.

## Các khối kết quả khác

| Khối | Thư mục | Số tệp | ok / quá giờ / lỗi |
|---|---|---:|:---:|
| Đo thời gian v2 (32 mạng) | `results/timing` | 288 | 288 / 0 / 0 |
| Đo thời gian v2, N = 5000 | `results/timing_n5000` | 48 | 48 / 0 / 0 |
| Bóc tách v2 | `results/ablation` | 808 | 808 / 0 / 0 |
| Mạng ứng dụng v2, kèm bản nhiễu | `results/applications` | 56 | 55 / 0 / 1 |
| Bộ đệm Pha I (đợt sửa) | `results/revision/trees` | 275 | 275 / 0 / 0 |
| Lưới Pha II trên bộ đệm | `results/revision/phase2` | 275 | 275 / 0 / 0 |
| Đo thời gian v3 | `results/round_c/timing` | 32 | 32 / 0 / 0 |
| Đo thời gian v3, N = 5000 | `results/round_c/timing_n5000` | 6 | 6 / 0 / 0 |
| Bóc tách v3 | `results/round_c/ablation` | 484 | 484 / 0 / 0 |
| Mạng ứng dụng v3, kèm bản nhiễu | `results/round_c/applications` | 33 | 33 / 0 / 0 |
| Chấm lại hai quy ước, MMR/Acc/Frac | `results/round_c/rescore/runs.csv` | 3888 dòng | |

Lượt không ok:

- `results/applications/brain_coactivation/wghac.json` (error): wGHAC hết bộ nhớ khi cấp phát ma trận khoảng cách giữa 106 180 clique

Bảng tổng hợp: `results/round_c/REPORT.md`, `results/round_c/timing_v3.md`, `results/round_c/ablation/SUMMARY.md`, `results/round_c/applications/SUMMARY.md`.

## Kiểm thử

22 hàm kiểm thử trong 4 tệp (`test_complex_metrics.py`, `test_heights.py`, `test_metrics.py`, `test_pvalues.py`); kiểm tra nhanh: `tests/smoke.py`.
