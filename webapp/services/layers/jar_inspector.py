# webapp/services/layers/jar_inspector.py

import io
import zipfile

def has_native_image_metadata(jar_bytes):
    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as jar:
        for file_name in jar.namelist():
            if file_name.startswith("META-INF/native-image/"):
                return True
    return False
