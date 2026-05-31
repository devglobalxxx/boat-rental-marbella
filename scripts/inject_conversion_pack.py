#!/usr/bin/env python3
"""Inject the conversion-pack widgets into every page:
  1. Live "just booked" ticker (rotating fake bookings)
  2. Sticky pulsing WhatsApp bubble (replaces the bare mobile-cta)
  3. Exit-intent popup with a different offer (welcome drink)
  4. Group discount badge (Marquee-style scarcity strip in hero)
"""
from __future__ import annotations
import re, glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "keyword_map.json").read_text())
SITE = CONFIG["site"]
WA = SITE.get("whatsapp_e164_noplus") or SITE["whatsapp_e164"].lstrip("+")


# ─── Widget 1: Live booking ticker ───────────────────────────────────────────
TICKER = '''
<!-- BEGIN LIVE_TICKER -->
<div id="liveBookingTicker" role="status" aria-live="polite" style="position:fixed;bottom:18px;left:18px;z-index:9997;max-width:300px;transform:translateY(140%);opacity:0;transition:transform 0.5s cubic-bezier(0.16, 1, 0.3, 1),opacity 0.4s;pointer-events:none;">
  <div style="display:flex;align-items:center;gap:10px;padding:10px 14px 10px 12px;background:linear-gradient(135deg,rgba(7,16,30,0.96) 0%,rgba(12,24,40,0.96) 100%);border:1px solid rgba(34,197,94,0.30);border-radius:14px;box-shadow:0 12px 32px rgba(0,0,0,0.50),0 0 0 1px rgba(34,197,94,0.08);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
    <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,rgba(34,197,94,0.15),rgba(34,197,94,0.08));border:1px solid rgba(34,197,94,0.30);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;">🚤</div>
    <div style="flex:1;min-width:0;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#22c55e;animation:pulse 1.5s ease-in-out infinite;flex-shrink:0;"></span>
        <span style="font-size:10px;color:#22c55e;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">Just booked</span>
      </div>
      <div id="liveTickerText" style="font-size:12px;color:rgba(244,244,242,0.85);line-height:1.4;font-weight:500;">—</div>
    </div>
    <button onclick="document.getElementById('liveBookingTicker').style.display='none'" aria-label="Close" style="background:none;border:none;color:rgba(244,244,242,0.40);cursor:pointer;font-size:14px;line-height:1;padding:4px;flex-shrink:0;font-family:-apple-system,sans-serif;">×</button>
  </div>
</div>
<style>@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.5;transform:scale(1.4)}}</style>
<script>
(function(){
  var BOOKS = [
    ["Anna", "Munich",   "Astondoa 40",      "next Saturday"],
    ["Marc", "Paris",    "Azimut 39",        "this weekend"],
    ["Lukas","Berlin",   "Mangusta 80",      "Jun 22"],
    ["Sophie","London",  "sunset cruise",    "this Friday"],
    ["Olivia","Stockholm","Catamaran charter","Aug 14"],
    ["David","Manchester","Astondoa 40",     "next Sunday"],
    ["Maria","Madrid",   "Azimut 58",        "Jul 5"],
    ["James","Dubai",    "luxury yacht",     "Aug 9"],
    ["Nora","Amsterdam", "Bavaria catamaran","Jun 28"],
    ["Hans","Zurich",    "Mangusta 80",      "Aug 17"],
    ["Sara","Oslo",      "sunset cruise",    "this Sunday"],
    ["Filip","Warsaw",   "Azimut 39",        "Jul 19"],
    ["Lucia","Milan",    "Astondoa 40",      "Aug 3"],
    ["Tom","Edinburgh",  "fishing boat",     "tomorrow"]
  ];
  var TIMES = ["just now","2 min ago","4 min ago","7 min ago","12 min ago","18 min ago","an hour ago","2h ago","3h ago"];
  var EL = document.getElementById('liveBookingTicker');
  var TXT = document.getElementById('liveTickerText');
  var i = Math.floor(Math.random()*BOOKS.length);

  function show(){
    var b = BOOKS[i % BOOKS.length];
    var t = TIMES[Math.floor(Math.random()*TIMES.length)];
    TXT.innerHTML = '<strong>'+b[0]+'</strong> from '+b[1]+' booked <strong>'+b[2]+'</strong><br><span style="color:rgba(244,244,242,0.45);font-size:11px;">for '+b[3]+' · '+t+'</span>';
    EL.style.transform='translateY(0)';EL.style.opacity='1';EL.style.pointerEvents='auto';
    setTimeout(function(){
      EL.style.transform='translateY(140%)';EL.style.opacity='0';
    }, 6000);
    i++;
  }
  setTimeout(show, 8000);          // first show after 8s
  setInterval(show, 22000);        // then every 22s
})();
</script>
<!-- END LIVE_TICKER -->
'''


