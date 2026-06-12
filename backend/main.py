"""
StudsUp — FastAPI backend
Local:  uvicorn main:app --reload --port 8000
Deploy: uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import sqlite3, os, math
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "studsup.db")

app = FastAPI(title="StudsUp API", version="1.0", docs_url="/api/docs")

# Allow all origins so the static frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def rows(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def one(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None

def paginate(items, page, per_page):
    total = len(items)
    start = (page - 1) * per_page
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total / per_page) if per_page else 1,
            "items": items[start:start + per_page]}

# ── HEALTH ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    conn = get_db()
    stats = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ["parts","sets","stores","users","lugs","streams","posts","discounts"]}
    conn.close()
    return {"status": "ok", "version": "1.0", "db": stats}

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL SEARCH
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/search")
def global_search(
    q: str = Query(""),
    categories: str = Query("parts,sets,stores,discounts,users,lugs,streams,videos"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    if not q.strip():
        return {"query": q, "total": 0, "results": {}}

    cats   = [c.strip() for c in categories.split(",")]
    conn   = get_db()
    q_like = f"%{q}%"
    q_fts  = f"{q}*"
    results = {}

    # PARTS
    if "parts" in cats:
        try:
            raw = rows(conn, """
                SELECT p.id,p.element_id,p.bl_part_id,p.bl_color_id,p.bl_color_name,p.color_css,
                       p.avail_lots,p.avail_qty,p.avail_min_usd,p.avail_avg_usd,p.avail_max_usd,
                       p.sold_qty,p.img_url
                FROM parts_fts f JOIN parts p ON f.rowid_ref=p.id
                WHERE parts_fts MATCH ? ORDER BY p.avail_qty DESC LIMIT 100
            """, (q_fts,))
        except Exception:
            raw = []
        if not raw:
            raw = rows(conn, """
                SELECT id,element_id,bl_part_id,bl_color_id,bl_color_name,color_css,
                       avail_lots,avail_qty,avail_min_usd,avail_avg_usd,avail_max_usd,sold_qty,img_url
                FROM parts WHERE bl_part_id LIKE ? OR CAST(element_id AS TEXT) LIKE ? OR bl_color_name LIKE ?
                ORDER BY avail_qty DESC LIMIT 100
            """, (q_like, q_like, q_like))
        results["parts"] = paginate(raw, page, per_page)

    # SETS
    if "sets" in cats:
        raw = rows(conn, """
            SELECT id,set_number,name,theme,year,part_count,retail_eur,
                   instructions_available,parts_list_available
            FROM sets WHERE set_number LIKE ? OR name LIKE ? OR theme LIKE ?
            ORDER BY year DESC LIMIT 100
        """, (q_like, q_like, q_like))
        results["sets"] = paginate(raw, page, per_page)

    # STORES
    if "stores" in cats:
        raw = rows(conn, """
            SELECT s.id,s.name,s.description,s.country,s.rating,s.total_sales,
                   s.min_order_eur,s.ships_worldwide,u.display_name as owner_name,u.avatar_color,
                   (SELECT COUNT(*) FROM discounts d WHERE d.store_id=s.id AND d.is_active=1) as active_discounts
            FROM stores s JOIN users u ON s.user_id=u.id
            WHERE s.name LIKE ? OR s.description LIKE ? OR s.country LIKE ?
            ORDER BY s.rating DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["stores"] = paginate(raw, page, per_page)

    # DISCOUNTS
    if "discounts" in cats:
        raw = rows(conn, """
            SELECT d.id,d.title,d.description,d.discount_pct,d.min_order_eur,
                   d.code,d.valid_until,s.name as store_name,s.country
            FROM discounts d JOIN stores s ON d.store_id=s.id
            WHERE d.is_active=1 AND (d.title LIKE ? OR d.description LIKE ? OR d.code LIKE ?)
            ORDER BY d.discount_pct DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["discounts"] = paginate(raw, page, per_page)

    # USERS
    if "users" in cats:
        raw = rows(conn, """
            SELECT id,username,display_name,avatar_color,country,city,seller_rating,seller_sales
            FROM users WHERE username LIKE ? OR display_name LIKE ? OR country LIKE ?
            ORDER BY seller_sales DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["users"] = paginate(raw, page, per_page)

    # LUGS
    if "lugs" in cats:
        raw = rows(conn, """
            SELECT id,name,slug,country,city,member_count,is_verified,
                   is_lego_recognized,logo_emoji,founded_year,website
            FROM lugs WHERE name LIKE ? OR country LIKE ? OR city LIKE ?
            ORDER BY member_count DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["lugs"] = paginate(raw, page, per_page)

    # STREAMS (live)
    if "streams" in cats:
        raw = rows(conn, """
            SELECT st.id,st.title,st.description,st.theme_tag,st.status,
                   st.viewer_count,st.vod_views,st.thumbnail_emoji,st.created_at,
                   u.display_name as streamer,u.avatar_color
            FROM streams st JOIN users u ON st.user_id=u.id
            WHERE st.title LIKE ? OR st.description LIKE ? OR st.theme_tag LIKE ?
            ORDER BY CASE st.status WHEN 'live' THEN 0 ELSE 1 END, st.viewer_count DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["streams"] = paginate(raw, page, per_page)

    # VIDEOS (vod)
    if "videos" in cats:
        raw = rows(conn, """
            SELECT st.id,st.title,st.description,st.theme_tag,st.vod_views,
                   st.thumbnail_emoji,st.created_at,u.display_name as streamer,u.avatar_color
            FROM streams st JOIN users u ON st.user_id=u.id
            WHERE st.status='vod' AND (st.title LIKE ? OR st.description LIKE ? OR st.theme_tag LIKE ?)
            ORDER BY st.vod_views DESC LIMIT 50
        """, (q_like, q_like, q_like))
        results["videos"] = paginate(raw, page, per_page)

    conn.close()
    return {"query": q, "total": sum(v.get("total",0) for v in results.values()), "results": results}

# ══════════════════════════════════════════════════════════════════════════════
# PARTS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/parts")
def list_parts(
    q: str = Query(""), color_id: Optional[int] = None,
    color_name: str = Query(""), min_price: Optional[float] = None,
    max_price: Optional[float] = None, in_stock: bool = Query(False),
    sort: str = Query("avail_avg_usd"), order: str = Query("asc"),
    page: int = Query(1, ge=1), per_page: int = Query(48, ge=1, le=200),
):
    conn = get_db()
    wheres, params = [], []
    if q:
        q_like = f"%{q}%"
        wheres.append("(bl_part_id LIKE ? OR CAST(element_id AS TEXT) LIKE ? OR bl_color_name LIKE ?)")
        params += [q_like, q_like, q_like]
    if color_id is not None:
        wheres.append("bl_color_id=?"); params.append(color_id)
    if color_name:
        wheres.append("bl_color_name LIKE ?"); params.append(f"%{color_name}%")
    if min_price is not None:
        wheres.append("avail_avg_usd >= ?"); params.append(min_price)
    if max_price is not None:
        wheres.append("avail_avg_usd <= ?"); params.append(max_price)
    if in_stock:
        wheres.append("avail_qty > 0")

    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    allowed   = {"avail_avg_usd","avail_min_usd","avail_qty","avail_lots","sold_qty","element_id"}
    sort_col  = sort if sort in allowed else "avail_avg_usd"
    ord_dir   = "DESC" if order.lower() == "desc" else "ASC"

    total  = conn.execute(f"SELECT COUNT(*) FROM parts {where_sql}", params).fetchone()[0]
    offset = (page - 1) * per_page
    items  = rows(conn, f"""
        SELECT id,element_id,bl_part_id,bl_color_id,bl_color_name,color_css,design_id,
               avail_lots,avail_qty,avail_min_usd,avail_avg_usd,avail_max_usd,sold_lots,sold_qty,img_url
        FROM parts {where_sql}
        ORDER BY {sort_col} {ord_dir} NULLS LAST LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total / per_page), "items": items}

@app.get("/api/parts/colors")
def list_colors():
    conn = get_db()
    data = rows(conn, "SELECT bl_color_id,bl_color_name,color_css,COUNT(*) as part_count FROM parts GROUP BY bl_color_id ORDER BY bl_color_name")
    conn.close()
    return data

@app.get("/api/parts/{element_id}")
def get_part(element_id: int):
    conn = get_db()
    p = one(conn, "SELECT * FROM parts WHERE element_id=?", (element_id,))
    conn.close()
    if not p: raise HTTPException(404, "Part not found")
    return p

# ══════════════════════════════════════════════════════════════════════════════
# STORES
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/stores")
def list_stores(q: str = Query(""), country: str = Query(""),
                page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    wheres, params = ["s.is_active=1"], []
    if q:
        wheres.append("(s.name LIKE ? OR s.description LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if country:
        wheres.append("s.country LIKE ?"); params.append(f"%{country}%")
    where_sql = "WHERE " + " AND ".join(wheres)
    total  = conn.execute(f"SELECT COUNT(*) FROM stores s {where_sql}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT s.id,s.name,s.description,s.country,s.rating,s.total_sales,
               s.min_order_eur,s.ships_worldwide,u.display_name as owner,u.avatar_color,
               (SELECT COUNT(*) FROM discounts d WHERE d.store_id=s.id AND d.is_active=1) as active_discounts
        FROM stores s JOIN users u ON s.user_id=u.id
        {where_sql} ORDER BY s.rating DESC, s.total_sales DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

# ══════════════════════════════════════════════════════════════════════════════
# DISCOUNTS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/discounts")
def list_discounts(q: str = Query(""), page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    q_like = f"%{q}%"
    where  = "WHERE d.is_active=1" + (" AND (d.title LIKE ? OR d.code LIKE ?)" if q else "")
    params = [q_like, q_like] if q else []
    total  = conn.execute(f"SELECT COUNT(*) FROM discounts d {where}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT d.id,d.title,d.description,d.discount_pct,d.min_order_eur,
               d.code,d.valid_from,d.valid_until,s.name as store_name,s.country,s.rating as store_rating
        FROM discounts d JOIN stores s ON d.store_id=s.id
        {where} ORDER BY d.discount_pct DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

# ══════════════════════════════════════════════════════════════════════════════
# SETS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/sets")
def list_sets(q: str = Query(""), theme: str = Query(""),
              year: Optional[int] = None, page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    wheres, params = [], []
    if q:
        wheres.append("(set_number LIKE ? OR name LIKE ? OR theme LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if theme:
        wheres.append("theme LIKE ?"); params.append(f"%{theme}%")
    if year:
        wheres.append("year=?"); params.append(year)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total  = conn.execute(f"SELECT COUNT(*) FROM sets {where_sql}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"SELECT * FROM sets {where_sql} ORDER BY year DESC LIMIT ? OFFSET ?",
                  params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/users")
def list_users(q: str = Query(""), page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    q_like = f"%{q}%"
    where  = "WHERE username LIKE ? OR display_name LIKE ? OR country LIKE ?" if q else ""
    params = [q_like, q_like, q_like] if q else []
    total  = conn.execute(f"SELECT COUNT(*) FROM users {where}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT id,username,display_name,avatar_color,country,city,seller_rating,seller_sales
        FROM users {where} ORDER BY seller_sales DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

@app.get("/api/users/{username}")
def get_user(username: str):
    conn = get_db()
    u = one(conn, "SELECT id,username,display_name,avatar_color,country,city,bio,seller_rating,seller_sales,created_at FROM users WHERE username=?", (username,))
    conn.close()
    if not u: raise HTTPException(404, "User not found")
    return u

# ══════════════════════════════════════════════════════════════════════════════
# LUGS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/lugs")
def list_lugs(q: str = Query(""), country: str = Query(""),
              page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    wheres, params = [], []
    if q:
        wheres.append("(name LIKE ? OR city LIKE ?)"); params += [f"%{q}%", f"%{q}%"]
    if country:
        wheres.append("country LIKE ?"); params.append(f"%{country}%")
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total  = conn.execute(f"SELECT COUNT(*) FROM lugs {where_sql}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT id,name,slug,country,city,member_count,is_verified,
               is_lego_recognized,logo_emoji,founded_year,website,description
        FROM lugs {where_sql} ORDER BY member_count DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

@app.get("/api/lugs/{slug}")
def get_lug(slug: str):
    conn = get_db()
    lug = one(conn, "SELECT * FROM lugs WHERE slug=?", (slug,))
    if not lug: raise HTTPException(404, "LUG not found")
    lug["members"] = rows(conn, """
        SELECT u.id,u.username,u.display_name,u.avatar_color,u.country,lm.role,lm.joined_at
        FROM lug_members lm JOIN users u ON lm.user_id=u.id
        WHERE lm.lug_id=? ORDER BY lm.role,u.display_name
    """, (lug["id"],))
    conn.close()
    return lug

# ══════════════════════════════════════════════════════════════════════════════
# STREAMS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/streams")
def list_streams(q: str = Query(""), status: str = Query(""),
                 page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    wheres, params = [], []
    if q:
        wheres.append("(st.title LIKE ? OR st.description LIKE ? OR st.theme_tag LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if status:
        wheres.append("st.status=?"); params.append(status)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    total  = conn.execute(f"SELECT COUNT(*) FROM streams st {where_sql}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT st.id,st.title,st.description,st.theme_tag,st.status,
               st.viewer_count,st.vod_views,st.thumbnail_emoji,st.created_at,
               u.display_name as streamer,u.username,u.avatar_color
        FROM streams st JOIN users u ON st.user_id=u.id
        {where_sql}
        ORDER BY CASE st.status WHEN 'live' THEN 0 ELSE 1 END, st.viewer_count DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

# ══════════════════════════════════════════════════════════════════════════════
# POSTS
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/posts")
def list_posts(q: str = Query(""), tag: str = Query(""),
               page: int = Query(1), per_page: int = Query(20)):
    conn = get_db()
    wheres, params = ["p.is_published=1"], []
    if q:
        wheres.append("(p.title LIKE ? OR p.excerpt LIKE ?)"); params += [f"%{q}%", f"%{q}%"]
    if tag:
        wheres.append("p.tag LIKE ?"); params.append(f"%{tag}%")
    where_sql = "WHERE " + " AND ".join(wheres)
    total  = conn.execute(f"SELECT COUNT(*) FROM posts p {where_sql}", params).fetchone()[0]
    offset = (page-1)*per_page
    items  = rows(conn, f"""
        SELECT p.id,p.title,p.excerpt,p.tag,p.cover_emoji,p.likes,p.read_min,p.published_at,
               u.display_name as author,u.username,u.avatar_color
        FROM posts p JOIN users u ON p.user_id=u.id
        {where_sql} ORDER BY p.published_at DESC LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    conn.close()
    return {"total": total, "page": page, "per_page": per_page,
            "pages": math.ceil(total/per_page), "items": items}

# ══════════════════════════════════════════════════════════════════════════════
# LUGBULK HISTORY
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/lugbulk/{user_id}")
def get_lugbulk(user_id: int):
    conn = get_db()
    data = rows(conn, """
        SELECT part_element_id,bl_part_id,bl_color_id,color_name,year,qty,note,updated_at
        FROM lugbulk_orders WHERE user_id=? ORDER BY year DESC, part_element_id
    """, (user_id,))
    conn.close()
    return data
