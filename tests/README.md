# Test Tìm Kiếm Thí Sinh

## Cấu trúc thư mục
```
tests/
├── data/
│   └── input/          # Chứa file data_search.xlsx
├── output/
│   ├── results/        # Kết quả test
│   └── logs/          # File logs
└── scripts/
    ├── search_test.py # Script chính
    └── utils.py       # Các hàm tiện ích
```

## Chuẩn bị
1. Đặt file `data_search.xlsx` vào thư mục `data/input/`
2. File Excel phải có 3 cột:
   - MÃ THÍ SINH
   - HỌ VÀ TÊN
   - CMND/CCCD

## Cài đặt thư viện
```bash
pip install pandas requests matplotlib seaborn
```

## Chạy test
```bash
cd scripts
python search_test.py
```

## Kết quả
1. File Excel chứa kết quả chi tiết trong thư mục `output/results/`
2. File log trong thư mục `output/logs/`
3. Biểu đồ hiệu suất trong thư mục `output/results/`

## Các loại test
1. Tìm theo một trường:
   - Mã thí sinh
   - Họ và tên
   - CMND/CCCD

2. Tìm theo nhiều trường:
   - Họ tên + CMND/CCCD
   - Tất cả các trường

## Báo cáo kết quả
1. Detailed Results: Kết quả chi tiết từng lần test
2. Statistics: Thống kê tổng hợp
3. Search Type Stats: Thống kê theo loại tìm kiếm
4. Biểu đồ:
   - Thời gian phản hồi theo loại tìm kiếm
   - Số lượng kết quả theo loại tìm kiếm 