# Hũ Chi Tiêu - Gia Đình

Theo dõi thu nhập, chi tiêu và tiết kiệm của gia đình theo tháng.
Dữ liệu đồng bộ qua **Google Sheets** — dùng trên điện thoại hay máy tính đều được.

## Setup Google Sheets (bắt buộc)

### Bước 1: Tạo Google Sheet
1. Vào [sheets.google.com](https://sheets.google.com) → tạo Sheet mới
2. Đặt tên bất kỳ (VD: "Hũ Chi Tiêu")
3. Copy **Sheet ID** từ URL:
   ```
   https://docs.google.com/spreadsheets/d/【SHEET_ID】/edit
   ```

### Bước 2: Tạo Service Account
1. Vào [console.cloud.google.com](https://console.cloud.google.com)
2. Tạo project mới (hoặc chọn project có sẵn)
3. Bật **Google Sheets API**: Library → tìm "Google Sheets API" → Enable
4. Tạo Service Account:
   - IAM & Admin → Service Accounts → Create
   - Đặt tên (VD: "streamlit-app")
   - Bấm Continue → Done
5. Vào Service Account vừa tạo → Keys → Add Key → Create new key → **JSON**
6. Download file JSON

### Bước 3: Share Sheet cho Service Account
1. Mở file JSON vừa download, copy email trong trường `client_email`
2. Vào Google Sheet → Share → paste email Service Account → Editor → Send

### Bước 4: Cấu hình trên Streamlit Cloud
1. Vào app trên Streamlit Cloud → Menu (⋮) → **Settings** → **Secrets**
2. Paste nội dung sau (thay `SHEET_ID` và nội dung file JSON):

```toml
SHEET_ID = "abc123xyz..."

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n"
client_email = "streamlit-app@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-app%40your-project.iam.gserviceaccount.com"
```

3. Bấm **Save** → **Redeploy**

### Bước 5: Chạy local (tùy chọn)
Tạo file `.streamlit/secrets.toml` trong thư mục project:
```toml
SHEET_ID = "abc123xyz..."

[gcp_service_account]
type = "service_account"
# ... paste nội dung từ file JSON của Service Account
```

## Chạy local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tính năng

### Tab 1 - Thu nhập
- Quản lý thu nhập cố định theo người (Duy, Hà)
- Thêm/sửa/xóa thu nhập phát sinh (thưởng, lãi...)
- Biểu đồ thu nhập theo người

### Tab 2 - Chi tiêu
- 6 nhóm: Cơm nước, DV chung cư, Điện nước, Giáo dục + y tế, Bỉm sửa + bánh kẹo, Khác
- Biểu đồ cột + pie chart phân bổ

### Tab 3 - Tiết kiệm
- Tổng quan thu - chi - tiết kiệm
- So sánh với tháng trước (delta)
- Biểu đồ xu hướng + chi tiêu theo nhóm
- Bảng lịch sử số dư lũy kế
- Ghi chú mỗi tháng

### Quản lý tháng
- Tạo tháng mới + copy dữ liệu tháng trước
- Xóa tháng (2 bước xác nhận)

### Khác
- Đồng bộ Google Sheets — dùng trên điện thoại anytime
- Import/Export JSON
- Responsive trên mobile
