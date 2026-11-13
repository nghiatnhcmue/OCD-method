# Bóc tách DOT-CCM v3

Cập nhật 2026-11-13 19:12. Cấu hình: `methods/proposed/config.json` (v3, họ theo đỉnh, q = 0,05). Kết quả: `results/round_c/ablation/`; mã: `revision/ablation_v3.py`.

Trạng thái: base ok: 168, no_log ok: 158, no_ot ok: 158.
Bản đầy đủ dựng lại từ bộ đệm trùng khít phủ v3 của đợt C: 168 / 168 mạng.

## Kiểm tra 1

Mỗi dòng so với bản đầy đủ trên đúng các mạng mà biến thể đã chạy xong.

| Biến thể | Số mạng | ONMI | ONMI-LFK | ONF1 | F1 | Omega | ONMI đầy đủ cùng mạng | Chênh ONMI | Thắng / thua | p | p (Holm) |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|---:|
| Đầy đủ (v3) | 108 | 0.703 | 0.761 | 0.684 | 0.846 | 0.725 | | | | | |
| Bỏ Pha II | 108 | 0.583 | 0.652 | 0.295 | 0.767 | 0.611 | 0.703 | -0.119 | 2 / 30 | 1.3e-06 | 6.4e-06 |
| Chọn tập theo mật độ thay cho Ψ | 108 | 0.697 | 0.755 | 0.663 | 0.842 | 0.715 | 0.703 | -0.006 | 13 / 21 | 0.092 | 0.37 |
| Bỏ nén log | 108 | 0.701 | 0.759 | 0.684 | 0.844 | 0.723 | 0.703 | -0.002 | 15 / 18 | 0.75 | 1 |
| Bỏ vận tải tối ưu | 108 | 0.671 | 0.726 | 0.750 | 0.797 | 0.682 | 0.703 | -0.032 | 19 / 14 | 0.54 | 1 |
| Pha II cần ít nhất 2 cạnh tới lõi | 108 | 0.703 | 0.761 | 0.684 | 0.846 | 0.725 | 0.703 | 0.000 | 0 / 0 | 1 | 1 |

Wilcoxon theo cặp trên ONMI, theo tô-pô (trung bình các chế độ trọng số đã có); Holm trên các biến thể của bộ này.

## Kiểm tra 2

Mỗi dòng so với bản đầy đủ trên đúng các mạng mà biến thể đã chạy xong.

| Biến thể | Số mạng | ONMI | ONMI-LFK | ONF1 | F1 | Omega | ONMI đầy đủ cùng mạng | Chênh ONMI | Thắng / thua | p | p (Holm) |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|---:|
| Đầy đủ (v3) | 50 | 0.850 | 0.886 | 0.747 | 0.932 | 0.865 | | | | | |
| Bỏ Pha II | 50 | 0.792 | 0.838 | 0.465 | 0.896 | 0.816 | 0.850 | -0.058 | 5 / 40 | 2.7e-08 | 1.4e-07 |
| Chọn tập theo mật độ thay cho Ψ | 50 | 0.856 | 0.887 | 0.758 | 0.934 | 0.870 | 0.850 | 0.007 | 25 / 23 | 0.26 | 0.26 |
| Bỏ nén log | 50 | 0.807 | 0.856 | 0.732 | 0.903 | 0.825 | 0.850 | -0.042 | 10 / 34 | 0.00033 | 0.0013 |
| Bỏ vận tải tối ưu | 50 | 0.840 | 0.879 | 0.784 | 0.924 | 0.842 | 0.850 | -0.009 | 29 / 12 | 0.017 | 0.034 |
| Pha II cần ít nhất 2 cạnh tới lõi | 50 | 0.850 | 0.886 | 0.748 | 0.932 | 0.865 | 0.850 | 0.000 | 11 / 2 | 0.0071 | 0.021 |

Wilcoxon theo cặp trên ONMI, theo mạng; Holm trên các biến thể của bộ này.

## Kiểm tra 3

| Biến thể | Số mạng | ONMI toàn mạng | ONMI có nhãn | F1 có nhãn | Omega có nhãn | Độ phủ có nhãn | Độ phủ toàn mạng | Số cộng đồng | Số mức thuộc TB |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Đầy đủ (v3) | 4 | 0.152 | 0.487 | 0.676 | 0.510 | 0.985 | 1.000 | 164.8 | 1.16 |
| Bỏ Pha II | 4 | 0.155 | 0.485 | 0.686 | 0.513 | 0.982 | 1.000 | 164.8 | 1.14 |
| Chọn tập theo mật độ thay cho Ψ | 4 | 0.160 | 0.568 | 0.697 | 0.529 | 0.986 | 1.000 | 202.0 | 1.29 |
| Pha II cần ít nhất 2 cạnh tới lõi | 4 | 0.153 | 0.486 | 0.678 | 0.510 | 0.984 | 1.000 | 164.8 | 1.15 |

Trung bình; không kiểm định vì số mạng ít.

## N = 5000

| Biến thể | Số mạng | ONMI | ONMI-LFK | ONF1 | F1 | Omega | Số cộng đồng | Số mức thuộc TB |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|
| Đầy đủ (v3) | 6 | 0.989 | 0.989 | 0.953 | 0.994 | 0.993 | 181.7 | 1.05 |
| Bỏ Pha II | 6 | 0.980 | 0.986 | 0.830 | 0.992 | 0.985 | 181.7 | 1.04 |
| Chọn tập theo mật độ thay cho Ψ | 6 | 0.987 | 0.988 | 0.965 | 0.994 | 0.994 | 182.2 | 1.06 |
| Pha II cần ít nhất 2 cạnh tới lõi | 6 | 0.993 | 0.994 | 0.965 | 0.997 | 0.994 | 181.7 | 1.05 |

Trung bình; không kiểm định vì số mạng ít.
