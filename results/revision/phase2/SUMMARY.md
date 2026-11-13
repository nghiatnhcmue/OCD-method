# Pha II: trước và sau

Pha I mới (bao đơn điệu) cho mọi dòng trừ v2. Thời gian Pha II đo bằng CLOCK_MONOTONIC_RAW trong lô song song, không theo quy trình đo thời gian; chỉ dùng để so tương đối. Mạng chưa có kết quả: 0.

### 35 mạng mà Pha II cũ làm giảm ONMI (35 mạng)

| Cấu hình | ONMI | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | 0.787 | 0.476 | 0.774 | 787.5 | 769.7 | 0.023 | 418.5 |  | 4.6 |
| Pha I mới, bỏ Pha II | 0.895 | 0.647 | 0.615 | 0.0 | 0.0 | - | 0.0 | 35 / 0 | - |
| Pha I mới + Pha II cũ | 0.787 | 0.477 | 0.777 | 788.0 | 770.2 | 0.023 | 418.5 | 3 / 4 | 4.6 |
| Compound Poisson, họ node, q = 0.001 | 0.897 | 0.675 | 0.662 | 8.6 | 1.5 | 0.831 | 0.0 | 35 / 0 | 20.8 |
| Compound Poisson, họ node, q = 0.01 | 0.898 | 0.687 | 0.684 | 14.8 | 4.4 | 0.703 | 0.5 | 35 / 0 | 20.8 |
| Compound Poisson, họ node, q = 0.05 | 0.897 | 0.689 | 0.709 | 28.3 | 14.9 | 0.473 | 4.7 | 35 / 0 | 20.7 |
| Compound Poisson, họ global, q = 0.001 | 0.897 | 0.667 | 0.648 | 5.2 | 0.3 | 0.950 | 0.0 | 35 / 0 | 20.7 |
| Compound Poisson, họ global, q = 0.01 | 0.897 | 0.674 | 0.659 | 7.6 | 0.7 | 0.906 | 0.0 | 35 / 0 | 20.7 |
| Compound Poisson, họ global, q = 0.05 | 0.898 | 0.683 | 0.675 | 10.7 | 1.3 | 0.880 | 0.0 | 35 / 0 | 20.7 |
| Số cạnh, họ node, q = 0.001 | 0.898 | 0.690 | 0.687 | 12.1 | 1.9 | 0.847 | 0.0 | 35 / 0 | 3.2 |

### Kiểm tra 1 (108 mạng)

| Cấu hình | ONMI | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | 0.768 | 0.831 | 0.853 | 455.5 | 78.6 | 0.827 | 8.0 |  | 6.1 |
| Pha I mới, bỏ Pha II | 0.583 | 0.295 | 0.239 | 0.0 | 0.0 | - | 0.0 | 14 / 88 | - |
| Pha I mới + Pha II cũ | 0.774 | 0.842 | 0.862 | 461.8 | 79.3 | 0.828 | 8.0 | 27 / 24 | 6.1 |
| Compound Poisson, họ node, q = 0.001 | 0.622 | 0.443 | 0.358 | 59.7 | 0.1 | 0.999 | 0.0 | 14 / 88 | 10.1 |
| Compound Poisson, họ node, q = 0.01 | 0.658 | 0.562 | 0.463 | 126.8 | 0.5 | 0.996 | 0.1 | 14 / 87 | 10.1 |
| Compound Poisson, họ node, q = 0.05 | 0.703 | 0.684 | 0.586 | 212.8 | 2.7 | 0.987 | 0.8 | 17 / 84 | 10.1 |
| Compound Poisson, họ global, q = 0.001 | 0.599 | 0.351 | 0.289 | 23.5 | 0.0 | 1.000 | 0.0 | 14 / 88 | 10.1 |
| Compound Poisson, họ global, q = 0.01 | 0.622 | 0.436 | 0.361 | 62.3 | 0.1 | 0.999 | 0.0 | 14 / 88 | 10.1 |
| Compound Poisson, họ global, q = 0.05 | 0.654 | 0.533 | 0.454 | 120.1 | 0.7 | 0.994 | 0.0 | 14 / 87 | 10.1 |
| Số cạnh, họ node, q = 0.001 | 0.626 | 0.460 | 0.370 | 68.3 | 0.1 | 0.999 | 0.0 | 14 / 88 | 2.0 |

### Kiểm tra 2 (50 mạng)

| Cấu hình | ONMI | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | 0.867 | 0.806 | 0.849 | 191.5 | 53.0 | 0.723 | 13.1 |  | 4.3 |
| Pha I mới, bỏ Pha II | 0.792 | 0.465 | 0.384 | 0.0 | 0.0 | - | 0.0 | 12 / 35 | - |
| Pha I mới + Pha II cũ | 0.868 | 0.806 | 0.849 | 191.7 | 52.9 | 0.724 | 13.1 | 8 / 12 | 4.3 |
| Compound Poisson, họ node, q = 0.001 | 0.810 | 0.564 | 0.469 | 23.1 | 0.1 | 0.995 | 0.0 | 13 / 34 | 17.7 |
| Compound Poisson, họ node, q = 0.01 | 0.827 | 0.652 | 0.546 | 45.6 | 0.4 | 0.992 | 0.0 | 15 / 32 | 17.7 |
| Compound Poisson, họ node, q = 0.05 | 0.850 | 0.747 | 0.648 | 81.0 | 3.4 | 0.958 | 0.9 | 22 / 25 | 17.7 |
| Compound Poisson, họ global, q = 0.001 | 0.799 | 0.495 | 0.415 | 9.2 | 0.0 | 0.998 | 0.0 | 12 / 35 | 17.7 |
| Compound Poisson, họ global, q = 0.01 | 0.807 | 0.532 | 0.448 | 19.8 | 0.2 | 0.992 | 0.0 | 14 / 33 | 17.7 |
| Compound Poisson, họ global, q = 0.05 | 0.818 | 0.579 | 0.492 | 34.4 | 0.6 | 0.983 | 0.0 | 15 / 32 | 17.7 |
| Số cạnh, họ node, q = 0.001 | 0.814 | 0.577 | 0.485 | 28.9 | 0.2 | 0.992 | 0.0 | 16 / 31 | 2.5 |

