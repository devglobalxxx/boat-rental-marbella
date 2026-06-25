"""Google Maps Places (New) text-search seed — pulls boat-rental operators
(name + website + phone, i.e. Google Business Profile data) into leads.db.
Self-contained (embedded city list); supports sharding for parallel agents.

  python3 -m scripts.scraper.seed_maps --shard 0 --shards 10
  python3 -m scripts.scraper.seed_maps --limit-cities 5      # pilot
"""
from __future__ import annotations
import argparse, json, os, time, pathlib, urllib.request, urllib.error
import tldextract
from . import store

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

CITIES = [
    ("Marbella","ES"),("Puerto Banus","ES"),("Estepona","ES"),("Fuengirola","ES"),("Malaga","ES"),
    ("Sotogrande","ES"),("Benalmadena","ES"),("Nerja","ES"),("Almeria","ES"),("Cadiz","ES"),
    ("Alicante","ES"),("Denia","ES"),("Javea","ES"),("Valencia","ES"),("Barcelona","ES"),
    ("Palma de Mallorca","ES"),("Ibiza","ES"),("Formentera","ES"),("Menorca","ES"),("Alcudia","ES"),
    ("Las Palmas","ES"),("Tenerife","ES"),("Lanzarote","ES"),
    ("Lisbon","PT"),("Algarve","PT"),("Vilamoura","PT"),("Lagos Portugal","PT"),("Albufeira","PT"),("Madeira","PT"),
    ("Nice","FR"),("Cannes","FR"),("Antibes","FR"),("Saint-Tropez","FR"),("Marseille","FR"),("Monaco","MC"),("Ajaccio","FR"),
    ("Genoa","IT"),("Portofino","IT"),("Naples","IT"),("Amalfi","IT"),("Capri","IT"),("Sorrento","IT"),
    ("Olbia","IT"),("Porto Cervo","IT"),("Cagliari","IT"),("Palermo","IT"),("Catania","IT"),("Venice","IT"),("Rimini","IT"),
    ("Split","HR"),("Dubrovnik","HR"),("Zadar","HR"),("Hvar","HR"),("Sibenik","HR"),("Trogir","HR"),
    ("Athens","GR"),("Mykonos","GR"),("Santorini","GR"),("Rhodes","GR"),("Corfu","GR"),("Crete","GR"),
    ("Lefkada","GR"),("Kos","GR"),("Paros","GR"),("Naxos","GR"),
    ("Valletta","MT"),("Sliema","MT"),("Limassol","CY"),("Paphos","CY"),("Larnaca","CY"),
    ("Bodrum","TR"),("Marmaris","TR"),("Fethiye","TR"),("Gocek","TR"),("Antalya","TR"),
    ("Miami","US"),("Fort Lauderdale","US"),("Key West","US"),("Naples Florida","US"),("Tampa","US"),
    ("San Diego","US"),("Los Angeles","US"),("Newport Beach","US"),("San Francisco","US"),("Seattle","US"),
    ("New York","US"),("Boston","US"),("Newport RI","US"),("Charleston SC","US"),("Annapolis","US"),
    ("Chicago","US"),("Lake Tahoe","US"),("Austin","US"),("Honolulu","US"),("Maui","US"),("New Orleans","US"),("Galveston","US"),
    ("Cancun","MX"),("Playa del Carmen","MX"),("Tulum","MX"),("Cabo San Lucas","MX"),("Puerto Vallarta","MX"),("La Paz Mexico","MX"),
    ("Nassau","BS"),("Exuma","BS"),("Tortola","VG"),("St Thomas","VI"),("St Martin","MF"),("Antigua","AG"),
    ("St Lucia","LC"),("Barbados","BB"),("Aruba","AW"),("Curacao","CW"),("San Juan PR","PR"),("Punta Cana","DO"),
    ("Cartagena Colombia","CO"),("Rio de Janeiro","BR"),("Angra dos Reis","BR"),("Buzios","BR"),("Florianopolis","BR"),
    ("Dubai","AE"),("Abu Dhabi","AE"),("Doha","QA"),("Muscat","OM"),("Tel Aviv","IL"),("Beirut","LB"),
    ("Cape Town","ZA"),("Mauritius","MU"),("Seychelles","SC"),("Zanzibar","TZ"),("Hurghada","EG"),("Sharm El Sheikh","EG"),
    ("Male Maldives","MV"),("Phuket","TH"),("Krabi","TH"),("Koh Samui","TH"),("Pattaya","TH"),
    ("Langkawi","MY"),("Singapore","SG"),("Bali","ID"),("Lombok","ID"),("Komodo","ID"),("Manila","PH"),("Cebu","PH"),("Phu Quoc","VN"),
    ("Hong Kong","HK"),("Tokyo","JP"),("Okinawa","JP"),("Jeju","KR"),
    ("Sydney","AU"),("Gold Coast","AU"),("Whitsundays","AU"),("Perth","AU"),("Cairns","AU"),
    ("Auckland","NZ"),("Bay of Islands","NZ"),("Fiji","FJ"),("Tahiti","PF"),("Bora Bora","PF"),
    ("Southampton","GB"),("Poole","GB"),("Cowes","GB"),("Brighton","GB"),("Plymouth","GB"),("Dublin","IE"),
    ("Amsterdam","NL"),("Hamburg","DE"),("Copenhagen","DK"),("Stockholm","SE"),("Oslo","NO"),
    # tier-2 expansion
    ("Torrevieja","ES"),("Cartagena Spain","ES"),("Roses","ES"),("Palamos","ES"),("Sitges","ES"),
    ("Santa Pola","ES"),("Mazarron","ES"),("Calpe","ES"),("Altea","ES"),("Gandia","ES"),
    ("Vigo","ES"),("La Coruna","ES"),("Santander","ES"),("San Sebastian","ES"),
    ("Faro","PT"),("Portimao","PT"),("Cascais","PT"),("Sesimbra","PT"),
    ("La Rochelle","FR"),("Hyeres","FR"),("Bandol","FR"),("Cassis","FR"),("Porquerolles","FR"),("Bonifacio","FR"),("Calvi","FR"),
    ("La Spezia","IT"),("Viareggio","IT"),("Gaeta","IT"),("Salerno","IT"),("Tropea","IT"),("Gallipoli","IT"),
    ("Alghero","IT"),("La Maddalena","IT"),("Trapani","IT"),("Lipari","IT"),("Ischia","IT"),("Procida","IT"),
    ("Pula","HR"),("Rovinj","HR"),("Zadar","HR"),("Vodice","HR"),("Makarska","HR"),("Korcula","HR"),
    ("Kotor","ME"),("Tivat","ME"),("Budva","ME"),
    ("Volos","GR"),("Kavala","GR"),("Lefkas","GR"),("Zakynthos","GR"),("Kefalonia","GR"),
    ("Skiathos","GR"),("Milos","GR"),("Naxos","GR"),("Kos","GR"),("Chania","GR"),
    ("Kas","TR"),("Cesme","TR"),("Datca","TR"),("Gocek","TR"),
    ("Sarasota","US"),("Clearwater","US"),("Destin","US"),("Panama City Beach","US"),("Pensacola","US"),
    ("Marathon FL","US"),("Sarasota","US"),("Hilton Head","US"),("Virginia Beach","US"),("Lake Havasu","US"),
    ("Marina del Rey","US"),("Long Beach","US"),("Santa Barbara","US"),("Sausalito","US"),("Tahoe City","US"),
    ("Cozumel","MX"),("Acapulco","MX"),("Mazatlan","MX"),("Isla Mujeres","MX"),
    ("Roatan","HN"),("Bocas del Toro","PA"),("Tamarindo","CR"),("San Andres","CO"),
    ("Grenada","GD"),("St Vincent","VC"),("Martinique","MQ"),("Guadeloupe","GP"),("Bahamas Nassau","BS"),
    ("Ras Al Khaimah","AE"),("Fujairah","AE"),("Manama","BH"),("Salalah","OM"),
    ("Gocek","TR"),("Hvar","HR"),("Mahe","SC"),("Praslin","SC"),
    ("Nha Trang","VN"),("Halong Bay","VN"),("Boracay","PH"),("Palawan","PH"),("El Nido","PH"),
    ("Gili Islands","ID"),("Sanur","ID"),("Pattaya","TH"),("Hua Hin","TH"),
    ("Airlie Beach","AU"),("Hamilton Island","AU"),("Mooloolaba","AU"),("Mandurah","AU"),("Hobart","AU"),
    ("Tauranga","NZ"),("Queenstown NZ","NZ"),
]

