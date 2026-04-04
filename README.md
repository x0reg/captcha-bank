# Python Captcha API

Project này cung cấp 3 endpoint giải captcha:

- `GET /`
- `GET /docs`
- `GET /docs/deploy`
- `POST /api/captcha/mb`
- `POST /api/captcha/vcb`
- `POST /api/captcha/bidv`

## Cấu trúc

- `run.py`: entrypoint Flask API
- `models/`: model JSON, weights, artifact liên quan
- `data/`: character sets cho từng model
- `docs/`: ghi chú triển khai

Khi mở `/`, app sẽ hiển thị docs hướng dẫn gọi API.
Deploy guide được giữ riêng ở `GET /docs/deploy`.

## Chạy local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Biến môi trường hỗ trợ:

- `CAPTCHA_HOST` mặc định `0.0.0.0`
- `CAPTCHA_PORT` mặc định `80`
