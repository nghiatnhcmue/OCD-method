# Mạng ứng dụng: kết quả của phương pháp đề xuất

Cập nhật 2026-11-13 13:52. Tham số như trong `methods/proposed/config.json`.

## Tổng quan

| Mạng | Đỉnh | Cạnh | Cộng đồng | Cỡ trung vị / lớn nhất | Độ phủ | Mức thuộc TB | Đỉnh chồng lấn: Pha I / cuối | Mức thuộc Pha II thêm | Độ dẫn trung vị | Thời gian (s) | Bước gộp |
|---|---:|---:|---:|:---:|---:|---:|:---:|---:|---:|---:|---:|
| C. elegans | 279 | 2287 | 2 | 169 / 186 | 100.0% | 1.21 | 59 / 59 | 0 | 0.169 | 226 | 90.1% |
| Đồng tác giả | 379 | 914 | 23 | 10 / 66 | 100.0% | 1.11 | 39 / 39 | 0 | 0.077 | 96 | 88.0% |
| Não người | 638 | 18625 | 7 | 59 / 300 | 100.0% | 1.20 | 58 / 118 | 68 | 0.420 | 230 | 83.3% |

Độ dẫn: độ dẫn có trọng số của từng cộng đồng. Bước gộp: phần của bước gộp cụm trong tổng thời gian các bước. Thời gian đo cùng điều kiện với timing/run_timing.py.

## Nơ-ron C. elegans (Varshney et al. 2011)

- Cặp nơ-ron trái/phải cùng ít nhất một cộng đồng: 92/92 cặp (100.0%). Mốc hoán vị nhãn đỉnh (100 lần): trung bình 69.8%, lớn nhất 79.3%.
- ONMI giữa tập bao phủ và 10 hạch giải phẫu: 0.108. Mốc hoán vị nhãn đỉnh: trung vị 0.006, lớn nhất 0.013.
- Ký hiệu hạch (Achacoso và Yamamoto 1992, cột AY Ganglion Designation): A hạch trước, B hạch lưng, C hạch bên, D hạch bụng, E hạch retrovesicular, F nhóm thân bên, G dây thần kinh bụng, H hạch trước hậu môn, J hạch lưng trực tràng, K hạch thắt lưng.

| # | Cỡ | Đầu / thân / đuôi | Hạch (số nơ-ron) | Độ dẫn | Nơ-ron có trọng số nội bộ lớn nhất |
|---:|---:|:---:|---|---:|---|
| 1 | 186 | 155 / 16 / 15 | A 38, B 5, C 61, D 32, E 21, F 12, G 2, H 3, J 2, K 10 | 0.184 | RIAL, RIAR, DVA, AVEL, AIBR, AVBR, AVER, AIBL |
| 2 | 152 | 37 / 88 / 27 | B 2, C 17, D 4, E 24, F 14, G 57, H 12, J 3, K 19 | 0.153 | AVAR, AVAL, PVCL, PVCR, AVBR, AVBL, DVA, AVDR |

Nơ-ron thuộc nhiều cộng đồng: 59.

