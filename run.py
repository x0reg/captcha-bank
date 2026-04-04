from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS, cross_origin

os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import model_from_json

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DOCS_DIR = BASE_DIR / "docs"
DEFAULT_HOST = os.getenv("CAPTCHA_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT") or os.getenv("CAPTCHA_PORT", "8099"))
DEPLOY_GUIDE_PATH = DOCS_DIR / "deploy.md"
API_GUIDE_TEXT = """# API Usage Guide

Base URL:
- local: `http://127.0.0.1:8099`
- docs page: `GET /`

Headers:
- `Content-Type: application/json`

Request body:
```json
{
  "imgbase64": "<base64-png>"
}
```

Endpoints:
- `POST /api/captcha/mb`: giai captcha MB Bank
- `POST /api/captcha/vcb`: giai captcha Vietcombank
- `POST /api/captcha/bidv`: giai captcha BIDV

Success response:
```json
{
  "status": "success",
  "captcha": "AB12C"
}
```

Error response:
```json
{
  "status": "error",
  "message": "imgbase64 is required"
}
```

Notes:
- `imgbase64` la phan base64 cua anh PNG.
- Khong can gui tien to `data:image/png;base64,`.
- Neu base64 sai dinh dang hoac anh bi loi, API se tra HTTP `400`.
"""

