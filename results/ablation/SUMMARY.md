# Thực nghiệm bổ sung

Cập nhật 2026-11-09 00:55.

Trạng thái các lượt: base ok: 162, min_edges ok: 168, no_log ok: 158, no_ot ok: 158, slpa_weighted ok: 162.
Bản đầy đủ chạy lại trùng khít kết quả chính: 330 / 330 mạng.

## Bỏ từng thành phần: Kiểm tra 1

| Biến thể | Số mạng | ONMI | ONMI-LFK | ONF1 | F1 | Omega | Chênh ONMI so với đầy đủ | Thắng / thua | p |
|---|:---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| Đầy đủ | 108 | 0.768 | 0.797 | 0.831 | 0.876 | 0.788 |  |  |  |
| Bỏ Pha II | 108 | 0.580 | 0.648 | 0.295 | 0.762 | 0.606 | -0.188 | 5 / 30 | 1.4e-06 |
| Chọn tập theo mật độ thay cho Ψ | 108 | 0.768 | 0.795 | 0.822 | 0.878 | 0.786 | -0.000 | 12 / 21 | 0.2 |
| Bỏ nén log | 108 | 0.769 | 0.799 | 0.838 | 0.878 | 0.788 | 0.001 | 12 / 21 | 0.029 |
| Bỏ vận tải tối ưu | 108 | 0.714 | 0.750 | 0.809 | 0.820 | 0.714 | -0.054 | 17 / 16 | 0.085 |
| Kiểm định hai chiều, cho phép bỏ đỉnh | 108 | 0.763 | 0.799 | 0.815 | 0.874 | 0.780 | -0.005 | 4 / 27 | 5e-06 |
| Pha II cần ít nhất 2 cạnh tới lõi | 108 | 0.763 | 0.799 | 0.823 | 0.875 | 0.787 | -0.005 | 11 / 17 | 0.065 |

Kiểm định Wilcoxon theo cặp trên ONMI, 36 tô-pô (trung bình 3 chế độ trọng số).

## Bỏ từng thành phần: Kiểm tra 2

| Biến thể | Số mạng | ONMI | ONMI-LFK | ONF1 | F1 | Omega | Chênh ONMI so với đầy đủ | Thắng / thua | p |
|---|:---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| Đầy đủ | 50 | 0.867 | 0.884 | 0.806 | 0.937 | 0.884 |  |  |  |
| Bỏ Pha II | 50 | 0.792 | 0.838 | 0.469 | 0.897 | 0.816 | -0.075 | 12 / 35 | 1.2e-05 |
| Chọn tập theo mật độ thay cho Ψ | 50 | 0.868 | 0.881 | 0.791 | 0.936 | 0.883 | 0.000 | 20 / 26 | 0.63 |
| Bỏ nén log | 50 | 0.803 | 0.841 | 0.755 | 0.895 | 0.816 | -0.065 | 10 / 32 | 0.00016 |
| Bỏ vận tải tối ưu | 50 | 0.851 | 0.876 | 0.818 | 0.927 | 0.855 | -0.016 | 23 / 18 | 0.52 |
| Kiểm định hai chiều, cho phép bỏ đỉnh | 50 | 0.859 | 0.880 | 0.779 | 0.933 | 0.872 | -0.009 | 7 / 34 | 4.9e-06 |
| Pha II cần ít nhất 2 cạnh tới lõi | 50 | 0.878 | 0.900 | 0.841 | 0.945 | 0.892 | 0.011 | 34 / 9 | 0.0027 |

Kiểm định Wilcoxon theo cặp trên ONMI, 50 mạng.

## Mạng protein (Kiểm tra 3): biến thể cho phép bỏ đỉnh