| Nơ-ron | Vùng | Hạch | Cộng đồng: trọng số nối vào |
|---|---|:---:|---|
| ADAL | đầu | E | 1: 44.00; 2: 28.00 |
| ADAR | đầu | E | 1: 37.00; 2: 20.00 |
| ADER | đầu | E | 1: 44.00; 2: 27.00 |
| ADLL | đầu | C | 1: 44.00; 2: 26.00 |
| ADLR | đầu | C | 1: 42.00; 2: 22.00 |
| AIML | đầu | D | 1: 31.00; 2: 16.00 |
| ALA | đầu | B | 1: 9.00; 2: 9.00 |
| ALML | thân | F | 1: 23.00; 2: 21.00 |
| ALMR | thân | F | 1: 11.00; 2: 10.00 |
| AQR | đầu | E | 1: 52.00; 2: 47.00 |
| ASHL | đầu | C | 1: 47.00; 2: 22.00 |
| ASHR | đầu | C | 1: 50.00; 2: 31.00 |
| AVBL | đầu | C | 1: 113.00; 2: 170.00 |
| AVBR | đầu | C | 1: 122.00; 2: 180.00 |
| AVDR | đầu | C | 1: 63.00; 2: 138.00 |
| AVEL | đầu | C | 1: 127.00; 2: 93.00 |
| AVER | đầu | C | 1: 119.00; 2: 81.00 |
| AVFL | đầu | E | 1: 81.00; 2: 79.00 |
| AVFR | đầu | E | 1: 63.00; 2: 59.00 |
| AVG | đầu | E | 1: 28.00; 2: 37.00 |
| AVHL | đầu | C | 1: 47.00; 2: 39.00 |
| AVHR | đầu | C | 1: 45.00; 2: 39.00 |
| AVJL | đầu | C | 1: 49.00; 2: 68.00 |
| AVJR | đầu | C | 1: 49.00; 2: 61.00 |
| AVKL | đầu | D | 1: 96.00; 2: 68.00 |
| AVL | đầu | D | 1: 42.00; 2: 60.00 |
| AVM | thân | F | 1: 33.00; 2: 46.00 |
| BDUL | thân | F | 1: 23.00; 2: 19.00 |
| BDUR | thân | F | 1: 28.00; 2: 36.00 |
| DVA | đuôi | J | 1: 135.00; 2: 155.00 |
| DVC | đuôi | J | 1: 63.00; 2: 64.00 |
| FLPL | đầu | E | 1: 42.00; 2: 72.00 |
| FLPR | đầu | E | 1: 27.00; 2: 56.00 |
| HSNL | thân | F | 1: 48.00; 2: 30.00 |
| HSNR | thân | F | 1: 42.00; 2: 47.00 |
| PDEL | thân | F | 1: 53.00; 2: 60.00 |
| PDER | thân | F | 1: 67.00; 2: 75.00 |
| PHAL | đuôi | K | 1: 30.00; 2: 38.00 |
| PHAR | đuôi | K | 1: 24.00; 2: 29.00 |
| PVM | thân | F | 1: 37.00; 2: 39.00 |
| PVNL | đuôi | K | 1: 38.00; 2: 56.00 |
| PVPL | đuôi | H | 1: 48.00; 2: 56.00 |
| PVPR | đuôi | H | 1: 62.00; 2: 73.00 |
| PVQR | đuôi | K | 1: 50.00; 2: 24.00 |
| PVR | đuôi | K | 1: 45.00; 2: 43.00 |
| PVT | đuôi | H | 1: 51.00; 2: 31.00 |
| RIFL | đầu | E | 1: 32.00; 2: 26.00 |
| RIFR | đầu | E | 1: 48.00; 2: 39.00 |
| SAAVR | đầu | C | 1: 27.00; 2: 15.00 |
| SABD | đầu | E | 1: 18.00; 2: 32.00 |
| SABVL | đầu | E | 1: 20.00; 2: 30.00 |
| SABVR | đầu | E | 1: 11.00; 2: 17.00 |
| SDQL | thân | F | 1: 12.00; 2: 11.00 |
| SDQR | thân | F | 1: 27.00; 2: 20.00 |
| SIBVL | đầu | D | 1: 12.00; 2: 6.00 |
| VA01 | thân | E | 1: 11.00; 2: 29.00 |
| VB01 | thân | E | 1: 35.00; 2: 27.00 |
| VC04 | thân | G | 1: 6.00; 2: 12.00 |
| VC05 | thân | G | 1: 16.00; 2: 15.00 |

## Vùng não người, mạng đồng kích hoạt (Crossley et al. 2013)

- Cộng đồng có ít nhất 90% số vùng cùng một bán cầu (x < 0 là bán cầu trái): 0/7.
- Khoảng cách trung bình giữa hai vùng trong cùng cộng đồng, chia cho giá trị đó của tập vùng ngẫu nhiên cùng cỡ (100 lần chọn): trung vị 0.83, từ 0.40 đến 0.92.
- Tọa độ tính bằng mm trong không gian chuẩn; y > 0 là phía trước (thùy trán), z > 0 là phía trên.

