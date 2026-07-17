#!/usr/bin/env python3
"""Turn Boat Rental Marbella photos into vertical YouTube Shorts.

The YouTube pipeline ran out of source videos (all Drive clips uploaded). This
script recycles the ~470 boat PHOTOS in the same Drive folder into fresh 1080x1920
Shorts: each reel is a Ken-Burns slideshow of 3 photos with a branded text overlay,
then uploaded BACK into the Drive folder so scripts/post_youtube.py picks it up on
its normal daily run — no other change needed.

Uses the ffmpeg bundled by the imageio-ffmpeg pip package (no system ffmpeg needed).

Usage:
  python3 scripts/make_reels.py --count 8        # make 8 reels, upload to Drive
  python3 scripts/make_reels.py --count 2 --no-upload   # local only (test)
"""
from __future__ import annotations
import argparse, datetime, io, os, pathlib, random, subprocess, sys, tempfile

ROOT    = pathlib.Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"; LOG_DIR.mkdir(exist_ok=True)
OUT_DIR = ROOT / "generated-reels"; OUT_DIR.mkdir(exist_ok=True)
LOG     = LOG_DIR / "make_reels.log"

DRIVE_FOLDER_ID = "1qEQPlq6084s7eaq2wqTtoTjN5t2yvFlS"
UPLOAD_SUBFOLDER = "AI REELS"          # reels land here (created if missing)
TOKEN_PATH = pathlib.Path.home() / ".social_post_token_v2.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
IMG_MAX = 5 * 1024 * 1024
_MIME_EXT = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

W, H = 1080, 1920
IMGS_PER_REEL = 3
SEC_PER_IMG = 4
FPS = 25

# brand text
BRAND   = "BOAT RENTAL MARBELLA"
TAGLINE = "Private Yacht Charters · Puerto Banús"
CTA1    = "boatrentalinmarbella.com"
CTA2    = "WhatsApp +358 400 406194"

TAGLINES = [
    "Private Yacht Charters · Puerto Banús",
    "Skipper · Drinks · Insurance Included",
    "Superyachts · Catamarans · Speedboats",
    "Your Best Day on the Costa del Sol",
    "Dolphin Cruises · Sunsets · Hen Parties",
    "Book a Boat in Marbella Today",
]

def log(m):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {m}"
    print(line, flush=True)
    with LOG.open("a") as f: f.write(line + "\n")

# ── env / fonts ────────────────────────────────────────────────────────────────
def load_env():
    for p in [ROOT / ".env", pathlib.Path.home() / ".env"]:
        if p.exists():
            for ln in p.read_text().splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    k, _, v = ln.partition("=")
                    if k.strip() and k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
load_env()

def _font(paths, size):
    from PIL import ImageFont
    for p in paths:
        if pathlib.Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

FONT_BOLD = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Black.ttf"]
FONT_REG  = ["/System/Library/Fonts/Supplemental/Arial.ttf",
             "/System/Library/Fonts/Helvetica.ttc"]

# ── Google Drive ───────────────────────────────────────────────────────────────
def get_drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def list_images(drive, folder_id, depth=0):
    out, tok = [], None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType,size)",
            pageSize=200, pageToken=tok).execute()
        for f in resp.get("files", []):
            mime = f.get("mimeType", "")
            if mime in _MIME_EXT and int(f.get("size", 0)) <= IMG_MAX:
                out.append(f)
            elif mime == "application/vnd.google-apps.folder" and depth < 2 and f["name"] != UPLOAD_SUBFOLDER:
                out.extend(list_images(drive, f["id"], depth + 1))
        tok = resp.get("nextPageToken")
        if not tok: break
    return out

def download(drive, file_id, dest):
    from googleapiclient.http import MediaIoBaseDownload
    req = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO(); dl = MediaIoBaseDownload(buf, req, chunksize=4 * 1024 * 1024)
    done = False
    while not done: _, done = dl.next_chunk()
    dest.write_bytes(buf.getvalue())

def ensure_subfolder(drive):
    resp = drive.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and name='{UPLOAD_SUBFOLDER}' and "
          "mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    items = resp.get("files", [])
    if items: return items[0]["id"]
    meta = {"name": UPLOAD_SUBFOLDER, "mimeType": "application/vnd.google-apps.folder",
            "parents": [DRIVE_FOLDER_ID]}
    return drive.files().create(body=meta, fields="id").execute()["id"]

def upload_video(drive, path, folder_id):
    from googleapiclient.http import MediaFileUpload
    meta = {"name": path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(path), mimetype="video/mp4", resumable=True)
    return drive.files().create(body=meta, media_body=media, fields="id").execute()["id"]

