# Đợt C: kết quả

Sinh bằng `python3 revision/round_c_report.py`.

## 1. Chọn họ kiểm định và q trên tập chọn (52 mạng)

Luật chọn: `results/round_c/PROTOCOL.md`. ONMI-MGH trung bình; mức thuộc sai trung bình trên mạng không chồng lấn.

| Cấu hình | ONMI | Mức thuộc sai (không chồng lấn) | Số mạng |
|---|---:|---:|---:|
| cp_node_0.05 **(chọn)** | 0.764 | 0.93 | 52 |
| cp_node_0.01 | 0.735 | 0.00 | 52 |
| cp_global_0.05 | 0.728 | 0.00 | 52 |
| cp_node_0.001 | 0.713 | 0.00 | 52 |
| cp_global_0.01 | 0.711 | 0.00 | 52 |
| cp_global_0.001 | 0.699 | 0.00 | 52 |

Đối chứng trên cùng tập: v2 0.794; Pha I v3 không Pha II 0.692.

Theo bộ:

| Cấu hình | tune1 (như KT1) | tune2 (như KT2) |
|---|---:|---:|
| cp_global_0.001 | 0.605 | 0.800 |
| cp_global_0.01 | 0.622 | 0.808 |
| cp_global_0.05 | 0.643 | 0.819 |
| cp_node_0.001 | 0.622 | 0.812 |
| cp_node_0.01 | 0.650 | 0.828 |
| cp_node_0.05 | 0.686 | 0.848 |
| phase1_only | 0.598 | 0.794 |
| v2 | 0.725 | 0.868 |