| # | Cỡ | Trái / phải | Tâm (x, y, z) | Khoảng cách TB (mm) | Tập ngẫu nhiên (mm) | Độ dẫn |
|---:|---:|:---:|:---:|---:|---:|---:|
| 1 | 300 | 147 / 153 | 3, -8, 34 | 71.8 | 82.5 | 0.198 |
| 2 | 200 | 105 / 95 | -0, 6, 2 | 76.3 | 82.6 | 0.232 |
| 3 | 105 | 52 / 53 | 3, -74, 5 | 47.2 | 82.4 | 0.267 |
| 4 | 59 | 29 / 30 | 3, -18, 1 | 74.4 | 82.6 | 0.420 |
| 5 | 45 | 20 / 25 | 3, -30, 66 | 32.7 | 82.3 | 0.512 |
| 6 | 32 | 17 / 15 | 1, -56, 11 | 64.5 | 82.7 | 0.691 |
| 7 | 24 | 14 / 10 | -8, -44, -14 | 68.8 | 82.7 | 0.731 |

Vùng thuộc nhiều cộng đồng: 118.

| Vùng (x, y, z) | Cộng đồng: trọng số nối vào |
|---|---|
| vùng 8 (-8, -38, 49) | 2: 0.84; 5: 0.34 |
| vùng 10 (-7, -24, 44) | 1: 1.74; 2: 0.67 |
| vùng 13 (7, -24, 34) | 1: 1.24; 2: 0.71 |
| vùng 15 (9, -27, 45) | 2: 0.85; 5: 0.52 |
| vùng 17 (6, -17, 43) | 2: 1.03; 5: 0.55 |
| vùng 23 (-4, -42, 29) | 2: 2.08; 6: 0.27 |
| vùng 25 (-8, -68, 26) | 2: 1.22; 3: 1.27 |
| vùng 36 (16, -78, 40) | 1: 1.11; 3: 1.38 |
| vùng 50 (-47, 23, -7) | 1: 3.04; 2: 0.99 |
| vùng 58 (26, 21, -19) | 1: 0.43; 2: 0.40 |
| vùng 60 (51, 25, -8) | 1: 1.48; 2: 0.50 |
| vùng 64 (-48, 29, 7) | 1: 2.27; 7: 0.46 |
| vùng 65 (-46, 25, 2) | 1: 3.79; 4: 0.97 |
| vùng 102 (-29, 40, 35) | 1: 0.84; 2: 0.47 |
| vùng 113 (39, 55, -6) | 1: 1.81; 2: 1.20 |
| vùng 114 (38, 21, 46) | 1: 1.22; 2: 1.20 |
| vùng 132 (29, 38, 37) | 1: 0.61; 2: 0.71 |
| vùng 139 (-17, -8, 75) | 1: 0.23; 5: 0.24 |
| vùng 178 (23, 62, 3) | 1: 0.53; 2: 0.48 |
| vùng 182 (17, 30, 51) | 2: 1.42; 5: 0.28 |
| vùng 185 (19, -9, 70) | 1: 1.76; 5: 0.72 |
| vùng 196 (-26, -42, -15) | 2: 1.32; 3: 1.35; 6: 0.33 |
| vùng 197 (-40, -52, -18) | 3: 2.53; 7: 0.80 |
| vùng 207 (36, -33, -24) | 2: 0.97; 3: 0.98 |
| vùng 212 (41, -43, -21) | 3: 2.01; 7: 0.62 |
| vùng 213 (-42, -20, 9) | 1: 1.85; 4: 2.01 |
| vùng 214 (46, -18, 9) | 1: 1.57; 4: 1.87 |
| vùng 215 (-19, -34, -1) | 2: 0.71; 3: 0.58 |
| vùng 220 (-48, -62, 25) | 2: 3.76; 6: 0.47 |
| vùng 239 (43, -6, -4) | 1: 1.84; 4: 1.03 |
| vùng 259 (-47, -67, -13) | 3: 3.45; 7: 0.85 |
| vùng 271 (-43, -74, 1) | 3: 3.84; 6: 0.90 |
| vùng 272 (-43, -74, 15) | 3: 1.55; 6: 1.33 |
| vùng 276 (-37, -73, 29) | 2: 1.82; 6: 0.46 |
| vùng 282 (43, -77, 4) | 3: 3.53; 6: 0.99 |
| vùng 294 (43, -67, 37) | 1: 0.69; 2: 1.09 |
| vùng 314 (30, -36, -11) | 2: 0.78; 3: 0.78 |
| vùng 319 (-11, -20, 76) | 1: 0.65; 5: 0.89 |
| vùng 320 (-7, -20, 63) | 1: 1.37; 5: 1.38 |
| vùng 339 (-11, -60, 9) | 2: 1.60; 3: 2.03 |
| vùng 355 (-19, -49, 69) | 1: 2.24; 5: 0.77 |
| vùng 363 (21, -50, 69) | 1: 1.11; 5: 0.98 |
| vùng 366 (-20, -39, 74) | 1: 1.11; 5: 1.15 |
| vùng 367 (-56, -4, 18) | 1: 2.72; 4: 1.46 |
| vùng 373 (-51, -10, 37) | 1: 3.85; 4: 2.03 |
| vùng 378 (-21, -34, 68) | 1: 1.04; 5: 0.84 |
| vùng 380 (-30, -31, 65) | 1: 1.94; 5: 0.87 |
| vùng 381 (-27, -40, 64) | 1: 2.41; 5: 1.02 |
| vùng 386 (30, -34, 67) | 1: 1.68; 5: 1.06 |
| vùng 389 (24, -34, 63) | 1: 0.69; 5: 0.98 |
| vùng 391 (29, -44, 64) | 1: 2.04; 5: 0.60 |
| vùng 392 (63, -3, 22) | 1: 2.29; 4: 1.24 |
| vùng 393 (53, -8, 34) | 1: 4.11; 4: 1.83 |
| vùng 395 (37, -36, 62) | 1: 2.47; 5: 0.72 |
| vùng 402 (-21, -14, 72) | 1: 2.48; 5: 1.11 |
| vùng 408 (-31, -25, 64) | 1: 3.76; 5: 1.17 |
| vùng 409 (-24, -22, 70) | 1: 2.09; 5: 1.26 |
| vùng 413 (24, -19, 77) | 1: 0.10; 5: 0.19 |
| vùng 414 (51, -7, 41) | 1: 4.32; 4: 1.98 |
| vùng 417 (26, -26, 67) | 1: 1.34; 5: 1.37 |
| ... còn 58 vùng | |

