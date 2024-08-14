from base64 import b64encode

import qrcode
from qrcode.main import QRCode
from qrcode.util import QRData
from io import BytesIO

cache = {}


def make(data: str):
    qr = QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(QRData(data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def make_base64(data: str):
    if data in cache[data]:
        return cache[data]
    image = make(data)
    buffer = BytesIO()
    image.save(buffer)
    img_str = str(b64encode(buffer.getvalue()).decode())
    cache[data] = img_str
    return img_str
