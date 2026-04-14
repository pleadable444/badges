from flask import Flask, jsonify, request
import requests, time

app = Flask(__name__)

BASE_USERS     = "https://users.roblox.com"
BASE_BADGES    = "https://badges.roblox.com"
BASE_THUMBS    = "https://thumbnails.roblox.com"
BASE_GROUPS    = "https://groups.roblox.com"
BASE_FRIENDS   = "https://friends.roblox.com"
BASE_GAMES     = "https://games.roblox.com"
DELAY          = 0.1

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# ── /user-by-name ──────────────────────────────────────────────────────────
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

# ── /game-icon ─────────────────────────────────────────────────────────────
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

# ── /badge-thumbnail ───────────────────────────────────────────────────────
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

# ── /avatar-thumbnail ──────────────────────────────────────────────────────
@app.route("/avatar-thumbnail")
def avatar_thumbnail():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid userId"}), 400
    try:
        data = get_json(f"{BASE_THUMBS}/v1/users/avatar-headshot", params={
            "userIds": user_id,
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

# ── /group-icon ────────────────────────────────────────────────────────────
@app.route("/group-icon")
def group_icon():
    group_id = request.args.get("groupId", "")
    if not group_id.isdigit():
        return jsonify({"success": False, "error": "Invalid groupId"}), 400
    try:
        data = get_json(f"{BASE_THUMBS}/v1/groups/icons", params={
            "groupIds": group_id,
            "size": "150x150",
            "format": "Png",
            "isCircular": False
        })
        imgs = data.get("data", [])
        if imgs:
            return jsonify({"success": True, "url": imgs[0].get("imageUrl", "")})
        return jsonify({"success": False, "error": "No group icon"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── /profile ───────────────────────────────────────────────────────────────
# Returns: user info, avatar URL, description, friend count, follower count
@app.route("/profile")
def profile():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid userId"}), 400
    try:
        user = get_json(f"{BASE_USERS}/v1/users/{user_id}")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

    # Avatar headshot
    avatar_url = ""
    try:
        data = get_json(f"{BASE_THUMBS}/v1/users/avatar-headshot", params={
            "userIds": user_id,
            "size": "150x150",
            "format": "Png",
            "isCircular": False
        })
        imgs = data.get("data", [])
        if imgs:
            avatar_url = imgs[0].get("imageUrl", "")
    except:
        pass

    # Friend count
    friend_count = 0
    try:
        fc = get_json(f"{BASE_FRIENDS}/v1/users/{user_id}/friends/count")
        friend_count = fc.get("count", 0)
    except:
        pass

    # Follower count
    follower_count = 0
    try:
        fc = get_json(f"{BASE_FRIENDS}/v1/users/{user_id}/followers/count")
        follower_count = fc.get("count", 0)
    except:
        pass

    return jsonify({
        "success":       True,
        "id":            user.get("id"),
        "name":          user.get("name"),
        "displayName":   user.get("displayName"),
        "description":   user.get("description", ""),
        "isBanned":      user.get("isBanned", False),
        "created":       user.get("created", ""),
        "avatarUrl":     avatar_url,
        "friendCount":   friend_count,
        "followerCount": follower_count,
    })

# ── /friends ───────────────────────────────────────────────────────────────
@app.route("/friends")
def friends():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid userId"}), 400
    try:
        data = get_json(f"{BASE_FRIENDS}/v1/users/{user_id}/friends")
        friend_list = data.get("data", [])

        # Batch avatar headshots (up to 100 at a time)
        avatar_map = {}
        ids = [str(f["id"]) for f in friend_list]
        for i in range(0, len(ids), 100):
            batch = ids[i:i+100]
            try:
                td = get_json(f"{BASE_THUMBS}/v1/users/avatar-headshot", params={
                    "userIds": ",".join(batch),
                    "size": "60x60",
                    "format": "Png",
                    "isCircular": False
                })
                for item in td.get("data", []):
                    avatar_map[str(item["targetId"])] = item.get("imageUrl", "")
            except:
                pass

        friends_out = []
        for f in friend_list:
            friends_out.append({
                "id":          f.get("id"),
                "name":        f.get("name"),
                "displayName": f.get("displayName"),
                "isOnline":    f.get("isOnline", False),
                "avatarUrl":   avatar_map.get(str(f.get("id", "")), "")
            })

        return jsonify({"success": True, "friends": friends_out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── /groups ────────────────────────────────────────────────────────────────
@app.route("/groups")
def groups():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid userId"}), 400
    try:
        data = get_json(f"{BASE_GROUPS}/v1/users/{user_id}/groups/roles")
        group_list = data.get("data", [])

        # Batch group icons
        group_ids = [str(g["group"]["id"]) for g in group_list]
        icon_map = {}
        for i in range(0, len(group_ids), 100):
            batch = group_ids[i:i+100]
            try:
                td = get_json(f"{BASE_THUMBS}/v1/groups/icons", params={
                    "groupIds": ",".join(batch),
                    "size": "150x150",
                    "format": "Png",
                    "isCircular": False
                })
                for item in td.get("data", []):
                    icon_map[str(item["targetId"])] = item.get("imageUrl", "")
            except:
                pass

        groups_out = []
        for g in group_list:
            grp = g.get("group", {})
            role = g.get("role", {})
            groups_out.append({
                "id":          grp.get("id"),
                "name":        grp.get("name"),
                "memberCount": grp.get("memberCount", 0),
                "role":        role.get("name", ""),
                "iconUrl":     icon_map.get(str(grp.get("id", "")), "")
            })

        return jsonify({"success": True, "groups": groups_out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── /played-games ──────────────────────────────────────────────────────────
# Derives played games from badge data.
# FIX: removed the [:60] cap on enrichment — all badges get enriched now.
@app.route("/played-games")
def played_games():
    user_id = request.args.get("userId", "")
    if not user_id.isdigit():
        return jsonify({"success": False, "error": "Invalid userId"}), 400

    # Collect all badges
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
        page = data.get("data", [])
        badges.extend(page)
        cursor = data.get("nextPageCursor") or ""
        if not cursor:
            break
        time.sleep(DELAY)

    # Enrich ALL badges missing awardingUniverse (was capped at 60 before — that was the bug)
    for badge in badges:
        u = badge.get("awardingUniverse") or {}
        if not u.get("name"):
            try:
                detail = get_json(f"{BASE_BADGES}/v1/badges/{badge['id']}")
                if detail.get("awardingUniverse"):
                    badge["awardingUniverse"] = detail["awardingUniverse"]
                time.sleep(DELAY)
            except:
                pass

    # Deduplicate into games
    games_map   = {}
    games_order = []

    for badge in badges:
        u           = badge.get("awardingUniverse") or {}
        universe_id = u.get("id") or 0
        name        = u.get("name") or "[Content Deleted]"
        place_id    = u.get("rootPlaceId", 0)

        # Skip genuinely deleted universes (id == 0 means Roblox returned nothing)
        key = str(universe_id) if universe_id else f"deleted_{badge.get('id', 0)}"

        if key not in games_map:
            games_map[key] = {
                "name":       name,
                "universeId": universe_id,
                "placeId":    place_id,
                "badgeCount": 0
            }
            games_order.append(key)

        games_map[key]["badgeCount"] += 1

    # Batch-fetch game icons for all non-deleted universes
    valid_universe_ids = [
        str(games_map[k]["universeId"])
        for k in games_order
        if games_map[k]["universeId"] != 0
    ]
    icon_map = {}
    for i in range(0, len(valid_universe_ids), 100):
        batch = valid_universe_ids[i:i+100]
        try:
            td = get_json(f"{BASE_THUMBS}/v1/games/icons", params={
                "universeIds": ",".join(batch),
                "returnPolicy": "PlaceHolder",
                "size": "150x150",
                "format": "Png",
                "isCircular": False
            })
            for item in td.get("data", []):
                icon_map[str(item["universeId"])] = item.get("imageUrl", "")
        except:
            pass
        time.sleep(DELAY)

    games = []
    for k in games_order:
        g = games_map[k]
        g["iconUrl"] = icon_map.get(str(g["universeId"]), "")
        games.append(g)

    return jsonify({
        "success":    True,
        "gameCount":  len(games),
        "badgeCount": len(badges),
        "games":      games
    })

# ── legacy /lookup kept for compatibility ──────────────────────────────────
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

    # Enrichment no longer capped at 60
    for badge in badges:
        if not (badge.get("awardingUniverse") or {}).get("name"):
            try:
                detail = get_json(f"{BASE_BADGES}/v1/badges/{badge['id']}")
                if detail.get("awardingUniverse"):
                    badge["awardingUniverse"] = detail["awardingUniverse"]
            except:
                pass

    games_map   = {}
    games_order = []

    for badge in badges:
        u           = badge.get("awardingUniverse") or {}
        universe_id = u.get("id") or 0
        key         = str(universe_id) if universe_id else f"deleted_{badge.get('id', 0)}"
        name        = u.get("name") or "[Content Deleted]"
        place_id    = u.get("rootPlaceId", 0)

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