## Đồng tác giả khoa học mạng (Newman 2006), thành phần liên thông lớn nhất

| # | Cỡ | Độ dẫn | Tác giả có trọng số nội bộ lớn nhất |
|---:|---:|---:|---|
| 1 | 66 | 0.066 | BARABASI, A, JEONG, H, KAHNG, B, OLTVAI, Z, VICSEK, T, ALBERT, R, KRAPIVSKY, P, RAVASZ, E |
| 2 | 64 | 0.063 | PASTORSATORRAS, R, VESPIGNANI, A, MORENO, Y, DIAZGUILERA, A, VAZQUEZ, A, AMARAL, L, GUIMERA, R, BARTHELEMY, M |
| 3 | 50 | 0.058 | NEWMAN, M, WATTS, D, STROGATZ, S, KIM, B, HOLME, P, SNEPPEN, K, MOORE, C, DODDS, P |
| 4 | 25 | 0.042 | STAUFFER, D, KERTESZ, J, HOLYST, J, DAFONTOURACOSTA, L, KASKI, K, FRONCZAK, A, BERNARDES, A, ONNELA, J |
| 5 | 23 | 0.067 | CALDARELLI, G, CAPOCCI, A, DELOSRIOS, P, GARLASCHELLI, D, MUNOZ, M, BATTISTON, S, MARRO, J, SERVEDIO, V |
| 6 | 20 | 0.143 | BOCCALETTI, S, MANCINI, H, BRAGARD, J, HWANG, D, VALLADARES, D, HENTSCHEL, H, CHAVEZ, M, AMANN, A |
| 7 | 19 | 0.128 | LATORA, V, MARCHIORI, M, CRUCITTI, P, RAPISARDA, A, TADIC, B, PORTA, S, THURNER, S, TIERI, P |
| 8 | 18 | 0.141 | KURTHS, J, ROSENBLUM, M, PIKOVSKY, A, ZHOU, C, CHATE, H, OSIPOV, G, VALLADARES, D, RUDZICK, O |
| 9 | 17 | 0.098 | SOLE, R, VALVERDE, S, FERRERICANCHO, R, KUNTZ, P, MONTOYA, J, SMITH, E, BUHL, J, GAUTRAIS, J |
| 10 | 12 | 0.080 | RAGHAVAN, P, RAJAGOPALAN, S, TOMKINS, A, KUMAR, R, KLEINBERG, J, KUMAR, S, SIVAKUMAR, D, UPFAL, E |
| 11 | 11 | 0.063 | RINALDO, A, MARITAN, A, RODRIGUEZITURBE, I, RIGON, R, BANAVAR, J, HOLTER, N, MITRA, M, CIEPLAK, M |
| 12 | 10 | 0.062 | TOROCZKAI, Z, BASSLER, K, PACZUSKI, M, BAIESI, M, BENNAIM, E, FRAUENFELDER, H, CORRAL, A, KOZMA, B |
| 13 | 10 | 0.115 | LAI, Y, MOTTER, A, LIU, Z, DEMOURA, A, HOPPENSTEADT, F, NISHIKAWA, T, GREBOGI, C, YE, N |
| 14 | 10 | 0.071 | GROSS, J, HAMALAINEN, M, SCHNITZLER, A, KUJALA, J, TIMMERMANN, L, SALMELIN, R, HARI, R, ILMONIEMI, R |
| 15 | 9 | 0.077 | HERRMANN, H, SOUSA, A, DEARCANGELIS, L, GONZALES, M, ROUX, S, YUSONG, T, LINGJIANG, K, MUREN, L |
| 16 | 8 | 0.077 | FORTUNA, L, LAROSA, M, FRASCA, M, BUCOLO, M, SPATA, A, COSENZA, S, STAGNI, C, USAI, L |
| 17 | 8 | 0.043 | HAVLIN, S, COHEN, R, BENAVRAHAM, D, SONG, C, MAKSE, H, EREZ, K, ROZENFELD, A, SCHWARTZ, N |
| 18 | 8 | 0.111 | BENJACOB, E, SHEFI, O, GOLDING, I, SEGEV, R, AYALI, A, CZIROK, A, COHEN, I, SHOCHET, O |
| 19 | 7 | 0.077 | PECORA, L, CARROLL, T, BARAHONA, M, HEAGY, J, FINK, K, JOHNSON, G, PELAEZ, A |
| 20 | 7 | 0.133 | LAWRENCE, S, GILES, C, FLAKE, G, KLEINBERG, J, PENNOCK, D, GLOVER, E, COETZEE, F |
| 21 | 6 | 0.217 | KRAPIVSKY, P, REDNER, S, ANTAL, T, BENNAIM, E, LEYVRAZ, F, VAZQUEZ, F |
| 22 | 6 | 0.167 | RODGERS, G, TADIC, B, THURNER, S, ERGUN, G, DARBYDOWMAN, K, CARUSO, F |
| 23 | 6 | 0.143 | CASTELLANO, C, RADICCHI, F, CECCONI, F, LORETO, V, PARISI, D, VILONE, D |

