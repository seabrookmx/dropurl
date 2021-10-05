import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
import os
import subprocess
import random
from string import ascii_lowercase

BUFF_SIZE = 81920
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
MAX_DIR_SIZE_BYTES = MAX_FILE_SIZE_BYTES * 50  # ~5GB

FILE_ROOT = os.environ.get('FILE_ROOT', '../files/')
URL_PREFIX = os.environ.get('URL_PREFIX', 'https://something.dev/')


def dir_size() -> int:
    return int(subprocess.check_output([
        'du',
        '-b',
        FILE_ROOT,
    ]).split()[0].decode('utf-8'))


def get_name(extension: str) -> str:
    for i in range(3):
        rand = ''.join(random.choice(ascii_lowercase) for i in range(7))
        name = rand + extension
        path = os.path.join(FILE_ROOT, name)
        if os.path.exists(path):
            continue

        return name

    raise SystemError('RNG is broken')


app = FastAPI()
api = FastAPI()
app.mount("/api", api)
app.mount("/", StaticFiles(directory="../static"), name="static")


@api.get("/healthcheck")
async def root():
    return {"healthy": "yes"}


@api.post("/upload/", status_code=201)
async def create_upload_file(file: UploadFile = File(...)):
    if dir_size() > MAX_DIR_SIZE_BYTES:
        raise HTTPException(status_code=507, detail="Storage limit reached")

    fn_parts = file.filename.split('.')
    extension = '.' + fn_parts[len(fn_parts) - 1:][0]

    rng_filename = get_name(extension)

    async with aiofiles.open(
            os.path.join(FILE_ROOT, rng_filename), mode='wb') as out_file:
        total_bytes = 0
        bytes_read = 1
        while bytes_read > 0:
            bytes = await file.read(BUFF_SIZE)
            bytes_read = len(bytes)
            total_bytes += bytes_read

            if total_bytes > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="File too large")

            await out_file.write(bytes)

    return {'filename': URL_PREFIX + rng_filename}

print('Booted..')
