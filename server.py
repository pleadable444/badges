from flask import Flask, jsonify, request
import requests, time

app = Flask(__name__)

BASE_USERS  = "https://users.roblox.com"
BASE_BADGES = "https://badges.roblox.com"
DELAY       = 0.2

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

@app.route("/lookup")
def lookup():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid user ID"}), 400

    try:
        user = get_json(f"{BASE_USERS}/v1/users/{user_id}")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

    # Fetch all badges (paginated)
    badges = []
    cursor = ""
    for _ in range(50):  # max 50 pages = 5000 badges
        params = {"limit": 100, "sortOrder": "Asc"}
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

    # Enrich missing universe info (cap at 60 to keep response fast)
    for badge in badges[:60]:
        if not (badge.get("awardingUniverse") or {}).get("name"):
            try:
                detail = get_json(f"{BASE_BADGES}/v1/badges/{badge['id']}")
                if detail.get("awardingUniverse"):
                    badge["awardingUniverse"] = detail["awardingUniverse"]
            except:
                pass
            time.sleep(DELAY)

    # Group by game
    games_map = {}
    games_order = []
    for badge in badges:
        u = badge.get("awardingUniverse") or {}
        name = u.get("name") or "[Deleted Game]"
        if name not in games_map:
            games_map[name] = {
                "name": name,
                "placeId": u.get("rootPlaceId", 0),
                "badges": []
            }
            games_order.append(name)
        games_map[name]["badges"].append({
            "name": badge.get("name", ""),
            "id": badge.get("id", 0),
            "created": badge.get("created", "")
        })

    games_order.sort(key=str.lower)
    games = [games_map[n] for n in games_order]

    return jsonify({
        "success": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "displayName": user.get("displayName"),
            "isBanned": user.get("isBanned", False),
            "created": user.get("created", "")
        },
        "badgeCount": len(badges),
        "gameCount": len(games),
        "games": games
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)