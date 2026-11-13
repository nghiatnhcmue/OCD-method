# Bao đơn điệu: thống kê đảo độ cao và tác động

Nút đảo (định nghĩa cũ): độ cao thô của nút lớn hơn độ cao gộp với cha. Lần gộp bị đảo: d(A,B) < max H của hai con; đảo kép: d(A,B) < min H của hai con. Độ lớn: (h(C) − h(cha))/h(C).

| Bộ | Số mạng | Nút trong | Nút đảo | Tỉ lệ (gộp) | Tỉ lệ, trung vị theo mạng | Tỉ lệ lớn nhất | Mạng có đảo | Lần gộp bị đảo | Đảo kép | Độ lớn trung vị | Độ lớn lớn nhất | Bước giảm độ cao |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Kiểm tra 1 | 108 | 107373 | 21609 | 20.1% | 19.1% | 30.7% | 108 | 20249 | 5030 | 0.021 | 0.198 | 17299 |
| Kiểm tra 2 | 50 | 49609 | 9751 | 19.7% | 19.2% | 27.8% | 50 | 10296 | 1526 | 0.017 | 0.178 | 8375 |
| Mạng protein | 4 | 9535 | 486 | 5.1% | 4.6% | 9.6% | 4 | 534 | 39 | 0.014 | 0.612 | 450 |
| N = 5000 | 6 | 29389 | 5443 | 18.5% | 18.4% | 20.1% | 6 | 5502 | 858 | 0.014 | 0.173 | 4645 |
| Mạng ứng dụng | 3 | 1290 | 98 | 7.6% | 7.5% | 10.4% | 3 | 91 | 11 | 0.023 | 0.147 | 87 |

| Bộ | Số mạng | Ψ đổi (nút, trung vị) | Tập chọn đổi | Phủ Pha I đổi | Phủ cuối đổi | ONMI(bật, tắt) phủ cuối, nhỏ nhất | ΔONMI TB | Thắng / thua ONMI | ΔONF1 TB | Thắng / thua ONF1 |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|:---:|
| Kiểm tra 1 | 108 | 231 | 57 | 54 | 52 | 0.011 | +0.0066 | 27 / 24 | +0.0107 | 31 / 17 |
| Kiểm tra 2 | 50 | 237 | 26 | 21 | 20 | 0.935 | +0.0003 | 8 / 12 | +0.0000 | 8 / 8 |
| Mạng protein | 4 | 141 | 4 | 4 | 4 | 0.941 | +0.0046 | 2 / 2 | +0.0029 | 2 / 2 |
| N = 5000 | 6 | 1027 | 4 | 2 | 3 | 0.992 | +0.0002 | 2 / 1 | +0.0004 | 2 / 0 |
| Mạng ứng dụng | 3 | 44 | 0 | 0 | 0 | 1.000 | - | - | - | - |

Δ = bật cờ trừ tắt cờ, trên phủ cuối (Pha II cũ). Mạng protein dùng ONMI có nhãn. ONF1 chỉ tính trên mạng có nhãn chồng lấn.
