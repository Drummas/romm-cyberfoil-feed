from flask import Flask, Response, request, jsonify
from urllib.parse import unquote
import requests
import logging
import os
from urllib.parse import quote
import mimetypes

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

ROMM_URL = os.environ.get("ROMM_URL")
API_KEY = os.environ.get("API_KEY")

# ⭐ Your actual ROM storage base path
ROMM_STORAGE = "/romm/library/"


@app.after_request
def fix_headers(response):
    if response.mimetype == "application/json":
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Connection"] = "close"
    return response


def get_roms():
    try:
        url = f"{ROMM_URL}/api/roms?platform_ids=22&limit=10000"
        r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
        return r.json().get("items", [])
    except Exception as e:
        logging.error("ERROR fetching roms list: %s", e)
        return []


def get_full_rom(rom_id):
    try:
        detail_url = f"{ROMM_URL}/api/roms/{rom_id}"
        r = requests.get(detail_url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        logging.error("ERROR fetching rom detail %s: %s", rom_id, e)
        return None


@app.route("/api/shop/icon/<rom_id>")
def proxy_icon(rom_id):
    full_rom = get_full_rom(rom_id)
    if not full_rom:
        return Response("", status=404)

    icon_path = full_rom.get("path_cover_small") or full_rom.get("url_cover")
    if not icon_path:
        return Response("", status=404)

    if icon_path.startswith("/"):
        icon_url = f"{ROMM_URL}{icon_path}"
    else:
        icon_url = icon_path

    try:
        r = requests.get(icon_url, timeout=10)
        if r.status_code != 200:
            return Response("", status=404)

        mime = r.headers.get("Content-Type", "image/png")
        return Response(r.content, mimetype=mime)
    except Exception:
        return Response("", status=500)


# ⭐ CyberFoil-compatible file server with Range support
@app.route("/api/shop/file/<rom_id>/<filename>")
def serve_file(rom_id, filename):
    full_rom = get_full_rom(rom_id)
    
    logging.error(f"FILES: {[f.get('file_name') for f in full_rom.get('files', [])]}")
       
    if not full_rom:
        return Response("ROM not found", status=404)

    # ⭐ Decode URL-encoded filename
    decoded_filename = unquote(filename)

    file_entry = next(
        (
            f for f in full_rom.get("files", [])
            if f.get("file_name") == decoded_filename
        ),
        None
    )
    if not file_entry:
        return Response("File not found", status=404)

    rel_path = file_entry.get("full_path")
    abs_path = os.path.join(ROMM_STORAGE, rel_path)

    if not os.path.exists(abs_path):
        return Response("File missing on disk", status=404)

    file_size = os.path.getsize(abs_path)
    range_header = request.headers.get("Range", None)

    if range_header:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        end = int(bytes_range[1]) if bytes_range[1] else file_size - 1

        length = end - start + 1

        with open(abs_path, "rb") as f:
            f.seek(start)
            chunk = f.read(length)

        resp = Response(chunk, status=206)
        resp.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Length"] = str(length)
        resp.headers["Content-Type"] = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
        return resp

    with open(abs_path, "rb") as f:
        data = f.read()

    resp = Response(data, status=200)
    resp.headers["Content-Length"] = str(file_size)
    resp.headers["Content-Type"] = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    return resp


def build_item_from_rom(full_rom):
    name = full_rom.get("name", "Unknown")
    rom_id = full_rom.get("id")

    file_entry = next(
        (
            f for f in full_rom.get("files", [])
            if f.get("file_name", "").endswith(".xci")
            or f.get("file_name", "").endswith(".nsp")
        ),
        None
    )
    if not file_entry:
        return None

    filename = file_entry["file_name"]
    encoded_filename = quote(filename)

    # ⭐ CyberFoil will download from our Range-capable endpoint
    file_url = f"/api/shop/file/{rom_id}/{encoded_filename}"

    size = file_entry.get("file_size_bytes", 0)
    icon_url = f"/api/shop/icon/{rom_id}"

    return {
        "name": name,
        "url": file_url,
        "size": size,
        "icon_url": icon_url,
    }


@app.route("/api/shop/sections")
def shop_sections():
    roms = get_roms()
    items = []

    for rom in roms:
        full_rom = get_full_rom(rom["id"])
        if not full_rom:
            continue

        item = build_item_from_rom(full_rom)
        if item:
            items.append(item)

    sections = [
        {
            "id": "base",
            "title": "Games",
            "items": items,
        }
    ]

    return jsonify({
        "sections": sections,
        "success": "RomM Switch Library",
    })


@app.route("/")
def root_legacy():
    return jsonify({
        "sections": [],
        "success": "CyberFoil shop root",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8465)
