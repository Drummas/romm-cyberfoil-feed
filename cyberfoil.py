from flask import Flask, jsonify
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

ROMM_URL = os.environ.get("ROMM_URL")
API_KEY = os.environ.get("API_KEY")

def get_roms():
    try:
        url = (
            f"{ROMM_URL}/api/roms"
            "?platform_ids=22"
            "&limit=10000"
        )

        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5
        )

        logging.info("DEBUG URL: %s", url)
        logging.info("DEBUG STATUS: %s", r.status_code)
        logging.info("DEBUG RAW RESPONSE: %s", r.text[:500])

        data = r.json()
        return data.get("items", [])
    except Exception as e:
        logging.error("DEBUG ERROR: %s", e)
        return []

@app.route("/cyberfoil.json")
def cyberfoil_feed():
    roms = get_roms()
    feed = []

    for rom in roms:
        title = rom["name"]
        size = rom["fs_size_bytes"]
        file_path = rom["full_path"]
        icon = rom["path_cover_small"] or rom["url_cover"]

        file_url = f"{ROMM_URL}/library/{file_path}"

        feed.append({
            "title": title,
            "size": size,
            "url": file_url,
            "iconUrl": icon
        })

    return jsonify(feed)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
