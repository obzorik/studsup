"""
StudsUp — Database initializer
Creates SQLite database with all tables and seeds data.
Run once: python db/init_db.py
"""
import sqlite3, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DB_PATH = os.path.join(os.path.dirname(__file__), "studsup.db")

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ── USERS ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    email       TEXT    NOT NULL UNIQUE,
    display_name TEXT   NOT NULL DEFAULT '',
    avatar_color TEXT   NOT NULL DEFAULT '#FF4444',
    country     TEXT    NOT NULL DEFAULT '',
    city        TEXT    NOT NULL DEFAULT '',
    bio         TEXT    NOT NULL DEFAULT '',
    seller_rating REAL  NOT NULL DEFAULT 0,
    seller_sales  INTEGER NOT NULL DEFAULT 0,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);

-- ── LUGS ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lugs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    slug        TEXT    NOT NULL UNIQUE,
    country     TEXT    NOT NULL DEFAULT '',
    city        TEXT    NOT NULL DEFAULT '',
    website     TEXT    NOT NULL DEFAULT '',
    description TEXT    NOT NULL DEFAULT '',
    founded_year INTEGER,
    head_user_id INTEGER REFERENCES users(id),
    ambassador_user_id INTEGER REFERENCES users(id),
    member_count INTEGER NOT NULL DEFAULT 0,
    is_verified INTEGER NOT NULL DEFAULT 0,
    is_lego_recognized INTEGER NOT NULL DEFAULT 0,
    postal_address TEXT NOT NULL DEFAULT '',
    postal_city   TEXT NOT NULL DEFAULT '',
    postal_zip    TEXT NOT NULL DEFAULT '',
    postal_country TEXT NOT NULL DEFAULT '',
    contact_email TEXT NOT NULL DEFAULT '',
    logo_emoji  TEXT NOT NULL DEFAULT '🧱',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lugs_slug    ON lugs(slug);
CREATE INDEX IF NOT EXISTS idx_lugs_country ON lugs(country);

-- ── LUG MEMBERS ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lug_members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    lug_id      INTEGER NOT NULL REFERENCES lugs(id),
    role        TEXT    NOT NULL DEFAULT 'member',
    joined_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, lug_id)
);

-- ── PARTS ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    element_id      INTEGER NOT NULL UNIQUE,
    lego_color_id   INTEGER NOT NULL DEFAULT 0,
    bl_color_id     INTEGER NOT NULL DEFAULT 0,
    bl_color_name   TEXT    NOT NULL DEFAULT '',
    color_css       TEXT    NOT NULL DEFAULT '#cccccc',
    design_id       INTEGER NOT NULL DEFAULT 0,
    bl_part_id      TEXT    NOT NULL DEFAULT '',
    -- Sold stats
    sold_lots       INTEGER NOT NULL DEFAULT 0,
    sold_qty        INTEGER NOT NULL DEFAULT 0,
    sold_min_usd    REAL,
    sold_avg_usd    REAL,
    sold_max_usd    REAL,
    -- Available stats
    avail_lots      INTEGER NOT NULL DEFAULT 0,
    avail_qty       INTEGER NOT NULL DEFAULT 0,
    avail_min_usd   REAL,
    avail_avg_usd   REAL,
    avail_max_usd   REAL,
    -- Derived / cache
    img_url         TEXT    NOT NULL DEFAULT '',
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_parts_element_id  ON parts(element_id);
CREATE INDEX IF NOT EXISTS idx_parts_bl_part_id  ON parts(bl_part_id);
CREATE INDEX IF NOT EXISTS idx_parts_bl_color_id ON parts(bl_color_id);
CREATE INDEX IF NOT EXISTS idx_parts_avail_avg   ON parts(avail_avg_usd);
CREATE INDEX IF NOT EXISTS idx_parts_bl_color_name ON parts(bl_color_name);

-- Full-text search on parts
CREATE VIRTUAL TABLE IF NOT EXISTS parts_fts USING fts5(
    element_id, bl_part_id, bl_color_name,
    content='parts', content_rowid='id'
);