# ─── Widget 2: Sticky pulsing WhatsApp bubble ────────────────────────────────
STICKY_WA = f'''
<!-- BEGIN STICKY_WA -->
<style>
@keyframes waPulse {{ 0%,100%{{ box-shadow:0 0 0 0 rgba(37,211,102,0.55), 0 8px 24px rgba(37,211,102,0.30); }} 50%{{ box-shadow:0 0 0 16px rgba(37,211,102,0), 0 8px 24px rgba(37,211,102,0.40); }} }}
.sticky-wa{{position:fixed;bottom:22px;right:22px;z-index:9996;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#25d366 0%,#128c7e 100%);display:flex;align-items:center;justify-content:center;text-decoration:none;animation:waPulse 2s ease-in-out infinite;transition:transform 0.2s;}}
.sticky-wa:hover{{transform:scale(1.08)}}
@media (max-width:480px){{ .sticky-wa{{bottom:18px;right:18px;width:54px;height:54px}} }}
</style>
<a class="sticky-wa" href="https://wa.me/{WA}?text=Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella" target="_blank" rel="nofollow noopener" aria-label="Chat on WhatsApp">
  <svg width="30" height="30" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.554-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>
</a>
<!-- END STICKY_WA -->
'''


# ─── Widget 3: Exit-intent popup (welcome drink offer) ──────────────────────
EXIT_POPUP = f'''
<!-- BEGIN EXIT_INTENT -->
<div id="exitIntent" role="dialog" aria-label="Wait — free welcome drink offer" aria-hidden="true" style="position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.75);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;padding:20px;animation:fadeIn 0.3s ease;">
  <div style="position:relative;max-width:440px;width:100%;background:linear-gradient(135deg,#07101e 0%,#0c1828 100%);border:2px solid rgba(201,168,78,0.30);border-radius:20px;padding:36px 32px 28px;box-shadow:0 32px 80px rgba(0,0,0,0.65);text-align:center;animation:popIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);">
    <button id="exitClose" aria-label="Close" style="position:absolute;top:14px;right:14px;width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);color:rgba(244,244,242,0.55);cursor:pointer;font-size:16px;line-height:1;padding:0;font-family:-apple-system,sans-serif;">×</button>
    <div style="font-size:54px;margin-bottom:8px;">🍾</div>
    <p style="font-size:11px;font-weight:800;color:#c9a84e;text-transform:uppercase;letter-spacing:0.14em;margin:0 0 12px;">Wait — before you go</p>
    <h2 style="font-size:28px;font-weight:800;color:#f4f4f2;line-height:1.15;letter-spacing:-0.02em;margin:0 0 12px;">
      Get a <span style="background:linear-gradient(135deg,#fde68a,#fbbf24,#c9a84e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">FREE welcome drink</span><br>on your charter
    </h2>
    <p style="font-size:14px;color:rgba(244,244,242,0.62);line-height:1.55;margin:0 0 22px;">Mention "WELCOME" when booking — your skipper will have a chilled bottle of Spanish cava waiting on board. 🥂</p>
    <a href="https://wa.me/{WA}?text=Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella%20and%20claim%20the%20FREE%20welcome%20drink%20%28code%3A%20WELCOME%29" target="_blank" rel="nofollow noopener" style="display:inline-flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:14px 22px;border-radius:50px;background:linear-gradient(135deg,#25d366 0%,#128c7e 100%);color:#fff;font-size:15px;font-weight:700;text-decoration:none;box-shadow:0 6px 20px rgba(37,211,102,0.35);">
      💬 Claim my free cava
    </a>
    <button id="exitDecline" style="display:block;margin:14px auto 0;background:none;border:none;color:rgba(244,244,242,0.40);font-size:12px;cursor:pointer;text-decoration:underline;">No thanks, take me away</button>
  </div>
</div>
<style>
@keyframes fadeIn {{ from {{ opacity:0 }} to {{ opacity:1 }} }}
@keyframes popIn {{ from {{ opacity:0; transform:scale(0.92) translateY(20px) }} to {{ opacity:1; transform:scale(1) translateY(0) }} }}
</style>
<script>
(function(){{
  var KEY='exitIntentShown';
  try{{ if(localStorage.getItem(KEY)){{var t=parseInt(localStorage.getItem(KEY),10);if(Date.now()-t<7*86400000)return;}} }}catch(e){{}}
  var EL=document.getElementById('exitIntent');
  if(!EL)return;
  var shown=false;
  function show(){{
    if(shown)return;shown=true;
    EL.style.display='flex';
    EL.setAttribute('aria-hidden','false');
    try{{localStorage.setItem(KEY,String(Date.now()));}}catch(e){{}}
  }}
  function hide(){{
    EL.style.display='none';EL.setAttribute('aria-hidden','true');
  }}
  // Desktop exit intent
  document.addEventListener('mouseout', function(e){{
    if(!e.relatedTarget && e.clientY<10) show();
  }});
  // Mobile: after 30s + scroll-to-bottom signal
  var mobileTimer=setTimeout(function(){{ if(window.innerWidth<=768 && window.scrollY>document.body.scrollHeight*0.50) show(); }}, 30000);
  document.getElementById('exitClose').addEventListener('click',hide);
  document.getElementById('exitDecline').addEventListener('click',hide);
  EL.addEventListener('click',function(e){{if(e.target===EL)hide();}});
}})();
</script>
<!-- END EXIT_INTENT -->
'''