### Mạng protein (4 mạng)

| Cấu hình | ONMI có nhãn | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | 0.412 | 0.094 | 0.288 | 933.5 | 909.0 | 0.026 | - |  | 24.7 |
| Pha I mới, bỏ Pha II | 0.485 | 0.061 | 0.098 | 0.0 | 0.0 | - | - | 4 / 0 | - |
| Pha I mới + Pha II cũ | 0.417 | 0.096 | 0.295 | 949.0 | 923.8 | 0.027 | - | 2 / 2 | 24.7 |
| Compound Poisson, họ node, q = 0.001 | 0.484 | 0.065 | 0.103 | 13.5 | 12.5 | 0.074 | - | 4 / 0 | 9.9 |
| Compound Poisson, họ node, q = 0.01 | 0.485 | 0.067 | 0.110 | 36.2 | 33.8 | 0.069 | - | 4 / 0 | 9.9 |
| Compound Poisson, họ node, q = 0.05 | 0.487 | 0.073 | 0.128 | 80.5 | 75.5 | 0.062 | - | 4 / 0 | 9.9 |
| Compound Poisson, họ global, q = 0.001 | 0.484 | 0.063 | 0.100 | 2.2 | 2.2 | 0.000 | - | 4 / 0 | 9.8 |
| Compound Poisson, họ global, q = 0.01 | 0.483 | 0.063 | 0.100 | 6.8 | 6.0 | 0.111 | - | 4 / 0 | 9.8 |
| Compound Poisson, họ global, q = 0.05 | 0.484 | 0.065 | 0.103 | 11.5 | 10.2 | 0.109 | - | 4 / 0 | 9.8 |
| Số cạnh, họ node, q = 0.001 | 0.484 | 0.074 | 0.118 | 18.8 | 16.0 | 0.147 | - | 4 / 0 | 1.4 |

### N = 5000 (6 mạng)

| Cấu hình | ONMI | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | 0.473 | 0.268 | 0.999 | 3866.3 | 3794.7 | 0.019 | 2977.7 |  | 64.9 |
| Pha I mới, bỏ Pha II | 0.980 | 0.830 | 0.709 | 0.0 | 0.0 | - | 0.0 | 6 / 0 | - |
| Pha I mới + Pha II cũ | 0.473 | 0.269 | 0.999 | 3859.2 | 3788.0 | 0.018 | 2977.3 | 2 / 1 | 64.9 |
| Compound Poisson, họ node, q = 0.001 | 0.988 | 0.915 | 0.843 | 33.3 | 0.2 | 0.995 | 0.0 | 6 / 0 | 156.9 |
| Compound Poisson, họ node, q = 0.01 | 0.991 | 0.949 | 0.907 | 51.8 | 2.7 | 0.949 | 2.7 | 6 / 0 | 156.9 |
| Compound Poisson, họ node, q = 0.05 | 0.989 | 0.953 | 0.958 | 91.8 | 29.8 | 0.675 | 26.7 | 6 / 0 | 156.9 |
| Compound Poisson, họ global, q = 0.001 | 0.985 | 0.888 | 0.799 | 22.5 | 0.0 | 1.000 | 0.0 | 6 / 0 | 156.7 |
| Compound Poisson, họ global, q = 0.01 | 0.987 | 0.912 | 0.838 | 32.2 | 0.2 | 0.995 | 0.0 | 6 / 0 | 156.7 |
| Compound Poisson, họ global, q = 0.05 | 0.991 | 0.940 | 0.889 | 45.2 | 0.5 | 0.989 | 0.0 | 6 / 0 | 156.7 |
| Số cạnh, họ node, q = 0.001 | 0.992 | 0.950 | 0.905 | 48.8 | 0.2 | 0.997 | 0.0 | 6 / 0 | 15.6 |

### Mạng ứng dụng (3 mạng)

| Cấu hình | ONMI | ONF1 | R_O | Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) | Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|
| v2 (kết quả cũ) | - | - | - | 25.3 | - | - | 25.3 |  | 0.7 |
| Pha I mới, bỏ Pha II | - | - | - | 0.0 | 0.0 | - | 0.0 | 0 / 0 | - |
| Pha I mới + Pha II cũ | - | - | - | 25.3 | - | - | 25.3 | 0 / 0 | 0.7 |
| Compound Poisson, họ node, q = 0.001 | - | - | - | 4.0 | - | - | 4.0 | 0 / 0 | 7.1 |
| Compound Poisson, họ node, q = 0.01 | - | - | - | 13.7 | - | - | 13.7 | 0 / 0 | 7.1 |
| Compound Poisson, họ node, q = 0.05 | - | - | - | 22.7 | - | - | 22.7 | 0 / 0 | 7.1 |
| Compound Poisson, họ global, q = 0.001 | - | - | - | 0.0 | - | - | 0.0 | 0 / 0 | 7.1 |
| Compound Poisson, họ global, q = 0.01 | - | - | - | 1.3 | - | - | 1.3 | 0 / 0 | 7.1 |
| Compound Poisson, họ global, q = 0.05 | - | - | - | 8.3 | - | - | 8.3 | 0 / 0 | 7.1 |
| Số cạnh, họ node, q = 0.001 | - | - | - | 14.0 | - | - | 14.0 | 0 / 0 | 0.7 |
