from flask import Flask, jsonify
import requests
import os

ROMM_URL = "http://192.168.2.132:8285"
API_KEY = "rmm_1a90aaa293475819cd54a76f4f717f7cdb80281a24c5d839c8aa2759c270901d"

app = Flask(__name__)

def get_roms():
    r = requests.get(
        f"{ROMM_URL}/api/roms",
        headers={"X-API-Key": API_KEY}
    )
    return r.json()

@app.route("/cyberfoil.json")
def cyberfoil_feed():
    roms = get_roms()
    feed = []

    for rom in roms:
        rom_id = rom["id"]
        title = rom.get("title")
        title_id = rom.get("titleId")
        version = rom.get("version")
        size = rom.get("size")

        # Find the base .xci inside the folder
        files = rom.get("files", [])
        xci_files = [f for f in files if f.lower().endswith(".xci")]

        if not xci_files:
            continue  # skip if no base game

        base_xci = xci_files[0]

        file_url = f"{ROMM_URL}/api/roms/{rom_id}/files/content/{base_xci}"
        icon_url = f"{ROMM_URL}/api/roms/{rom_id}/icon"

        feed.append({
            "title": title,
            "titleId": title_id,
            "version": version,
            "iconUrl": icon_url,
            "url": file_url,
            "size": size
        })

    return jsonify(feed)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