Tác giả thuộc nhiều cộng đồng: 39.

| Tác giả | Cộng đồng: trọng số nối vào |
|---|---|
| ANTAL, T | 1: 1.00; 21: 1.00 |
| BENJACOB, E | 1: 1.00; 18: 1.75 |
| BENNAIM, E | 12: 1.00; 21: 1.00 |
| BIANCONI, G | 1: 2.00; 5: 1.00 |
| CARUSO, F | 7: 1.00; 22: 0.33 |
| CASTELLANO, C | 2: 1.00; 23: 1.50 |
| COHEN, I | 1: 1.00; 18: 0.75 |
| COSENZA, S | 7: 0.50; 16: 0.83 |
| CZIROK, A | 1: 1.00; 18: 0.75 |
| FLAMMINI, A | 2: 1.00; 11: 0.33 |
| FORTUNATO, S | 4: 1.00; 7: 1.00 |
| HAN, S | 1: 1.00; 3: 1.67 |
| HERRMANN, H | 2: 1.00; 15: 3.50 |
| HONG, D | 2: 1.00; 15: 0.50 |
| HONG, H | 1: 1.00; 3: 3.00 |
| HUSS, M | 1: 0.50; 3: 1.50 |
| KEPLER, T | 2: 0.67; 9: 0.67 |
| KINNEY, R | 1: 0.33; 7: 0.67 |
| KLEINBERG, J | 3: 1.00; 10: 1.00; 20: 1.00 |
| KRAPIVSKY, P | 1: 7.00; 21: 6.33 |
| LEYVRAZ, F | 1: 1.00; 21: 1.00 |
| LOPEZRUIZ, R | 2: 0.33; 6: 0.67 |
| MARITAN, A | 2: 1.00; 11: 3.33 |
| OSIPOV, G | 6: 0.75; 8: 1.75 |
| PELAEZ, A | 6: 0.50; 19: 0.50 |
| REDNER, S | 1: 6.00; 21: 5.33 |
| SCHNITZLER, A | 8: 1.00; 14: 2.00 |
| SCHWARTZ, N | 1: 0.25; 17: 0.75 |
| SHOCHET, O | 1: 1.00; 18: 0.75 |
| SMITH, E | 2: 1.17; 9: 1.17 |
| STAGNI, C | 7: 0.50; 16: 0.83 |
| TADIC, B | 7: 2.50; 22: 3.33 |
| THURNER, S | 7: 1.50; 22: 2.00 |
| USAI, L | 7: 0.50; 16: 0.83 |
| VALLADARES, D | 6: 2.50; 8: 1.00 |
| VAZQUEZ, F | 1: 1.00; 21: 1.00 |
| VILONE, D | 2: 1.00; 23: 0.50 |
| YOON, C | 1: 1.00; 3: 1.67 |
| ZHOU, C | 6: 0.75; 8: 2.25; 13: 0.50 |