DOCS_TEMPLATE = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Captcha API Docs</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4efe8;
            --panel: #fffaf4;
            --border: #d9cbb8;
            --text: #231f1a;
            --muted: #6f6558;
            --accent: #9e3d22;
            --accent-soft: #f7e4d8;
            --code: #2b251f;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top left, rgba(158, 61, 34, 0.16), transparent 28%),
                linear-gradient(180deg, #f8f2ea 0%, var(--bg) 100%);
            color: var(--text);
        }

        main {
            max-width: 960px;
            margin: 0 auto;
            padding: 40px 20px 64px;
        }

        .hero,
        .card {
            background: rgba(255, 250, 244, 0.92);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 14px 40px rgba(47, 35, 24, 0.08);
        }

        .hero {
            padding: 28px;
            margin-bottom: 20px;
        }

        .eyebrow {
            display: inline-block;
            margin-bottom: 12px;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        h1, h2 {
            margin: 0 0 12px;
            line-height: 1.1;
        }

        p {
            margin: 0;
            color: var(--muted);
            line-height: 1.6;
        }

        .grid {
            display: grid;
            gap: 20px;
        }

        .grid-2 {
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }

        .card {
            padding: 24px;
        }

        ul {
            margin: 0;
            padding-left: 20px;
            color: var(--muted);
        }

        li + li {
            margin-top: 8px;
        }

        code,
        pre {
            font-family: Consolas, "Courier New", monospace;
        }

        pre {
            margin: 14px 0 0;
            padding: 16px;
            overflow-x: auto;
            border-radius: 14px;
            background: var(--code);
            color: #f7efe7;
            line-height: 1.5;
            font-size: 14px;
        }

        .routes {
            display: grid;
            gap: 12px;
            margin-top: 18px;
        }

        .route {
            padding: 14px 16px;
            border-radius: 14px;
            border: 1px solid var(--border);
            background: white;
        }

        .route strong {
            color: var(--accent);
        }

        .route span {
            display: block;
            margin-top: 6px;
            color: var(--muted);
            font-size: 14px;
        }

        a {
            color: var(--accent);
        }
    </style>
</head>
<body>
    <main>
        <section class="hero">
            <div class="eyebrow">Captcha API</div>
            <h1>Docs sử dụng API</h1>
            <p>Gửi ảnh captcha dưới dạng base64 qua JSON, API sẽ trả về chuỗi captcha đã nhận diện.</p>
        </section>

        <section class="grid">
            <article class="card">
                <h2>Tổng quan</h2>
                <pre>{{ api_guide }}</pre>
            </article>

            <article class="card">
                <h2>Endpoints</h2>
                <div class="routes">
                    {% for endpoint in endpoints %}
                    <div class="route">
                        <strong>{{ endpoint.method }} {{ endpoint.path }}</strong>
                        <span>{{ endpoint.description }}</span>
                    </div>
                    {% endfor %}
                </div>
            </article>

            <section class="grid grid-2">
                <article class="card">
                    <h2>Request body</h2>
                    <p>Body JSON dùng chung cho tất cả endpoint.</p>
                    <pre>{{ sample_payload }}</pre>
                </article>

                <article class="card">
                    <h2>Success response</h2>
                    <pre>{{ sample_response }}</pre>
                </article>

                <article class="card">
                    <h2>Error response</h2>
                    <pre>{{ error_response }}</pre>
                </article>

                <article class="card">
                    <h2>Ví dụ JavaScript</h2>
                    <pre>{{ js_example }}</pre>
                </article>
            </section>

            <article class="card">
                <h2>Ví dụ cURL</h2>
                <pre>{{ curl_example }}</pre>
            </article>

            <article class="card">
                <h2>Deploy guide</h2>
                <p>Nếu cần tài liệu triển khai server, xem thêm tại <a href="/docs/deploy">/docs/deploy</a>.</p>
            </article>
        </section>
    </main>
</body>
</html>
"""

TEXT_DOCS_TEMPLATE = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <style>
        body {
            margin: 0;
            padding: 32px 20px;
            background: #f4efe8;
            color: #231f1a;
            font-family: "Segoe UI", sans-serif;
        }

        main {
            max-width: 960px;
            margin: 0 auto;
        }

        h1 {
            margin: 0 0 16px;
        }

        a {
            color: #9e3d22;
        }

        pre {
            margin: 0;
            padding: 20px;
            overflow-x: auto;
            border-radius: 16px;
            background: #2b251f;
            color: #f7efe7;
            line-height: 1.55;
            font-size: 14px;
            font-family: Consolas, "Courier New", monospace;
        }
    </style>
</head>
<body>
    <main>
        <h1>{{ title }}</h1>
        <p><a href="/">Quay lại docs API</a></p>
        <pre>{{ content }}</pre>
    </main>
</body>
</html>
"""


def load_characters(file_name: str) -> list[str]:
    raw_content = (DATA_DIR / file_name).read_text(encoding="utf-8").strip()
    characters = ast.literal_eval(raw_content)
    if not isinstance(characters, list) or not all(isinstance(char, str) for char in characters):
        raise ValueError(f"Invalid character file: {file_name}")
    return characters


@dataclass(frozen=True)
class CaptchaConfig:
    width: int
    height: int
    max_length: int
    character_file: str
    model_json: str
    weights_file: str


class CaptchaService:
    def __init__(self, config: CaptchaConfig) -> None:
        self.config = config
        characters = load_characters(config.character_file)
        self.char_to_num = layers.StringLookup(vocabulary=characters, mask_token=None)
        self.num_to_char = layers.StringLookup(
            vocabulary=self.char_to_num.get_vocabulary(),
            mask_token=None,
            invert=True,
        )
        self.model = self._load_model()

    def _load_model(self):
        model_definition = (MODELS_DIR / self.config.model_json).read_text(encoding="utf-8")
        model = model_from_json(model_definition)
        model.load_weights(MODELS_DIR / self.config.weights_file)
        return model

    def _prepare_image(self, image_base64: str) -> np.ndarray:
        normalized = image_base64.replace("+", "-").replace("/", "_")
        image = tf.io.decode_base64(normalized)
        image = tf.io.decode_png(image, channels=1)
        image = tf.image.convert_image_dtype(image, tf.float32)
        image = tf.image.resize(image, [self.config.height, self.config.width])
        image = tf.transpose(image, perm=[1, 0, 2])
        return np.array([image])

    def _decode_predictions(self, predictions: np.ndarray) -> list[str]:
        input_len = np.full(predictions.shape[0], predictions.shape[1])
        decoded = keras.backend.ctc_decode(
            predictions,
            input_length=input_len,
            greedy=True,
        )[0][0][:, : self.config.max_length]
        results = []
        for item in decoded:
            value = tf.strings.reduce_join(self.num_to_char(item)).numpy().decode("utf-8")
            results.append(value.replace("[UNK]", "").replace("-", ""))
        return results

    def predict(self, image_base64: str) -> str:
        predictions = self.model.predict(self._prepare_image(image_base64), verbose=0)
        return self._decode_predictions(predictions)[0]


CAPTCHA_SERVICES = {
    "mb": CaptchaService(
        CaptchaConfig(
            width=320,
            height=80,
            max_length=15,
            character_file="char_mb.txt",
            model_json="model_mb.json",
            weights_file="model_mb.h5",
        )
    ),
    "vcb": CaptchaService(
        CaptchaConfig(
            width=320,
            height=80,
            max_length=15,
            character_file="char_vcb.txt",
            model_json="model_vcb.json",
            weights_file="model_vcb.h5",
        )
    ),
    "bidv": CaptchaService(
        CaptchaConfig(
            width=200,
            height=50,
            max_length=5,
            character_file="char_bidv.txt",
            model_json="model_bidv.json",
            weights_file="weights.keras",
        )
    ),
}

app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


def make_prediction_response(service_name: str):
    payload = request.get_json(silent=True) or {}
    image_base64 = payload.get("imgbase64")
    if not image_base64:
        return jsonify(status="error", message="imgbase64 is required"), 400

    try:
        captcha = CAPTCHA_SERVICES[service_name].predict(image_base64)
    except (tf.errors.InvalidArgumentError, ValueError, TypeError) as exc:
        return jsonify(status="error", message=str(exc)), 400

    return jsonify(status="success", captcha=captcha)


def build_absolute_url(path: str) -> str:
    root_url = request.url_root.rstrip("/") + "/"
    return urljoin(root_url, path.lstrip("/"))


@app.route("/", methods=["GET"])
@app.route("/docs", methods=["GET"])
def docs_view():
    endpoints = [
        {
            "method": "POST",
            "path": "/api/captcha/mb",
            "description": "Giai captcha MB Bank.",
        },
        {
            "method": "POST",
            "path": "/api/captcha/vcb",
            "description": "Giai captcha Vietcombank.",
        },
        {
            "method": "POST",
            "path": "/api/captcha/bidv",
            "description": "Giai captcha BIDV.",
        },
    ]
    mb_url = build_absolute_url("/api/captcha/mb")
    return render_template_string(
        DOCS_TEMPLATE,
        endpoints=endpoints,
        api_guide=API_GUIDE_TEXT,
        sample_payload='{\n  "imgbase64": "<base64-png>"\n}',
        sample_response='{\n  "status": "success",\n  "captcha": "AB12C"\n}',
        error_response='{\n  "status": "error",\n  "message": "imgbase64 is required"\n}',
        curl_example=(
            f"curl -X POST {mb_url} \\\n"
            '  -H "Content-Type: application/json" \\\n'
            '  -d "{\\"imgbase64\\": \\"<base64-png>\\"}"'
        ),
        js_example=(
            "const response = await fetch('/api/captcha/mb', {\n"
            "  method: 'POST',\n"
            "  headers: { 'Content-Type': 'application/json' },\n"
            "  body: JSON.stringify({ imgbase64: '<base64-png>' }),\n"
            "});\n\n"
            "const data = await response.json();\n"
            "console.log(data);"
        ),
    )


@app.route("/docs/deploy", methods=["GET"])
def deploy_docs_view():
    return render_template_string(
        TEXT_DOCS_TEMPLATE,
        title="Deploy Guide",
        content=DEPLOY_GUIDE_PATH.read_text(encoding="utf-8").strip(),
    )


@app.route("/api/captcha/mb", methods=["POST"])
@cross_origin(origin="*")
def predict_mb():
    return make_prediction_response("mb")


@app.route("/api/captcha/vcb", methods=["POST"])
@cross_origin(origin="*")
def predict_vcb():
    return make_prediction_response("vcb")


@app.route("/api/captcha/bidv", methods=["POST"])
@cross_origin(origin="*")
def predict_bidv():
    return make_prediction_response("bidv")


if __name__ == "__main__":
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT)