QUERIES = ["boat rental in {city}", "yacht charter in {city}", "boat hire in {city}",
           "jet ski rental in {city}", "catamaran charter in {city}", "fishing charter in {city}",
           "sailing charter in {city}", "speedboat rental in {city}", "party boat rental in {city}",
           "sunset cruise in {city}"]

EXCLUDE = {"clickandboat.com","samboat.com","boatsetter.com","getmyboat.com","boataround.com",
           "yachtcharterfleet.com","sailogy.com","facebook.com","instagram.com","tripadvisor.com",
           "viator.com","getyourguide.com","google.com","bednblue.com","expedia.com","booking.com"}

def _load_env():
    p = pathlib.Path(__file__).resolve().parents[2] / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,_,v=line.partition("="); os.environ.setdefault(k.strip(), v.strip())

def _root(url):
    try:
        ext=tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else None
    except Exception: return None

def search(query, key, n=20):
    payload=json.dumps({"textQuery":query,"maxResultCount":n}).encode()
    req=urllib.request.Request(ENDPOINT, data=payload, method="POST", headers={
        "Content-Type":"application/json","X-Goog-Api-Key":key,
        "X-Goog-FieldMask":"places.displayName,places.websiteUri,places.nationalPhoneNumber,places.internationalPhoneNumber"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("places", [])
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:160]}"); return None
    except Exception as e:
        print(f"  {type(e).__name__}: {e}"); return None