-- ── SETS ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    set_number  TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    theme       TEXT    NOT NULL DEFAULT '',
    year        INTEGER,
    part_count  INTEGER NOT NULL DEFAULT 0,
    retail_eur  REAL,
    img_url     TEXT    NOT NULL DEFAULT '',
    instructions_available INTEGER NOT NULL DEFAULT 0,
    parts_list_available   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sets_number ON sets(set_number);
CREATE INDEX IF NOT EXISTS idx_sets_theme  ON sets(theme);
CREATE VIRTUAL TABLE IF NOT EXISTS sets_fts USING fts5(
    set_number, name, theme,
    content='sets', content_rowid='id'
);

-- ── STORES ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    name        TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    country     TEXT    NOT NULL DEFAULT '',
    rating      REAL    NOT NULL DEFAULT 0,
    total_sales INTEGER NOT NULL DEFAULT 0,
    is_active   INTEGER NOT NULL DEFAULT 1,
    min_order_eur REAL  NOT NULL DEFAULT 0,
    ships_worldwide INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stores_user_id ON stores(user_id);
CREATE INDEX IF NOT EXISTS idx_stores_country ON stores(country);
CREATE VIRTUAL TABLE IF NOT EXISTS stores_fts USING fts5(
    name, description, country,
    content='stores', content_rowid='id'
);

-- ── LISTINGS (parts for sale) ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS listings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    INTEGER NOT NULL REFERENCES stores(id),
    part_id     INTEGER NOT NULL REFERENCES parts(id),
    condition   TEXT    NOT NULL DEFAULT 'new',   -- new / used
    qty         INTEGER NOT NULL DEFAULT 0,
    price_eur   REAL    NOT NULL,
    note        TEXT    NOT NULL DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_listings_store_id ON listings(store_id);
CREATE INDEX IF NOT EXISTS idx_listings_part_id  ON listings(part_id);
CREATE INDEX IF NOT EXISTS idx_listings_price    ON listings(price_eur);

-- ── DISCOUNTS ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS discounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    INTEGER NOT NULL REFERENCES stores(id),
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    discount_pct REAL   NOT NULL DEFAULT 0,
    min_order_eur REAL  NOT NULL DEFAULT 0,
    code        TEXT    NOT NULL DEFAULT '',
    valid_from  TEXT,
    valid_until TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_discounts_store_id ON discounts(store_id);
CREATE INDEX IF NOT EXISTS idx_discounts_active   ON discounts(is_active);