# ─── Widget 4: Scarcity strip (above hero or top of body) ────────────────────
SCARCITY_STRIP = '''
<!-- BEGIN SCARCITY_STRIP -->
<div id="scarcityStrip" style="background:linear-gradient(90deg,rgba(248,113,113,0.10) 0%,rgba(245,158,11,0.10) 50%,rgba(248,113,113,0.10) 100%);border-bottom:1px solid rgba(245,158,11,0.20);padding:8px 16px;text-align:center;font-size:12px;color:#fbbf24;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;">
  <span style="width:6px;height:6px;border-radius:50%;background:#f87171;animation:pulse 1.5s ease-in-out infinite;"></span>
  <span><strong style="color:#fde68a;">High demand:</strong> <span id="scarcityCount">12</span> people viewed boats in the last hour · Only <strong style="color:#fbbf24;" id="scarcitySpots">4</strong> dates left in <span id="scarcityMonth">June</span></span>
</div>
<script>
(function(){
  var MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
  var d=new Date();
  document.getElementById('scarcityMonth').textContent=MONTHS[d.getMonth()];
  document.getElementById('scarcityCount').textContent=8+Math.floor(Math.random()*18);
  document.getElementById('scarcitySpots').textContent=2+Math.floor(Math.random()*5);
})();
</script>
<!-- END SCARCITY_STRIP -->
'''


# ─── Patterns ────────────────────────────────────────────────────────────────
TICKER_RE   = re.compile(r'<!-- BEGIN LIVE_TICKER -->.*?<!-- END LIVE_TICKER -->',   re.DOTALL)
STICKY_RE   = re.compile(r'<!-- BEGIN STICKY_WA -->.*?<!-- END STICKY_WA -->',       re.DOTALL)
EXIT_RE     = re.compile(r'<!-- BEGIN EXIT_INTENT -->.*?<!-- END EXIT_INTENT -->',   re.DOTALL)
SCARCITY_RE = re.compile(r'<!-- BEGIN SCARCITY_STRIP -->.*?<!-- END SCARCITY_STRIP -->', re.DOTALL)


def inject(html: str) -> str:
    # remove any existing instances (idempotent)
    for pat in (TICKER_RE, STICKY_RE, EXIT_RE, SCARCITY_RE):
        html = pat.sub('', html)

    # Append widgets before </body>
    if '</body>' in html:
        widgets = TICKER + STICKY_WA + EXIT_POPUP
        html = html.replace('</body>', widgets + '\n</body>')

    # Inject scarcity strip right after <body>
    body_open = re.search(r'<body[^>]*>', html)
    if body_open:
        idx = body_open.end()
        html = html[:idx] + '\n' + SCARCITY_STRIP + html[idx:]

    return html


def main():
    updated = 0
    for path in glob.glob('site/**/*.html', recursive=True):
        with open(path) as f:
            html = f.read()
        new_html = inject(html)
        if new_html != html:
            with open(path, 'w') as f:
                f.write(new_html)
            updated += 1
    print(f"Conversion pack injected into {updated} pages")


if __name__ == "__main__":
    main()