def run(shard=None, shards=None, limit_cities=None, queries_per_city=4, only=None):
    _load_env()
    key=os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key: print("ERROR: GOOGLE_MAPS_API_KEY missing"); return {"added":0}
    con=store.connect()
    if only:
        names={n.strip().lower() for n in only.split(",") if n.strip()}
        known={c.lower():(c,co) for c,co in CITIES}
        cities=[known.get(n,(n.title(),"AE")) for n in names]
    else:
        cities=CITIES[:limit_cities] if limit_cities else CITIES
    if shards: cities=[c for i,c in enumerate(cities) if i%shards==shard]
    added=phoned=0
    for ci,(city,country) in enumerate(cities,1):
        for q in QUERIES[:queries_per_city]:
            query=q.format(city=city)
            ck=f"maps::{query}"
            if store.url_seen(con, ck): continue
            places=search(query, key, 20)
            if places is None:
                print("API error — stopping shard."); return {"added":added,"phoned":phoned}
            store.mark_url(con, ck, 200 if places else 1)
            for p in places:
                web=p.get("websiteUri","")
                if not web: continue
                root=_root(web)
                if not root or root in EXCLUDE or any(root.endswith("."+b) for b in EXCLUDE): continue
                name=(p.get("displayName") or {}).get("text","")[:120]
                phone=p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber") or ""
                store.add_seed(con, root, city, country, "google_maps", company=name)
                added+=1
                if phone:
                    row=con.execute("SELECT phones FROM leads WHERE domain=?", (root,)).fetchone()
                    ex=[]
                    try: ex=json.loads(row[0]) if row and row[0] else []
                    except Exception: pass
                    if phone not in ex:
                        ex.append(phone)
                        con.execute("UPDATE leads SET phones=? WHERE domain=?", (json.dumps(sorted(set(ex))), root)); con.commit(); phoned+=1
            time.sleep(0.4)
        print(f"  [{ci:>3}/{len(cities)}] {city:<20} added={added} phoned={phoned}", flush=True)
    return {"added":added,"phoned":phoned}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--shard",type=int); ap.add_argument("--shards",type=int)
    ap.add_argument("--limit-cities",type=int); ap.add_argument("--queries",type=int,default=4)
    ap.add_argument("--city",type=str,help="comma-separated city names to target (overrides shard/limit-cities)")
    a=ap.parse_args()
    print(run(a.shard,a.shards,a.limit_cities,a.queries,a.city))
