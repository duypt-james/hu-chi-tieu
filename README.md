# Hũ Chi Tiêu - Gia Đình

Theo dõi thu nhập, chi tiêu và tiết kiệm của gia đình theo tháng.

## Deploy lên Streamlit Cloud

1. Tạo repo mới trên GitHub
2. Upload file: `app.py` và `requirements.txt`
3. Vào [share.streamlit.io](https://share.streamlit.io)
4. Bấm **New app** → chọn repo → nhập `app.py` → bấm **Deploy**

## Chạy local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tính năng 3 tab

### Tab 1 - Thu nhập
- Quản lý thu nhập cố định theo người (Duy, Hà)
- Thêm/sửa/xóa thu nhập phát sinh (thưởng, lãi...)
- Biểu đồ thu nhập theo người

### Tab 2 - Chi tiêu
- 6 nhóm chi tiêu: Cơm nước, DV chung cư, Điện nước, Giáo dục + y tế, Bỉm sửa + bánh kẹo, Khác
- Biểu đồ cột + pie chart phân bổ
- Hiển thị % chi tiêu mỗi nhóm

### Tab 3 - Tiết kiệm
- Tổng quan thu - chi - tiết kiệm tháng hiện tại
- Biểu đồ xu hướng qua các tháng
- Bảng lịch sử số dư lũy kế

### Quản lý tháng
- Tạo tháng mới (năm + tháng)
- Xóa tháng (có xác nhận)
- Chuyển qua lại giữa các tháng

### Khác
- Import/Export dữ liệu dạng JSON
- Responsive trên điện thoại