## Mức thuộc do Pha II thêm

Kỳ vọng và p theo mô hình CCM của Pha II; p chưa hiệu chỉnh, BH mức q = 0.001 theo từng đỉnh.

| Mạng | Đỉnh | Cộng đồng | Trọng số nối vào lõi | Kỳ vọng | p |
|---|---|---:|---:|---:|---:|
| Não người | vùng 8 | 5 | 0.21 | 0.02 | 0.003 |
| Não người | vùng 15 | 5 | 0.32 | 0.02 | 0.00018 |
| Não người | vùng 17 | 5 | 0.26 | 0.03 | 0.0014 |
| Não người | vùng 23 | 6 | 0.24 | 0.04 | 0.0064 |
| Não người | vùng 25 | 2 | 1.09 | 0.44 | 0.0014 |
| Não người | vùng 64 | 7 | 0.26 | 0.04 | 0.004 |
| Não người | vùng 65 | 4 | 0.94 | 0.34 | 0.0038 |
| Não người | vùng 182 | 5 | 0.24 | 0.03 | 0.0032 |
| Não người | vùng 185 | 5 | 0.27 | 0.03 | 0.0006 |
| Não người | vùng 196 | 6 | 0.23 | 0.05 | 0.0099 |
| Não người | vùng 197 | 7 | 0.39 | 0.06 | 0.0011 |
| Não người | vùng 207 | 3 | 0.74 | 0.29 | 0.0045 |
| Não người | vùng 212 | 7 | 0.27 | 0.03 | 0.0015 |
| Não người | vùng 220 | 6 | 0.40 | 0.07 | 0.001 |
| Não người | vùng 239 | 4 | 0.84 | 0.17 | 4.7e-05 |
| Não người | vùng 259 | 7 | 0.46 | 0.06 | 0.00043 |
| Não người | vùng 271 | 6 | 0.47 | 0.09 | 0.0011 |
| Não người | vùng 276 | 6 | 0.31 | 0.05 | 0.0017 |
| Não người | vùng 282 | 6 | 0.42 | 0.08 | 0.002 |
| Não người | vùng 339 | 2 | 1.46 | 0.60 | 0.00063 |
| Não người | vùng 355 | 5 | 0.31 | 0.03 | 0.0011 |
| Não người | vùng 367 | 4 | 0.72 | 0.23 | 0.0038 |
| Não người | vùng 373 | 4 | 1.27 | 0.34 | 0.00011 |
| Não người | vùng 380 | 5 | 0.21 | 0.03 | 0.0063 |
| Não người | vùng 381 | 5 | 0.34 | 0.03 | 0.00048 |
| Não người | vùng 391 | 5 | 0.25 | 0.03 | 0.0017 |
| Não người | vùng 392 | 4 | 0.67 | 0.19 | 0.003 |
| Não người | vùng 393 | 4 | 0.95 | 0.33 | 0.0037 |
| Não người | vùng 395 | 5 | 0.34 | 0.03 | 0.00029 |
| Não người | vùng 402 | 5 | 0.35 | 0.03 | 0.00024 |
| Não người | vùng 408 | 5 | 0.31 | 0.05 | 0.0057 |
| Não người | vùng 409 | 5 | 0.34 | 0.03 | 0.00021 |
| Não người | vùng 414 | 4 | 1.12 | 0.36 | 0.0011 |
| Não người | vùng 423 | 5 | 0.24 | 0.03 | 0.0052 |
| Não người | vùng 426 | 5 | 0.37 | 0.02 | 6e-05 |
| Não người | vùng 429 | 5 | 0.22 | 0.02 | 0.0033 |
| Não người | vùng 435 | 5 | 0.31 | 0.02 | 0.0002 |
| Não người | vùng 435 | 6 | 0.17 | 0.03 | 0.012 |
| Não người | vùng 439 | 5 | 0.30 | 0.03 | 0.00046 |
| Não người | vùng 448 | 6 | 0.34 | 0.04 | 0.00044 |
| Não người | vùng 473 | 4 | 1.37 | 0.41 | 0.00021 |
| Não người | vùng 477 | 4 | 1.49 | 0.44 | 0.00011 |
| Não người | vùng 487 | 5 | 0.35 | 0.05 | 0.00096 |
| Não người | vùng 490 | 5 | 0.47 | 0.02 | 7e-07 |
| Não người | vùng 495 | 5 | 0.48 | 0.07 | 0.00024 |
| Não người | vùng 501 | 4 | 0.85 | 0.27 | 0.0017 |
| Não người | vùng 513 | 3 | 1.83 | 0.91 | 0.008 |
| Não người | vùng 517 | 7 | 0.25 | 0.02 | 0.0006 |
| Não người | vùng 532 | 7 | 0.33 | 0.07 | 0.008 |
| Não người | vùng 536 | 6 | 0.48 | 0.08 | 0.00029 |
| Não người | vùng 536 | 7 | 0.43 | 0.05 | 0.00015 |
| Não người | vùng 544 | 7 | 0.23 | 0.04 | 0.0057 |
| Não người | vùng 549 | 6 | 0.49 | 0.08 | 0.00029 |
| Não người | vùng 557 | 7 | 0.43 | 0.03 | 9.9e-06 |
| Não người | vùng 558 | 6 | 0.21 | 0.04 | 0.0094 |
| Não người | vùng 558 | 7 | 0.35 | 0.02 | 8.1e-05 |
| Não người | vùng 559 | 4 | 0.81 | 0.23 | 0.00073 |
| Não người | vùng 564 | 6 | 0.32 | 0.06 | 0.0029 |
| Não người | vùng 567 | 6 | 0.47 | 0.03 | 6.1e-06 |
| Não người | vùng 573 | 6 | 0.23 | 0.03 | 0.0054 |
| Não người | ... còn 8 mức thuộc | | | | |

