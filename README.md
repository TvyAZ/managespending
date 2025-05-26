# Bot Quản Lý Chi Tiêu Telegram

Bot Telegram giúp bạn theo dõi thu nhập, chi tiêu và quản lý ngân sách cá nhân.

## Tính năng

- 💰 Thêm thu nhập theo danh mục
- 💸 Thêm chi tiêu theo danh mục  
- 📊 Xem tổng kết thu chi hàng tháng
- 🎯 Đặt ngân sách cho từng danh mục
- 📈 Kiểm tra tình trạng ngân sách với cảnh báo màu
- 📝 Xem lịch sử giao dịch gần đây
- 🗑️ Xóa giao dịch cuối cùng
- 📋 Danh mục thu chi được định nghĩa sẵn
- 💚 Hiển thị số dư (thu - chi)

## Cài đặt

1. **Tạo Bot Telegram**
   - Nhắn tin cho @BotFather trên Telegram
   - Sử dụng lệnh `/newbot`
   - Làm theo hướng dẫn để tạo bot
   - Sao chép token của bot

2. **Cài đặt thư viện**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình môi trường**
   ```bash
   cp .env.example .env
   # Chỉnh sửa file .env và thêm token bot của bạn
   ```

4. **Chạy Bot**
   ```bash
   python spending_bot.py
   ```

**Hoặc sử dụng script thiết lập tự động:**
```bash
python setup.py
```

## Cách sử dụng

### Lệnh chính

- `/start` - Khởi động bot và hiển thị menu chính
- `/in <số tiền> <danh mục> [mô tả]` - Thêm thu nhập
- `/out <số tiền> <danh mục> [mô tả]` - Thêm chi tiêu
- `/summary` - Xem tổng kết thu chi tháng này
- `/budget <danh mục> <số tiền>` - Đặt ngân sách tháng cho danh mục
- `/status` - Kiểm tra tình trạng ngân sách
- `/history` - Xem lịch sử giao dịch gần đây
- `/delete` - Xóa giao dịch cuối cùng
- `/clear <password>` - Xóa toàn bộ dữ liệu (password: `deleteall`)
- `/categories` - Xem danh mục thu chi
- `/help` - Hiển thị hướng dẫn

### Ví dụ sử dụng

```
/in 5m wrk Lương tháng 5
/in 200k ano Tiền thưởng
/out 50k eat Cafe sáng
/out 100k ent Xem phim
/budget eat 1m
/budget ent 500k
/summary
/status
/history
/delete
```

**Hỗ trợ định dạng số tiền:**
- Không có đơn vị = tự động "k": `50` = `50,000 VND`
- Sử dụng `k` cho nghìn: `500k` = `500,000 VND`
- Sử dụng `m` cho triệu: `5m` = `5,000,000 VND`

### Danh mục

#### THU NHẬP:
- `wrk` - 💼 Công việc (lương, dự án, thu nhập chính)
- `ano` - 💰 Khác (quà tặng, hỗ trợ, thưởng, lãi)

#### CHI TIÊU:
- `shp` - 🛍️ Mua sắm (đồ dùng cá nhân, gia đình)
- `eat` - 🍽️ Ăn uống (ăn ngoài, đi chợ, cafe)
- `ser` - 🔧 Dịch vụ (cắt tóc, sửa chữa, tiền điện/nước)
- `ent` - 🎬 Giải trí (xem phim, du lịch, game)
- `inv` - 📈 Đầu tư (cổ phiếu, tiết kiệm, góp vốn)
- `wrk` - 💼 Công việc (chi phí phục vụ công việc)
- `ano` - 📦 Khác (từ thiện, quà tặng, tiền phạt)

## Cơ sở dữ liệu

Bot sử dụng SQLite (`spending.db`) để lưu trữ:
- Giao dịch thu chi với số tiền, danh mục, mô tả và thời gian
- Ngân sách tháng cho từng danh mục
- Dữ liệu riêng biệt cho từng người dùng

## Tính năng chính

### Theo dõi Thu Chi
- Thêm thu nhập/chi tiêu với số tiền, danh mục và mô tả
- Tự động ghi nhận ngày giờ
- Xem tổng kết theo danh mục cho tháng hiện tại
- Hiển thị số dư (tổng thu - tổng chi)

### Quản lý Ngân sách
- Đặt ngân sách tháng cho bất kỳ danh mục chi tiêu nào
- Theo dõi chi tiêu so với ngân sách
- Chỉ báo trạng thái bằng màu (🟢🟡🔴)
- Tính toán phần trăm và số tiền còn lại

### Giao diện
- Nút bấm nhanh cho các chức năng chính
- Hệ thống menu tương tác
- Thông báo trạng thái rõ ràng
- Thông báo lỗi hữu ích

## Cấu trúc file

```
managespending/
├── spending_bot.py      # Ứng dụng bot chính
├── setup.py            # Script thiết lập tự động
├── requirements.txt     # Thư viện Python cần thiết
├── .env.example        # Template môi trường
├── .env               # Token bot của bạn (tạo file này)
├── spending.db        # Cơ sở dữ liệu SQLite (tự động tạo)
└── README.md          # File này
```

## Đóng góp

Chào mừng đóng góp bằng cách:
- Thêm tính năng mới
- Cải thiện giao diện người dùng
- Thêm danh mục chi tiêu
- Thực hiện tính năng xuất dữ liệu
- Thêm phân tích chi tiêu

## Bảo mật

- Giữ token bot an toàn và không commit vào version control
- File `.env` được gitignore để bảo mật
- Dữ liệu của mỗi người dùng được tách biệt bằng user ID