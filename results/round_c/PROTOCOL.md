# Đợt C: giao thức chọn tham số Pha II và tập khóa

Viết và commit trước khi chạy bất kỳ phương pháp nào trên tập chọn và tập khóa.

## Dữ liệu

Sinh bằng `revision/gen_extra.py`, dùng đúng hai bộ sinh của Kiểm tra 1 và 2 (`research/phat_trien_v2/kiem_tra_luan_van.py`),
khối seed mới đã kiểm không trùng với mọi seed đã dùng trong kho. Dữ liệu nằm ở `data_extra/`, ngoài `data/` đã niêm phong.

| Bộ | Thư mục | Thiết kế | Seed tô-pô |
|---|---|---|---|
| `tune1` | `data_extra/tune_kt1` | như KT1: μ ∈ {0,1; 0,3; 0,5} × (o_n, o_m) ∈ {(0, 2); (200, 4); (400, 6)} × 1 lần lặp × 3 chế độ trọng số = 27 mạng | 993 000 000 + 100·i |
| `tune2` | `data_extra/tune_kt2` | như KT2: 5 mức trộn × 5 mức chồng lấn × 1 lần lặp = 25 mạng | 993 500 000 + 100·i |
| `lock1` | `data_extra/locked_kt1` | như `tune1` | 994 000 000 + 100·i |
| `lock2` | `data_extra/locked_kt2` | như `tune2` | 994 500 000 + 100·i |

## Chọn họ kiểm định và q (trên `tune1` + `tune2`, 52 mạng)

- Pha I cố định: cấu hình v3 (bao đơn điệu bật). P-value cố định: compound Poisson, ξ ~ Gamma.
- Ứng viên: họ ∈ {node, global} × q ∈ {0,001; 0,01; 0,05}, tức 6 cấu hình.
- Tiêu chí: ONMI-MGH trung bình trên 52 mạng, mỗi mạng một trọng số.
- Hòa: nếu hai cấu hình chênh nhau không quá 0,005, chọn cấu hình có ít mức thuộc sai hơn trên các mạng không chồng
  lấn của tập chọn; nếu vẫn hòa, chọn q nhỏ hơn.
- Không dùng Kiểm tra 1–3, N = 5000 hay mạng ứng dụng để chọn.

## Tập khóa (`lock1` + `lock2`, 52 mạng)

1. Ghi cấu hình đã chọn vào `methods/proposed/config.json`, commit, gắn tag `v3-frozen`.
2. Chạy đúng một lần: Pha I v3, Pha II với cấu hình đã chọn; kèm hai dòng đối chứng tính từ cùng lượt chạy: v2 (Pha I
   và Pha II cũ) và Pha I v3 không có Pha II. Thêm OSLOM làm đối thủ tham chiếu.
3. Không đổi tham số sau khi xem kết quả tập khóa. Báo kết quả nguyên trạng.