-- ── STREAMS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS streams (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    theme_tag   TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'vod',  -- live / vod / scheduled
    viewer_count INTEGER NOT NULL DEFAULT 0,
    vod_views   INTEGER NOT NULL DEFAULT 0,
    thumbnail_emoji TEXT NOT NULL DEFAULT '🎥',
    started_at  TEXT,
    ended_at    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_streams_user_id ON streams(user_id);
CREATE INDEX IF NOT EXISTS idx_streams_status  ON streams(status);
CREATE VIRTUAL TABLE IF NOT EXISTS streams_fts USING fts5(
    title, description, theme_tag,
    content='streams', content_rowid='id'
);

-- ── BLOG POSTS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    title       TEXT    NOT NULL,
    excerpt     TEXT    NOT NULL DEFAULT '',
    body        TEXT    NOT NULL DEFAULT '',
    tag         TEXT    NOT NULL DEFAULT '',
    cover_emoji TEXT    NOT NULL DEFAULT '📝',
    likes       INTEGER NOT NULL DEFAULT 0,
    read_min    INTEGER NOT NULL DEFAULT 5,
    is_published INTEGER NOT NULL DEFAULT 1,
    published_at TEXT   NOT NULL DEFAULT (datetime('now')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
    title, excerpt, tag,
    content='posts', content_rowid='id'
);

-- ── LUGBULK HISTORY ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lugbulk_orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    lug_id      INTEGER REFERENCES lugs(id),
    part_element_id INTEGER NOT NULL,
    bl_part_id  TEXT    NOT NULL DEFAULT '',
    bl_color_id INTEGER NOT NULL DEFAULT 0,
    color_name  TEXT    NOT NULL DEFAULT '',
    year        INTEGER NOT NULL,
    qty         INTEGER NOT NULL DEFAULT 0,
    note        TEXT    NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, part_element_id, bl_color_id, year)
);
CREATE INDEX IF NOT EXISTS idx_lb_user_id ON lugbulk_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_lb_year    ON lugbulk_orders(year);
"""

BL_COLORS = {
    0:"Black",1:"Blue",2:"Green",3:"Dark Turquoise",4:"Red",5:"Dark Pink",
    6:"Brown",7:"Light Gray",8:"Dark Gray",9:"Light Blue",10:"Bright Green",
    11:"Trans-Dark Blue",12:"Trans-Green",13:"Trans-Clear",14:"Yellow",
    15:"White",17:"Trans-Red",18:"Trans-Orange",19:"Tan",20:"Light Violet",
    22:"Purple",23:"Dark Blue-Violet",24:"Trans-Neon Orange",25:"Orange",
    26:"Magenta",27:"Lime",28:"Dark Tan",29:"Trans-Pink",31:"Medium Blue",
    32:"Medium Green",34:"Aqua",37:"Trans-Dark Pink",38:"Reddish Brown",
    39:"Sand Blue",40:"Sand Green",41:"Dark Orange",42:"Very Light Gray",
    43:"Trans-Neon Green",45:"Sand Purple",46:"Dark Red",47:"Glitter Trans-Clear",
    48:"Trans-Medium Blue",51:"Speckle DBGray-Copper",52:"Trans-Dark Orange",
    54:"Pearl White",55:"Pearl Light Gold",57:"Flat Silver",59:"Chrome Silver",
    60:"Trans-Light Purple",61:"Pearl Light Gray",62:"Flat Dark Gold",63:"Dark Blue",
    64:"Trans-Neon Yellow",67:"Chrome Gold",68:"Very Light Bluish Gray",
    69:"Dark Bluish Gray",71:"Light Bluish Gray",72:"Medium Dark Flesh",
    73:"Dark Flesh",75:"Medium Nougat",77:"Medium Azure",78:"Aqua",80:"Warm Tan",
    84:"Nougat",85:"Dark Purple",86:"Sand Orange",88:"Dark Pink",89:"Lavender",
    91:"Pearl Dark Gray",95:"Olive Green",96:"Bright Pink",97:"Coral",
    100:"Trans-Light Orange",103:"Trans-Bright Green",104:"Bright Light Yellow",
    105:"Trans-Orange",108:"Bright Light Blue",109:"Dark Azure",110:"Charcoal",
    112:"Medium Lavender",114:"Lime Green",115:"Yellowish Green",127:"Pearl Gold",
    130:"Milky White",134:"Copper",135:"Metallic Gold",137:"Metallic Silver",
    138:"Metallic Bright Orange",142:"Flat Earth",143:"Bright Light Orange",
    145:"Sand Yellow",148:"Metallic Dark Gray",149:"Trans-Black",
    150:"Glow in Dark Trans",152:"Dark Brown",154:"Bright Pink",
    155:"Medium Dark Pink",160:"Trans-Light Blue",167:"Sand Yellow-Orange",
    168:"Dark Salmon",170:"Medium Brown",175:"Glitter Trans-Purple",
    176:"Glitter Trans-Red",178:"Metallic Blue",220:"Light Aqua",
    223:"Bright Light Pink",224:"Neon Orange",228:"Dark Olive Green",
    232:"Trans-Very Light Blue",233:"Light Lilac",236:"Neon Yellow",
    240:"Olive Green",241:"Medium Violet",
}

COLOR_CSS = {
    0:"#1a1a1a",1:"#006cb7",2:"#00852b",3:"#00a29b",4:"#c91a09",5:"#c870a0",
    6:"#583927",7:"#9ba19d",8:"#6d6e5c",9:"#9fc3e9",10:"#37ab2d",
    13:"rgba(200,200,200,0.3)",14:"#f2cd37",15:"#ffffff",19:"#f5e4bc",
    22:"#7b4fb5",25:"#fe8a18",27:"#bbd159",28:"#c7ac78",38:"#88421d",
    39:"#5a7184",40:"#7db38a",41:"#a95500",42:"#e6e3da",46:"#720e0f",
    54:"#ede8d6",55:"#dcbe6b",57:"#9b9b9b",63:"#003882",67:"#d4aa00",
    68:"#dddcd8",69:"#595d60",71:"#a0a5a9",72:"#cc8f62",73:"#845e41",
    75:"#d67240",77:"#68c3d4",78:"#5db5b5",80:"#f3dfc0",84:"#d09168",
    85:"#4b0082",88:"#c870a0",89:"#b390d8",91:"#5c5c5c",95:"#7c9051",
    96:"#f2a5b8",97:"#ff7b54",104:"#fde832",108:"#9fc3e9",109:"#0071c1",
    112:"#b89dbf",114:"#8bbf2e",127:"#daa016",130:"#f2f0ea",134:"#c7822a",
    135:"#c7af5e",137:"#9b9b9b",142:"#ab9966",143:"#ffa830",145:"#d2c46a",
    148:"#58595a",149:"rgba(0,0,0,0.55)",152:"#352100",154:"#f2a5b8",
    220:"#bce5d7",223:"#f6ada1",228:"#4b5320",
}

def seed_parts(conn):
    try:
        import pandas as pd
    except ImportError:
        print("pandas not available — skipping part seed")
        return 0

    xlsx_path = "/mnt/user-data/uploads/LUGBULK_2026.xlsx"
    if not os.path.exists(xlsx_path):
        print(f"XLSX not found at {xlsx_path} — skipping part seed")
        return 0

    print("Reading XLSX...")
    df = pd.read_excel(xlsx_path, sheet_name='BLPrices', header=0)
    print(f"  {len(df)} rows")

    rows = []
    for _, r in df.iterrows():
        try:
            eid    = int(r['Element ID'])
            lcol   = int(r['LEGO Color ID'])
            blcol  = int(r['BL Color ID'])
            did    = int(r['Design ID'])
            blp    = str(r['BL Part ID']).strip() if str(r['BL Part ID']) != 'nan' else str(did)
            cname  = BL_COLORS.get(blcol, f"Color {blcol}")
            ccss   = COLOR_CSS.get(blcol, "#cccccc")
            img    = f"https://img.bricklink.com/ItemImage/PN/{blcol}/{blp}.png"

            def f(v): return float(v) if str(v) not in ('nan','None') else None
            rows.append((eid, lcol, blcol, cname, ccss, did, blp,
                         int(r['Sold Lots']), int(r['Sold Qty']),
                         f(r['Sold Min Price USD']), f(r['Sold Avg Price']), f(r['Sold Max Price']),
                         int(r['Available Lots']), int(r['Available Qty']),
                         f(r['Available Min Price']), f(r['Available Avg Price']), f(r['Available Max Price']),
                         img))
        except Exception as e:
            continue

    cur = conn.cursor()
    cur.executemany("""
        INSERT OR REPLACE INTO parts
          (element_id,lego_color_id,bl_color_id,bl_color_name,color_css,
           design_id,bl_part_id,sold_lots,sold_qty,sold_min_usd,sold_avg_usd,sold_max_usd,
           avail_lots,avail_qty,avail_min_usd,avail_avg_usd,avail_max_usd,img_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    # Populate FTS
    cur.execute("DELETE FROM parts_fts")
    cur.execute("INSERT INTO parts_fts(rowid,element_id,bl_part_id,bl_color_name) SELECT id,element_id,bl_part_id,bl_color_name FROM parts")
    conn.commit()
    print(f"  Inserted {len(rows)} parts into DB + FTS index")
    return len(rows)


def seed_demo(conn):
    cur = conn.cursor()

    # Users
    users = [
        (1,'georgs_bricks','georgs@studsup.com','Georgs T.','#FF4444','Latvia','Riga','AFOL since 2004. Technic & Castle.',4.9,312),
        (2,'brickmaster_shop','bm@studsup.com','BrickMaster Shop','#1a1a2e','Latvia','Riga','Official parts store. 8,420+ sales.',4.9,8420),
        (3,'partsbarn_eu','pb@studsup.com','PartsBarn EU','#3b82f6','Germany','Berlin','Bulk parts from Germany.',4.8,3110),
        (4,'legoking_vintage','lk@studsup.com','LegoKing Vintage','#f59e0b','Netherlands','Amsterdam','New and used parts.',4.7,1890),
        (5,'studstrader','st@studsup.com','StudsTrader','#8b5cf6','Poland','Warsaw','Quality parts, fast shipping.',5.0,540),
        (6,'maris_k','maris@brickbaltic.lv','Maris Kalniņš','#1a1a2e','Latvia','Riga','LUG founder. Castle builder.',5.0,120),
        (7,'liga_p','liga@brickbaltic.lv','Liga Puriņa','#3b82f6','Latvia','Riga','LEGO Ambassador.',4.9,80),
        (8,'brickmasterpaul','paul@studsup.com','BrickMasterPaul','#22c55e','Latvia','Riga','Live streamer. Castle & City.',4.8,240),
    ]
    cur.executemany("INSERT OR REPLACE INTO users (id,username,email,display_name,avatar_color,country,city,bio,seller_rating,seller_sales) VALUES (?,?,?,?,?,?,?,?,?,?)", users)

    # LUG
    cur.execute("INSERT OR REPLACE INTO lugs (id,name,slug,country,city,website,description,founded_year,head_user_id,ambassador_user_id,member_count,is_verified,is_lego_recognized,postal_address,postal_city,postal_zip,postal_country,contact_email,logo_emoji) VALUES (1,'BrickBaltic LUG','brickbaltic','Latvia','Riga','https://brickbaltic.lv','Largest LEGO User Group in the Baltic states.',2012,6,7,284,1,1,'Krišjāņa Barona iela 7','Riga','LV-1011','Latvia','head@brickbaltic.lv','🇱🇻')")
    cur.execute("INSERT OR REPLACE INTO lug_members (user_id,lug_id,role) VALUES (1,1,'member')")
    cur.execute("INSERT OR REPLACE INTO lug_members (user_id,lug_id,role) VALUES (6,1,'head')")
    cur.execute("INSERT OR REPLACE INTO lug_members (user_id,lug_id,role) VALUES (7,1,'ambassador')")

    # Stores
    stores = [
        (1,2,'BrickMaster_Shop','Official LEGO parts store. Latvia. Fast EU shipping.','Latvia',4.9,8420,1,5.0,1),
        (2,3,'PartsBarn_EU','Bulk parts specialist from Germany. All quantities.','Germany',4.8,3110,1,10.0,1),
        (3,4,'LegoKing_Vintage','New and used parts. Netherlands.','Netherlands',4.7,1890,1,3.0,1),
        (4,5,'StudsTrader','Quality parts, fast shipping. Poland.','Poland',5.0,540,1,8.0,0),
    ]
    cur.executemany("INSERT OR REPLACE INTO stores (id,user_id,name,description,country,rating,total_sales,is_active,min_order_eur,ships_worldwide) VALUES (?,?,?,?,?,?,?,?,?,?)", stores)
    cur.execute("INSERT INTO stores_fts(rowid,name,description,country) SELECT id,name,description,country FROM stores ")

    # Discounts
    discounts = [
        (1,1,'Summer sale 10% off','10% off all orders over €20','10.0',20.0,'SUMMER10','2026-06-01','2026-08-31',1),
        (2,2,'Bulk buyer discount','15% off orders over €50','15.0',50.0,'BULK15','2026-01-01','2026-12-31',1),
        (3,1,'New member welcome','5% off first order','5.0',0,'WELCOME5','2026-01-01','2026-12-31',1),
    ]
    cur.executemany("INSERT OR REPLACE INTO discounts (id,store_id,title,description,discount_pct,min_order_eur,code,valid_from,valid_until,is_active) VALUES (?,?,?,?,?,?,?,?,?,?)", discounts)

    # Sets
    sets_data = [
        (1,'10305','Lion Knights Castle','Castle',2022,4514,259.99,'https://img.bricklink.com/ItemImage/SN/0/10305-1.png',1,1),
        (2,'75192','Millennium Falcon','Star Wars',2017,7541,799.99,'https://img.bricklink.com/ItemImage/SN/0/75192-1.png',1,1),
        (3,'10294','Titanic','Icons',2021,9090,629.99,'https://img.bricklink.com/ItemImage/SN/0/10294-1.png',1,1),
        (4,'42156','PEUGEOT 9X8 Hypercar','Technic',2023,1775,189.99,'https://img.bricklink.com/ItemImage/SN/0/42156-1.png',1,1),
        (5,'71043','Hogwarts Castle','Harry Potter',2018,6020,469.99,'https://img.bricklink.com/ItemImage/SN/0/71043-1.png',1,1),
    ]
    cur.executemany("INSERT OR REPLACE INTO sets (id,set_number,name,theme,year,part_count,retail_eur,img_url,instructions_available,parts_list_available) VALUES (?,?,?,?,?,?,?,?,?,?)", sets_data)
    cur.execute("INSERT INTO sets_fts(rowid,set_number,name,theme) SELECT id,set_number,name,theme FROM sets ")

    # Streams
    streams_data = [
        (1,8,'Building Hogwarts Castle live — day 3 of 5!','Live castle MOC build','Castle','live',1240,0,'🏗️'),
        (2,1,'Technic supercar MOC — gearbox reveal','Full gearbox walkthrough','Technic','live',430,0,'🤖'),
        (3,6,'Sorting 50K bulk parts haul','Sorting LUGBULK haul','Bulk','live',218,0,'📦'),
        (4,8,'Custom minifig painting tutorial','Airbrush technique on minifigs','Custom','vod',0,12400,'🎨'),
        (5,1,'Building a full LEGO city — 12 hour marathon','Full city layout from scratch','City','vod',0,8100,'🏙️'),
    ]
    cur.executemany("INSERT OR REPLACE INTO streams (id,user_id,title,description,theme_tag,status,viewer_count,vod_views,thumbnail_emoji) VALUES (?,?,?,?,?,?,?,?,?)", streams_data)
    cur.execute("INSERT INTO streams_fts(rowid,title,description,theme_tag) SELECT id,title,description,theme_tag FROM streams ")

    # Posts
    posts_data = [
        (1,1,'Building a pneumatic V8 engine from LEGO Technic','3 months, 2,400 parts, all 8 pistons firing in sequence.','Technic build','⚙️',342,14,1),
        (2,1,'My biggest castle build yet — 4,800 parts','BrickFest Baltic was in 2 weeks and I was nowhere near done.','MOC showcase','🏰',218,9,1),
        (3,6,'BrickFest Baltic 2025 — recap and photos','2,000+ visitors, 48 LUG builds, 3 countries represented.','Event recap','🎪',128,6,1),
        (4,2,'Best retiring sets to buy in 2025','Data from 5 years of price tracking shows which themes appreciate most.','Investing','💰',891,6,1),
        (5,3,'Bulk sorting workflow: from 20kg of mixed bricks to clean bins','My complete system — containers, labelling and tools.','Guide','📦',217,12,1),
    ]
    cur.executemany("INSERT OR REPLACE INTO posts (id,user_id,title,excerpt,tag,cover_emoji,likes,read_min,is_published) VALUES (?,?,?,?,?,?,?,?,?)", posts_data)
    cur.execute("INSERT INTO posts_fts(rowid,title,excerpt,tag) SELECT id,title,excerpt,tag FROM posts ")

    conn.commit()
    print("  Demo data seeded")


def main():
    print(f"Initializing database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    seed_demo(conn)
    n = seed_parts(conn)
    conn.close()
    size = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"\n✓ Database ready: {size:.1f} MB  |  {n} parts loaded")

if __name__ == "__main__":
    main()
