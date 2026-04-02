from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, jsonify, request
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
DEFAULT_HOST = os.getenv("CAPTCHA_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT") or os.getenv("CAPTCHA_PORT", "8099"))


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