| Biến thể | ONMI toàn mạng | ONMI có nhãn | F1 có nhãn | Omega có nhãn | Độ phủ có nhãn | Độ phủ toàn mạng | Số cộng đồng | Cỡ lớn nhất | Số mức thuộc TB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Đầy đủ | 0.126 | 0.412 | 0.607 | 0.472 | 0.998 | 1.000 | 162.8 | 224.5 | 1.44 |
| Bỏ Pha II | 0.154 | 0.481 | 0.685 | 0.511 | 0.982 | 1.000 | 162.8 | 224.2 | 1.13 |
| Chọn tập theo mật độ thay cho Ψ | 0.135 | 0.452 | 0.638 | 0.472 | 0.999 | 1.000 | 202.0 | 211.8 | 1.63 |
| Kiểm định hai chiều, cho phép bỏ đỉnh | 0.179 | 0.445 | 0.610 | 0.567 | 0.904 | 0.810 | 161.2 | 109.0 | 1.16 |
| Pha II cần ít nhất 2 cạnh tới lõi | 0.146 | 0.476 | 0.664 | 0.497 | 0.986 | 1.000 | 162.8 | 224.5 | 1.18 |

Trung bình trên 4 mạng; không kiểm định vì số mạng quá ít.

## Chênh ONMI so với bản đầy đủ theo loại mạng: Kiểm tra 1

| Biến thể | μ = 0.1 (36) | μ = 0.3 (36) | μ = 0.5 (36) | không chồng lấn (18) | có chồng lấn (90) |
|---|---:|---:|---:|---:|---:|
| Đầy đủ (ONMI) | 0.903 | 0.797 | 0.604 | 0.987 | 0.724 |
| Bỏ Pha II | -0.235 | -0.221 | -0.108 | 0.013 | -0.228 |
| Chọn tập theo mật độ thay cho Ψ | -0.002 | 0.006 | -0.005 | -0.008 | 0.001 |
| Bỏ nén log | -0.003 | -0.002 | 0.008 | -0.000 | 0.001 |
| Bỏ vận tải tối ưu | 0.013 | -0.033 | -0.141 | 0.000 | -0.064 |
| Kiểm định hai chiều, cho phép bỏ đỉnh | -0.003 | -0.002 | -0.009 | 0.000 | -0.006 |
| Pha II cần ít nhất 2 cạnh tới lõi | -0.006 | -0.004 | -0.005 | 0.000 | -0.006 |

Dòng đầu là ONMI của bản đầy đủ; các dòng sau là chênh trung bình so với dòng đầu. Số trong ngoặc: số mạng của nhóm.

## Chênh ONMI so với bản đầy đủ theo loại mạng: Kiểm tra 2