# ── frame compositing (PIL) ────────────────────────────────────────────────────
def brand_frame(img_path, out_path, tagline):
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.open(img_path).convert("RGB")
    # cover-scale to WxH
    sc = max(W / im.width, H / im.height)
    nw, nh = int(im.width * sc), int(im.height * sc)
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    im = im.crop((left, top, left + W, top + H))
    d = ImageDraw.Draw(im, "RGBA")
    # bottom gradient for legibility
    grad_h = 620
    grad = Image.new("L", (1, grad_h), 0)
    for y in range(grad_h):
        grad.putpixel((0, y), int(215 * (y / grad_h) ** 1.4))
    grad = grad.resize((W, grad_h))
    black = Image.new("RGBA", (W, grad_h), (0, 0, 0, 255))
    black.putalpha(grad)
    im.paste(black, (0, H - grad_h), black)
    # top scrim for tagline
    topbar = Image.new("RGBA", (W, 180), (0, 0, 0, 110))
    im.paste(topbar, (0, 0), topbar)
    # text — kept in the upper/mid-lower band so YouTube's Shorts UI (bottom ~15%
    # and right-side buttons) doesn't cover the CTA.
    f_brand = _font(FONT_BOLD, 66)
    f_tag   = _font(FONT_REG, 38)
    f_cta   = _font(FONT_BOLD, 44)
    def ctext(y, txt, font, fill=(255, 255, 255)):
        w = d.textlength(txt, font=font)
        d.text(((W - w) / 2, y), txt, font=font, fill=fill)
    ctext(74, tagline, f_tag, (240, 240, 240))
    ctext(H - 480, BRAND, f_brand)
    # accent line
    d.rectangle([(W/2 - 110, H - 396), (W/2 + 110, H - 390)], fill=(255, 170, 40, 255))
    ctext(H - 362, CTA1, f_cta, (255, 200, 90))
    ctext(H - 300, CTA2, f_tag, (235, 235, 235))
    im.save(out_path, "PNG")

# ── ffmpeg assembly ────────────────────────────────────────────────────────────
def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def make_clip(ff, frame_png, out_mp4, zoom_in=True):
    frames = SEC_PER_IMG * FPS
    if zoom_in:
        zexpr = f"z='min(zoom+0.0009,1.14)'"
    else:
        zexpr = f"z='if(lte(zoom,1.0),1.14,max(1.001,zoom-0.0009))'"
    vf = (f"scale=8000:-1,zoompan={zexpr}:d={frames}:x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
    cmd = [ff, "-y", "-loop", "1", "-i", str(frame_png), "-vf", vf,
           "-t", str(SEC_PER_IMG), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-preset", "veryfast", "-r", str(FPS), str(out_mp4)]
    subprocess.run(cmd, check=True, capture_output=True)

def concat(ff, clips, out_mp4, workdir):
    listf = workdir / "list.txt"
    listf.write_text("".join(f"file '{c}'\n" for c in clips))
    cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
           "-movflags", "+faststart", str(out_mp4)]
    subprocess.run(cmd, check=True, capture_output=True)

# ── main ───────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=6, help="how many reels to make")
    ap.add_argument("--no-upload", action="store_true")
    a = ap.parse_args()

    ff = ffmpeg_exe()
    log(f"Making {a.count} reels (ffmpeg: {pathlib.Path(ff).name})")
    drive = get_drive()
    imgs = list_images(drive, DRIVE_FOLDER_ID)
    log(f"Drive: {len(imgs)} source photos")
    if len(imgs) < IMGS_PER_REEL:
        log("Not enough photos."); return 1

    rng = random.Random(datetime.datetime.now().timestamp())
    rng.shuffle(imgs)

    made = []
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        pool = imgs[: a.count * IMGS_PER_REEL]
        # download pool
        local = []
        for f in pool:
            ext = _MIME_EXT[f["mimeType"]]
            dst = tdp / f"src_{f['id']}{ext}"
            try:
                download(drive, f["id"], dst); local.append(dst)
            except Exception as e:
                log(f"  dl error {f['id']}: {e}")
        log(f"Downloaded {len(local)} photos")

        for i in range(a.count):
            batch = local[i * IMGS_PER_REEL:(i + 1) * IMGS_PER_REEL]
            if len(batch) < IMGS_PER_REEL: break
            tagline = TAGLINES[i % len(TAGLINES)]
            clips = []
            for j, src in enumerate(batch):
                frame = tdp / f"frame_{i}_{j}.png"
                brand_frame(src, frame, tagline)
                clip = tdp / f"clip_{i}_{j}.mp4"
                make_clip(ff, frame, clip, zoom_in=(j % 2 == 0))
                clips.append(clip)
            stamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
            out = OUT_DIR / f"reel_marbella_{stamp}_{i+1}.mp4"
            concat(ff, clips, out, tdp)
            made.append(out)
            log(f"  ✓ reel {i+1}/{a.count}: {out.name} ({out.stat().st_size//1024} KB)")

    if a.no_upload:
        log(f"Done (local only): {len(made)} reels in {OUT_DIR}")
        return 0

    fid = ensure_subfolder(drive)
    up = 0
    for m in made:
        try:
            vid = upload_video(drive, m, fid); up += 1
            log(f"  ⬆ uploaded {m.name} -> Drive/{UPLOAD_SUBFOLDER} ({vid})")
        except Exception as e:
            log(f"  upload error {m.name}: {e}")
    log(f"Done: {len(made)} reels made, {up} uploaded to Drive/{UPLOAD_SUBFOLDER}")
    log("They'll be picked up by the next post_youtube.py run.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
