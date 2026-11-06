# OCD-method

Mã thực nghiệm của luận văn về phát hiện cộng đồng chồng lấn trên mạng có trọng số: phương pháp đề xuất, 8 phương pháp
đối chứng (wGHAC, OSLOM, SLPA, Infomap, BigCLAM, DANMF, ClusterONE, ASLPAw), ba bộ dữ liệu kiểm tra, ba mạng thật, mã
chấm điểm và kết quả.

## Cấu trúc

```
settings.py             đường dẫn, danh sách phương pháp và bộ dữ liệu, giới hạn thời gian
run_all.sh              chạy các phương pháp trên ba bộ, chấm phần còn thiếu rồi tổng hợp
requirements.txt        các gói Python và phiên bản đã dùng
methods/<phương pháp>/  method.py (cách gọi và tham số), run_test1.py, run_test2.py, run_test3.py
methods/proposed/       thêm algorithm.py (phương pháp đề xuất) và config.json
common/                 đọc dữ liệu, chạy song song có giới hạn thời gian, chấm điểm, chấm lại, tổng hợp
timing/                 đo thời gian chạy trên 32 mạng đại diện
applications/           ba mạng thật (data/), chuyển định dạng, chạy và tổng hợp
lib/                    độ đo, wGHAC, trình bao các phương pháp đối chứng
data/                   ba bộ kiểm tra; DANH_SACH_TEP.csv ghi sha256 của từng tệp
tools/                  OSLOM2, BigCLAM (SNAP), tệp nhị phân khoảng cách CT của wGHAC, ClusterONE 1.0
results/                raw/ (tập bao phủ), scores/ (điểm), timing/, applications/, logs/, before_fix/,
                        scores_all.csv, SUMMARY.md, SUMMARY.xlsx
```

## Dữ liệu

| Mã | Bộ | Mô tả |
|---|---|---|
| test1 | Kiểm tra 1 | 108 mạng LFR (N = 1000): 36 cấu trúc, mỗi cấu trúc có 3 chế độ trọng số INJ, FLAT, PERM |
| test2 | Kiểm tra 2 | 50 mạng LFR có trọng số, sinh bằng chương trình của Lancichinetti và Fortunato (N = 1000) |
| test3 | Kiểm tra 3 | 4 mạng tương tác protein của nấm men, nhãn là các phức hợp CYC2008 |

Ba mạng thật trong `applications/data/` được tải về nguyên trạng (nguồn tải: `SOURCES.tsv`) và không có nhãn chuẩn:

| Mạng | Nguồn | Đỉnh / cạnh |
|---|---|---|
| Nơ-ron C. elegans | Varshney và cộng sự, PLoS Comput. Biol., 2011 (WormAtlas) | 279 / 2287 |
| Đồng tác giả khoa học mạng | Newman, Phys. Rev. E, 2006 (Netzschleuder) | 379 / 914 |
| Vùng não người, đồng kích hoạt | Crossley và cộng sự, PNAS, 2013 (Netzschleuder) | 638 / 18 625 |

## Môi trường

Ubuntu 22.04 (WSL2), Python 3.10.12, các gói trong `requirements.txt`:

```
pip install -r requirements.txt
```

Các tệp nhị phân trong `tools/` dành cho Linux x86-64 và cần gói `libgomp1`. ClusterONE cần Java 17: nếu không có
`tools/java/jre/` thì dùng lệnh `java` của hệ thống (ví dụ gói `openjdk-17-jre-headless`).

## Cách chạy

Chạy từ thư mục gốc của repo:

```
python3 methods/oslom/run_test1.py                      # OSLOM trên các mạng của Kiểm tra 1 chưa có kết quả
python3 methods/wghac/run_test2.py <net_id> --workers 1  # một mạng
python3 methods/danmf/run_test3.py --rerun              # chạy lại cả các mạng đã có kết quả
python3 common/rescore.py --workers 4                   # chấm lại mọi lượt đã lưu
python3 common/summarize.py                             # bảng tổng hợp
bash run_all.sh                                         # toàn bộ
python3 timing/run_timing.py                            # đo thời gian chạy
python3 applications/prepare.py                         # tệp gốc của ba mạng thật thành danh sách cạnh
python3 applications/run.py                             # ba mạng thật, mỗi mạng thêm 10 bản bỏ 5% cạnh
python3 applications/summarize.py                       # results/applications/SUMMARY.md
```

Mỗi lượt (một phương pháp trên một mạng) chạy trong một tiến trình riêng với một luồng tính, giới hạn 6 giờ. Lượt quá
giờ ghi trạng thái `timeout`, lượt lỗi ghi `error`; lượt chạy lại thất bại không xóa kết quả `ok` đã có. OSLOM, BigCLAM
và ClusterONE còn có giới hạn riêng (7000, 1800 và 7200 giây); lượt lâu nhất của ba phương pháp này là 236, 76 và 5 giây.

## Thời gian chạy

`timing/run_timing.py` đo riêng trên 32 mạng (18 của Kiểm tra 1, 10 của Kiểm tra 2, 4 của Kiểm tra 3): chỉ chạy khi máy
rảnh, tối đa 5 lượt cùng lúc, mỗi lượt gắn một cặp nhân, đồng hồ `CLOCK_MONOTONIC_RAW`. Trung vị (giây):

| Phương pháp | Kiểm tra 1 | Kiểm tra 2 | Kiểm tra 3 |
|---|---:|---:|---:|
| wGHAC | 2319 | 3111 | 5412 |
| ASLPAw | 2030 | 1969 | 4804 |
| Phương pháp đề xuất | 811 | 855 | 1786 |
| OSLOM | 56 | 33 | 31 |
| DANMF | 22 | 20 | 84 |
| BigCLAM | 15 | 16 | 16 |
| SLPA | 8 | 8 | 7 |
| Infomap | 4 | 4 | 4 |
| ClusterONE | 0,9 | 0,9 | 1,2 |

## Nguồn

- `lib/wghac/` dựa trên mã wGHAC kèm bài báo của Prokop, Drázdilová và Platoš (PLoS ONE, 2024,
  doi:10.1371/journal.pone.0312596), đã lược bớt; tệp nhị phân khoảng cách CT trong `tools/` cũng từ mã này.
- Nguồn tải của ClusterONE, chương trình LFR, Java và các tệp CYC2008: `tools/SOURCES.tsv`.
