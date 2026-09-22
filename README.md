# Hũ Chi Tiêu - Gia Đình

Theo dõi thu nhập, chi tiêu và tiết kiệm của gia đình theo tháng.
Dữ liệu đồng bộ qua **GitHub Gist** — dùng trên điện thoại hay máy tính đều được.

## Setup đồng bộ (chỉ cần 1 lần)

### Bước 1: Tạo GitHub Personal Access Token
1. Vào [github.com/settings/tokens](https://github.com/settings/tokens)
2. Bấm **Generate new token (classic)**
3. Đặt tên: `hu-chi-tieu`
4. Chọn quyền: **gist**
5. Bấm **Generate token** → copy token

### Bước 2: Tạo Gist
1. Vào [gist.github.com](https://gist.github.com)
2. Tạo file mới tên `hu_chitieu_data.json`, nội dung: `{}`
3. Bấm **Create public gist**
4. Copy **Gist ID** từ URL:
   ```
   https://gist.github.com/abc123【ĐÂY LÀ GIST_ID】
   ```

### Bước 3: Thêm Secrets trên Streamlit Cloud
1. Vào [share.streamlit.io](https://share.streamlit.io)
2. Chọn app → menu ⋮ → **Settings** → **Secrets**
3. Paste:
```toml
GITHUB_TOKEN = "ghp_abc123..."
GIST_ID = "abc123..."
```
4. Bấm **Save** → app tự redeploy

## Chạy local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tính năng

### Tab 1 - Thu nhập
- Thu nhập cố định theo người (Duy, Hà)
- Thu nhập phát sinh (thưởng, lãi...)
- Biểu đồ thu nhập

### Tab 2 - Chi tiêu
- 6 nhóm: Cơm nước, DV chung cư, Điện nước, Giáo dục + y tế, Bỉm sửa + bánh kẹo, Khác
- Biểu đồ cột + pie chart

### Tab 3 - Tiết kiệm
- Tổng quan thu - chi - tiết kiệm
- So sánh với tháng trước
- Xu hướng qua các tháng
- Bảng lịch sử số dư lũy kế
- Ghi chú

### Quản lý tháng
- Tạo tháng mới + copy dữ liệu tháng trước
- Xóa tháng (2 bước xác nhận)

### Khác
- Đồng bộ GitHub Gist — sửa trên điện thoại máy tính đều sync
- Import/Export JSON
- Responsive trên điện thoại
