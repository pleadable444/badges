from flask import Flask, jsonify, request
import requests, time

app = Flask(__name__)

BASE_USERS     = "https://users.roblox.com"
BASE_BADGES    = "https://badges.roblox.com"
BASE_THUMBS    = "https://thumbnails.roblox.com"
BASE_ECONOMY   = "https://economy.roblox.com"
DELAY          = 0.2

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

@app.route("/user-by-name")
def user_by_name():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "error": "No username provided"}), 400
    try:
        data = requests.post(
            f"{BASE_USERS}/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
            timeout=10
        ).json()
        users = data.get("data", [])
        if not users:
            return jsonify({"success": False, "error": "User not found"}), 404
        return jsonify({"success": True, "id": users[0]["id"], "name": users[0]["name"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/thumbnail")
def thumbnail():
    place_id = request.args.get("placeId", "")
    if not place_id.isdigit():
        return jsonify({"success": False, "error": "Invalid placeId"}), 400
    try:
        data = get_json(f"{BASE_THUMBS}/v1/games/icons", params={
            "universeIds": place_id,
            "returnPolicy": "PlaceHolder",
            "size": "150x150",
            "format": "Png",
            "isCircular": False
        })
        imgs = data.get("data", [])
        if imgs:
            return jsonify({"success": True, "url": imgs[0].get("imageUrl", "")})
        return jsonify({"success": False, "error": "No thumbnail found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/game-icon")
def game_icon():
    universe_id = request.args.get("universeId", "")
    if not universe_id.isdigit():
        return jsonify({"success": False, "error": "Invalid universeId"}), 400
    try:
        data = get_json(f"{BASE_THUMBS}/v1/games/icons", params={
            "universeIds": universe_id,
            "returnPolicy": "PlaceHolder",
            "size": "150x150",
            "format": "Png",
            "isCircular": False
        })
        imgs = data.get("data", [])
        if imgs:
            return jsonify({"success": True, "url": imgs[0].get("imageUrl", "")})
        return jsonify({"success": False, "error": "No thumbnail"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/badge-thumbnail")
def badge_thumbnail():
    badge_id = request.args.get("badgeId", "")
    if not badge_id.isdigit():
        return jsonify({"success": False, "error": "Invalid badgeId"}), 400
    try:
        data = get_json(f"{BASE_THUMBS}/v1/badges/icons", params={
            "badgeIds": badge_id,
            "size": "150x150",
            "format": "Png",
            "isCircular": False
        })
        imgs = data.get("data", [])
        if imgs:
            return jsonify({"success": True, "url": imgs[0].get("imageUrl", "")})
        return jsonify({"success": False, "error": "No thumbnail"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/lookup")
def lookup():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid user ID"}), 400

    try:
        user = get_json(f"{BASE_USERS}/v1/users/{user_id}")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

    badges = []
    cursor = ""
    for _ in range(50):
        params = {"limit": 100, "sortOrder": "Desc"} 
        if cursor:
            params["cursor"] = cursor
        try:
            data = get_json(f"{BASE_BADGES}/v1/users/{user_id}/badges", params)
        except:
            break
        badges.extend(data.get("data", []))
        cursor = data.get("nextPageCursor") or ""
        if not cursor:
            break
        time.sleep(DELAY)

    for badge in badges[:60]:
        if not (badge.get("awardingUniverse") or {}).get("name"):
            try:
                detail = get_json(f"{BASE_BADGES}/v1/badges/{badge['id']}")
                if detail.get("awardingUniverse"):
                    badge["awardingUniverse"] = detail["awardingUniverse"]
            except:
                pass
            time.sleep(DELAY)

    games_map   = {}
    games_order = []

    for badge in badges:
        u        = badge.get("awardingUniverse") or {}
        universe_id = u.get("id") or 0
        key      = str(universe_id) if universe_id else f"deleted_{badge.get('id', 0)}"
        name     = u.get("name") or "[Content Deleted]"
        place_id = u.get("rootPlaceId", 0)

        if key not in games_map:
            games_map[key] = {
                "name":       name,
                "universeId": universe_id,
                "placeId":    place_id,
                "badges":     []
            }
            games_order.append(key)

        games_map[key]["badges"].append({
            "name":        badge.get("name", ""),
            "id":          badge.get("id", 0),
            "created":     badge.get("created", ""),
            "awardedDate": badge.get("awardedDate", "")
        })

    games = [games_map[k] for k in games_order]

    return jsonify({
        "success":    True,
        "user": {
            "id":          user.get("id"),
            "name":        user.get("name"),
            "displayName": user.get("displayName"),
            "isBanned":    user.get("isBanned", False),
            "created":     user.get("created", "")
        },
        "badgeCount": len(badges),
        "gameCount":  len(games),
        "games":      games
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
