# Python Captcha API

Project này cung cấp 3 endpoint giải captcha:

- `POST /api/captcha/mb`
- `POST /api/captcha/vcb`
- `POST /api/captcha/bidv`

## Cấu trúc

- `run.py`: entrypoint Flask API
- `models/`: model JSON, weights, artifact liên quan
- `data/`: character sets cho từng model
- `docs/`: ghi chú triển khai

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
