from flask import Flask, jsonify
import requests

ROMM_URL = "http://192.168.2.132:8285"
API_KEY = "rmm_1a90aaa293475819cd54a76f4f717f7cdb80281a24c5d839c8aa2759c270901d"

app = Flask(__name__)

def get_roms():
    r = requests.get(
        f"{ROMM_URL}/api/roms",
        headers={"X-API-Key": API_KEY}
    )
    print("DEBUG RAW RESPONSE:", r.text)   # ← IMPORTANT
    return r.json()["items"]               # ← CORRECT FOR YOUR ROMM

@app.route("/cyberfoil.json")
def cyberfoil_feed():
    roms = get_roms()
    feed = []

    for rom in roms:
        if rom["platform_slug"] != "switch":
            continue

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
