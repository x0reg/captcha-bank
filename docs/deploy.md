# Deploy Guide (Ubuntu + Python 3.9)

Project này nên deploy theo kiểu:

- Python `3.9`
- virtualenv riêng
- Flask app chạy nội bộ ở `127.0.0.1:8000`
- `systemd` để tự khởi động cùng máy
- tùy chọn dùng `nginx` reverse proxy ra port `80`

## 1. Cài Python 3.9

### Ubuntu 22.04 / 24.04

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3.9-dev
```

### Kiểm tra version

```bash
python3.9 --version
```

## 2. Chuẩn bị source

```bash
sudo mkdir -p /opt/captcha
sudo chown $USER:$USER /opt/captcha
cd /opt/captcha
```

Copy source project vào thư mục này rồi cài môi trường:

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Chạy thử app

Không nên chạy trực tiếp ở port `80`, vì port này thường cần quyền cao hoặc đã bị web server khác chiếm.

```bash
export CAPTCHA_HOST=127.0.0.1
export CAPTCHA_PORT=8000
python run.py
```

Test nhanh:

```bash
curl http://127.0.0.1:8000
```

Lưu ý: app này hiện chỉ khai báo các endpoint `POST`, nên nếu `curl /` trả `404` thì đó không phải lỗi deploy.

## 4. Tạo service bằng systemd

Tạo file service:

```bash
sudo nano /etc/systemd/system/captcha.service
```

Nội dung:

```ini
[Unit]
Description=Captcha Flask API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/captcha
Environment=CAPTCHA_HOST=127.0.0.1
Environment=CAPTCHA_PORT=8000
ExecStart=/opt/captcha/.venv/bin/python /opt/captcha/run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Nếu source đang thuộc user khác, cần cấp quyền đọc:

```bash
sudo chown -R www-data:www-data /opt/captcha
```

Nạp và chạy service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable captcha
sudo systemctl start captcha
sudo systemctl status captcha
```

Xem log:

```bash
sudo journalctl -u captcha -f
```

## 5. Reverse proxy bằng Nginx

Cài Nginx:

```bash
sudo apt update
sudo apt install -y nginx
```

Tạo config:

```bash
sudo nano /etc/nginx/sites-available/captcha
```

Nội dung:

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Kích hoạt cấu hình:

```bash
sudo ln -s /etc/nginx/sites-available/captcha /etc/nginx/sites-enabled/captcha
sudo nginx -t
sudo systemctl restart nginx
```

## 6. Update code khi deploy lại

```bash
cd /opt/captcha
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart captcha
```

## 7. Các lệnh vận hành

```bash
sudo systemctl status captcha
sudo systemctl restart captcha
sudo systemctl stop captcha
sudo journalctl -u captcha -f
sudo systemctl status nginx
```

## 8. Ghi chú thực tế

- Nếu Ubuntu của server không có sẵn `python3.9`, cài qua `deadsnakes` như trên.
- Không nên bind Flask trực tiếp ra `0.0.0.0:80`.
- Nếu cần public HTTPS, thêm SSL ở Nginx bằng Let's Encrypt.
- File model đang khá lớn, nên kiểm tra RAM server trước khi chạy TensorFlow.
