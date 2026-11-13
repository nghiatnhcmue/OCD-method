# Thời gian DOT-CCM v3 theo quy trình đo

Cập nhật 2026-11-13 13:23. v3: `results/round_c/timing*` (đo lại, `RUN_TAG=round_c python3 timing/run_timing.py --set all --methods proposed`). v2 và wGHAC: số đã lưu trong `results/timing*`. Cùng quy trình: cặp nhân gắn bằng `taskset`, 5 tiến trình, `CLOCK_MONOTONIC_RAW`, mỗi lượt đo một lần.

| Bộ | v2 (s) | v3 (s) | v3 / v2 | wGHAC (s) | wGHAC / v3 | Pha II v2 (s) | Pha II v3 (s) | Số mạng v3 |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| Kiểm tra 1 (18 mạng) | 811 | 779 | 0.96 | 2,319 | 2.98 | 4.0 | 9.5 | 18 |
| Kiểm tra 2 (10 mạng) | 855 | 861 | 1.01 | 3,111 | 3.61 | 3.8 | 13.7 | 10 |
| Collins 2007 | 470 | 417 | 0.89 | 16,921 | 40.63 | 5.7 | 8.1 | 1 |
| Gavin 2006 | 1,090 | 933 | 0.86 | 711 | 0.76 | 12.8 | 7.2 | 1 |
| Krogan Core | 2,481 | 2,476 | 1.00 | 1,481 | 0.60 | 22.7 | 6.2 | 1 |
| Krogan Ext | 5,866 | 5,790 | 0.99 | 9,342 | 1.61 | 40.3 | 14.3 | 1 |

Trung vị trên các mạng của bộ (chỉ mạng có cả hai lượt v2 và v3). Pha II: `info.step_seconds.F_phase2`.

## N = 5000

| Mạng | v2 (s) | v3 (s) | v3 / v2 | Pha II v2 (s) | Pha II v3 (s) | RSS v3 (GB) |
|---|---:|---:|---:|---:|---:|---:|
| on0_omx_seed1 | 3,185 | 3,681 | 1.16 | 41.9 | 118.5 | 3.71 |
| on0_omx_seed2 | 3,283 | 3,495 | 1.06 | 51.5 | 112.3 | 3.67 |
| on0_omx_seed3 | 3,001 | 3,567 | 1.19 | 42.6 | 110.3 | 3.07 |
| on500_om2_seed1 | 3,184 | 3,723 | 1.17 | 48.5 | 108.8 | 3.12 |
| on500_om2_seed2 | 3,134 | 3,657 | 1.17 | 48.3 | 109.3 | 3.10 |
| on500_om2_seed3 | 3,167 | 3,688 | 1.16 | 46.3 | 109.8 | 3.20 |
| Trung vị, không chồng lấn | 3,185 | 3,567 | | | | |
| Trung vị, có chồng lấn | 3,167 | 3,688 | | | | |

Tỉ số v3 / v2 theo từng mạng trên 38 mạng: trung vị 1.010, nhỏ nhất 0.804, lớn nhất 1.189. Pha I của hai bản giống nhau, nên phần chênh ngoài Pha II là dao động giữa hai lần đo.