| Biến thể | μ = 0.1 (10) | μ = 0.3 (10) | μ = 0.5 (30) | μ_w = 0.1 (20) | μ_w = 0.3 (20) | μ_w = 0.5 (10) | không chồng lấn (10) | có chồng lấn (40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Đầy đủ (ONMI) | 0.915 | 0.889 | 0.844 | 0.900 | 0.878 | 0.781 | 0.979 | 0.839 |
| Bỏ Pha II | -0.031 | -0.099 | -0.082 | -0.052 | -0.109 | -0.055 | 0.020 | -0.099 |
| Chọn tập theo mật độ thay cho Ψ | -0.009 | -0.004 | 0.005 | 0.005 | -0.001 | -0.006 | -0.003 | 0.001 |
| Bỏ nén log | -0.021 | -0.006 | -0.099 | -0.102 | -0.013 | -0.093 | -0.087 | -0.059 |
| Bỏ vận tải tối ưu | 0.003 | -0.003 | -0.027 | 0.019 | 0.000 | -0.118 | 0.000 | -0.020 |
| Kiểm định hai chiều, cho phép bỏ đỉnh | -0.001 | -0.007 | -0.012 | -0.009 | -0.006 | -0.014 | 0.000 | -0.011 |
| Pha II cần ít nhất 2 cạnh tới lõi | 0.051 | 0.015 | -0.004 | 0.021 | 0.004 | 0.004 | 0.011 | 0.010 |

Dòng đầu là ONMI của bản đầy đủ; các dòng sau là chênh trung bình so với dòng đầu. Số trong ngoặc: số mạng của nhóm.

## SLPA có trọng số (phụ lục)

Luật nghe cộng trọng số cạnh thay vì cộng 1; mọi phần khác như SLPA của cdlib (t = 21, r = 0.1, hạt giống 42).

| Bộ | Biến thể | ONMI | ONMI-LFK | ONF1 | F1 | Omega | Chênh ONMI | Thắng / thua | p |
|---|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| Kiểm tra 1 | SLPA | 0.546 | 0.565 | 0.687 | 0.690 | 0.578 |  |  |  |
| Kiểm tra 1 | SLPA có trọng số | 0.562 | 0.594 | 0.698 | 0.718 | 0.595 | 0.016 | 15 / 17 | 0.13 |
| Kiểm tra 2 | SLPA | 0.638 | 0.648 | 0.611 | 0.747 | 0.630 |  |  |  |
| Kiểm tra 2 | SLPA có trọng số | 0.706 | 0.748 | 0.615 | 0.840 | 0.746 | 0.068 | 30 / 19 | 0.043 |
| Kiểm tra 3 | SLPA | 0.193 | 0.255 | 0.053 | 0.377 | 0.156 |  |  |  |
| Kiểm tra 3 | SLPA có trọng số | 0.210 | 0.301 | 0.053 | 0.423 | 0.189 |  |  |  |

## Kiểm định Wilcoxon cho bảng chính (ONMI)

Phương pháp đề xuất so với từng phương pháp đối chứng; p hai phía, hiệu chỉnh Holm trên 8 so sánh của mỗi bộ.

| Bộ | So với | Số cặp | Thắng / thua | Chênh TB | p | p (Holm) |
|---|---|:---:|:---:|---:|---:|---:|
| Kiểm tra 1 | wGHAC | 36 | 33 / 3 | 0.117 | 7.3e-10 | 4.4e-09 |
| Kiểm tra 1 | OSLOM | 36 | 29 / 6 | 0.127 | 4.9e-06 | 4.9e-06 |
| Kiểm tra 1 | SLPA | 36 | 32 / 3 | 0.222 | 4.2e-07 | 9.9e-07 |
| Kiểm tra 1 | Infomap | 36 | 32 / 4 | 0.277 | 4e-09 | 2e-08 |
| Kiểm tra 1 | BigCLAM | 36 | 35 / 1 | 0.199 | 5.8e-11 | 4.7e-10 |
| Kiểm tra 1 | DANMF | 36 | 35 / 1 | 0.184 | 5.8e-11 | 4.7e-10 |
| Kiểm tra 1 | ClusterONE | 36 | 35 / 0 | 0.281 | 2.5e-07 | 9.9e-07 |
| Kiểm tra 1 | ASLPAw | 36 | 33 / 2 | 0.291 | 3.2e-07 | 9.9e-07 |
| Kiểm tra 2 | wGHAC | 50 | 47 / 3 | 0.353 | 5.9e-14 | 3.5e-13 |
| Kiểm tra 2 | OSLOM | 50 | 31 / 16 | 0.057 | 0.0003 | 0.0003 |
| Kiểm tra 2 | SLPA | 50 | 43 / 7 | 0.229 | 5.7e-12 | 2.9e-11 |
| Kiểm tra 2 | Infomap | 50 | 41 / 6 | 0.176 | 1.3e-08 | 4e-08 |
| Kiểm tra 2 | BigCLAM | 50 | 50 / 0 | 0.157 | 1.8e-15 | 1.4e-14 |
| Kiểm tra 2 | DANMF | 50 | 50 / 0 | 0.323 | 1.8e-15 | 1.4e-14 |
| Kiểm tra 2 | ClusterONE | 50 | 33 / 14 | 0.109 | 2.5e-05 | 5.1e-05 |
| Kiểm tra 2 | ASLPAw | 50 | 43 / 6 | 0.184 | 5.7e-09 | 2.3e-08 |

## Thời gian trên bộ N = 5000

6 mạng LFR có trọng số (μ_t = μ_w = 0.3; 3 mạng không chồng lấn, 3 mạng có 500 đỉnh chồng lấn, o_m = 2), cùng quy trình đo với 32 mạng đại diện. Lượt quá giờ được tính là lâu hơn giới hạn khi lấy trung vị. Cột N = 1000: mạng cùng tham số, không chồng lấn, trong 32 mạng đại diện.

| Phương pháp | ok / quá giờ / lỗi | Không chồng lấn: trung vị (s) | Có chồng lấn: trung vị (s) | Lớn nhất (s) | N = 1000 (s) | Gấp (lần) | Bộ nhớ lớn nhất (GB) |
|---|:---:|---:|---:|---:|---:|---:|---:|
| Phương pháp đề xuất | 6 / 0 / 0 | 3185 | 3167 | 3283 | 869 | 3.7 | 3.7 |
| OSLOM | 6 / 0 / 0 | 207 | 213 | 263 | 16 | 13.1 | 0.5 |
| SLPA | 6 / 0 / 0 | 23 | 23 | 25 | 11 | 2.1 | 0.5 |
| Infomap | 6 / 0 / 0 | 4 | 5 | 7 | 4 | 1.2 | 0.5 |
| BigCLAM | 6 / 0 / 0 | 85 | 79 | 90 | 14 | 5.9 | 0.5 |
| DANMF | 6 / 0 / 0 | 355 | 231 | 367 | 16 | 22.6 | 0.7 |
| ClusterONE | 6 / 0 / 0 | 2 | 2 | 2 | 1 | 2.6 | 0.2 |
| ASLPAw | 6 / 0 / 0 | 12017 | 12197 | 12648 | 1825 | 6.6 | 0.5 |

Gấp: trung vị nhóm không chồng lấn chia cho thời gian ở N = 1000. Bộ nhớ: RSS lớn nhất của lượt chạy, chỉ có ở các lượt đo sau khi bổ sung trường này.

wGHAC không đo ở N = 5000. Mỗi mạng có 28191–30637 clique cực đại; wGHAC dựng ma trận khoảng cách dày giữa mọi cặp clique (6.4–7.5 GB mỗi lượt) và tính từng cặp. Ngoại suy theo số cặp clique từ mạng N = 1000 cùng tham số (6295 clique, 2865 s) cho khoảng 16–19 giờ mỗi mạng, vượt giới hạn 6 giờ. Lần chạy đầu, 3 lượt wGHAC chạy cùng lúc làm máy hết bộ nhớ sau 3,3 giờ.

## Độ chính xác trên bộ N = 5000

| Phương pháp | Số mạng | ONMI không chồng lấn | ONMI có chồng lấn | ONMI | ONMI-LFK | ONF1 | F1 | Omega | Số mức thuộc TB |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Phương pháp đề xuất | 6 | 0.529 | 0.416 | 0.473 | 0.575 | 0.268 | 0.721 | 0.539 | 1.81 |
| OSLOM | 6 | 1.000 | 0.990 | 0.995 | 0.997 | 0.962 | 0.999 | 0.996 | 1.05 |
| SLPA | 6 | 0.995 | 0.965 | 0.980 | 0.979 | 0.819 | 0.986 | 0.984 | 1.04 |
| Infomap | 6 | 0.994 | 0.834 | 0.914 | 0.934 | 0.000 | 0.960 | 0.936 | 1.00 |
| BigCLAM | 6 | 0.825 | 0.593 | 0.709 | 0.723 | 0.909 | 0.815 | 0.764 | 1.07 |
| DANMF | 6 | 0.653 | 0.421 | 0.537 | 0.663 | 0.304 | 0.733 | 0.629 | 0.68 |
| ClusterONE | 6 | 1.000 | 0.943 | 0.971 | 0.978 | 0.717 | 0.988 | 0.980 | 1.03 |
| ASLPAw | 6 | 0.987 | 0.833 | 0.910 | 0.926 | 0.128 | 0.954 | 0.937 | 1.00 |
| Đề xuất, bỏ Pha II | 6 | 1.000 | 0.961 | 0.981 | 0.986 | 0.830 | 0.992 | 0.986 | 1.04 |
| Đề xuất, Pha II cần ít nhất 2 cạnh tới lõi | 6 | 0.939 | 0.927 | 0.933 | 0.953 | 0.799 | 0.976 | 0.952 | 1.10 |

Trung bình trên 6 mạng (3 không chồng lấn, 3 có chồng lấn). Hai dòng cuối: cùng lần chạy của phương pháp đề xuất, bỏ Pha II hoặc chỉ nhận mức thuộc có ít nhất 2 cạnh tới lõi.