## Độ ổn định khi bỏ 5% cạnh

Mỗi bản nhiễu bỏ ngẫu nhiên 5% số cạnh (hạt giống 2026 + r), không để đỉnh nào mất hết cạnh. ONMI và Omega so với tập bao phủ trên mạng gốc; mốc ngẫu nhiên: tập bao phủ gốc với nhãn đỉnh bị xáo (10 lần).

| Mạng | Phương pháp | Cộng đồng (gốc) | Cỡ lớn nhất (gốc) | Bản nhiễu ok | ONMI: trung vị (min-max) | Omega trung vị | ONMI mốc ngẫu nhiên | Cộng đồng sau nhiễu (min-max) |
|---|---|---:|---:|:---:|:---:|---:|---:|:---:|
| C. elegans | Phương pháp đề xuất | 2 | 186/279 | 10/10 | 0.911 (0.681-0.967) | 0.942 | 0.001 | 2-2 |
| C. elegans | wGHAC | chưa chạy | | | | | | |
| Đồng tác giả | Phương pháp đề xuất | 23 | 66/379 | 10/10 | 0.830 (0.758-0.972) | 0.856 | 0.000 | 23-28 |
| Đồng tác giả | wGHAC | chưa chạy | | | | | | |
| Não người | Phương pháp đề xuất | 7 | 300/638 | 10/10 | 0.558 (0.461-0.852) | 0.701 | 0.001 | 6-15 |
| Não người | wGHAC | chưa chạy | | | | | | |

## Thời gian chạy trên mạng gốc

| Mạng | Phương pháp đề xuất (s) | wGHAC (s) |
|---|---:|---:|
| C. elegans | 226 | chưa chạy |
| Đồng tác giả | 96 | chưa chạy |
| Não người | 230 | chưa chạy |
