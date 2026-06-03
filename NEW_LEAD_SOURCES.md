# BoatHire24 — New Lead Sources Playbook

## 1. Executive Summary

This playbook maps 30+ net-new, scrapeable lead sources for BoatHire24's owner-supply outreach — directories, registries, and listicles that publish operators' own phone/website/email rather than gating contact behind a marketplace booking flow (unlike Boatsetter, Click&Boat, GetMyBoat, which forbid off-platform contact). Sources span three families: industry/association operator directories (charter brokers, fishing-charter associations, watersports), regional tourism portals plus official government registries, and editorial listicles/review platforms. They are ranked by scrape-value — operator volume × email/website exposure × low scrape difficulty. The highest-yield work this week is a handful of easy, server-rendered sources that expose inline contact: TopBarcos (the home Málaga/Marbella market), CYBA and AYCA (inline email after Cloudflare de-obfuscation), the DMA Yachting Greek/Croatian curated lists, and CharterWorld's bulk broker dump. For website-only sources, the standard second pass is to crawl each operator's own `/contact` (or `/impressum`, `/contacto`) page to harvest email; treat booking-gated platforms (FishingBooker, Guidesly, FishAnywhere, Yumping) strictly as name+geo seed lists for external enrichment.

## 2. TOP-15 Sources Ranked by Scrape-Value

| Rank | Source | Region | Operators | Exposes | Difficulty | Scrape method |
|------|--------|--------|-----------|---------|------------|---------------|
| 1 | [TopBarcos — Directorio de Empresas Náuticas](https://www.topbarcos.com/directorio-empresas-nauticas/embarcaciones/alquiler-charter) | **Spain (Málaga/Cádiz/Baleares — home geo)** | Hundreds | Phone + website | Easy | Iterate `buscador-empresas-nauticas?actividad=alquiler+-+charter&b_start:int=N` (N+=30) or per-province pages; fetch each *ficha* for name, port, phone, outbound website. Server-rendered, no JS. |
| 2 | [CYBA — Charter Yacht Brokers Assoc.](https://www.cyba.net/member-directory/) | Worldwide (US, Caribbean, Med, Greece, Turkey) | ~200–330 | **Email + website + phone + person** | Easy | Single non-paginated page; parse member cards. Decode Cloudflare `data-cfemail` (XOR first byte as key). Cross-check `cyba.info/cyba-members/directory/`. |
| 3 | [CharterWorld — Broker Company Lists 1/2/3](https://www.charterworld.com/index.html?sub=broker-company-list1) | Worldwide | ~300+ (plus ~450+ via Med/Caribbean pages) | Phone + address | Easy | Fetch 3 static pages (`broker-company-list1/2/3`), regex-parse comma-delimited lines (name, street, city/country, phone, fax). Plain HTML. |
| 4 | [AYCA — American Yacht Charter Assoc.](https://ayca.net/membership/our-members/) | US / North America | ~80+ | **Email + website + phone + address** | Easy | Single page, members in expandable sections; de-obfuscate emails. |
| 5 | [DMA Yachting — Greek Charter Companies](https://mygreekcharter.com/list-of-greek-yacht-charter-companies/) | Greece (nationwide) | ~80+ | Phone + website | Easy | One GET, parse consistent table (name, address, phone, outbound site); follow each site for email. |
| 6 | [NACO — Nat'l Assoc. of Charterboat Operators](https://www.nacocharters.org/directory.html) | USA (all 50 states) | Hundreds | Name + phone + website + email | Easy | Crawl index for `/directory/<state>.html`, parse member rows. Retry with browser if empty. |
| 7 | [Boaters List — Rentals/Yacht-Charters](https://www.boaterslist.com/store-listing/page/1/?store_categories=rentals-yacht-charters) | USA nationwide | Thousands (170+ pages) | Phone + website + often email/form | Medium | Paginate `/store-listing/page/<N>/?store_categories=rentals-yacht-charters` (~173); follow store profiles. 403s plain — use real browser UA. |
| 8 | [Central Yacht Agent — Find a Broker](https://www.centralyachtagent.com/findabroker.php) | Worldwide (heavy US/FL + Caribbean) | Hundreds (A–Z) | Website + phone + person (email on detail) | Easy–Medium | Iterate each letter filter (~36 requests), parse blocks; follow company link for email. |
| 9 | [Virgilio Aziende — Nautica · Noleggio Barche](https://www.virgilio.it/italia/elenco/ricerca-aziende/nautica-noleggio-barche_(24)) | Italy nationwide | ~1,031 | Phone + address (website/email on detail) | Medium | Paginate `…nautica-noleggio-barche_(N)` N=1..~27; follow `aziende.virgilio.it/nautica/{city}/{name}`. PagineGialle.it fallback. |
| 10 | [Charter Boats UK (CBUK)](https://www.charterboats-uk.co.uk/) | UK by port | 450+ skippers | Phone + website + email | Medium | Enumerate port IDs (`/boats/packages/?portId=NNN`), parse boat profiles. Cloudflare 403 — headless browser, realistic UA, delays. |
| 11 | [Fin & Field — Operators by US state](https://www.finandfield.com/directory/CT) | USA all 50 states | Thousands | Phone + website + email (detail) | Medium | Iterate `/directory/<STATE_ABBR>`, collect profile URLs, fetch each, filter type=`Charter Boat`. |
| 12 | [Yumping — Boat Rental directory](https://www.yumping.com/en/boat-rental/andalucia) | Spain + Italy (Andalucía 274; Sardegna 65) | Thousands | Contact form (name + location) | Medium | Region pages `/en/boat-rental/{region}` paginate 20/page; cards link to company profiles. Name+website-resolution seed, not raw email. |
| 13 | [Ludington (MI) Charter Boat Assoc.](https://charterludington.com/business-directory/wpbdp_category/fishingcharter/) | USA / Lake Michigan | ~20–40 | **Captain + phone + website + email** | Easy | WordPress Business Directory (wpbdp); paginate category, parse structured listing markup. |
| 14 | [Erie County (NY) Charter Captains](https://www3.erie.gov/environment/charter-captains) | USA / Lake Erie–Niagara | ~30–60 | Phone + many websites | Easy | Parse static gov HTML; follow website links for email. |
| 15 | [Ezilon Europe — Croatia Yacht Charter](https://www.ezilon.com/regional/croatia/travel/yacht_charter/index.shtml) | Croatia (template → Greece/France) | ~22/page | Website + blurb | Easy | Static HTML, `previous 1 next` pagination; parse name + outbound site, follow for email. |

## 3. The Three Sections (Deduped)

> Dedup rule: sources that recur across sections (TopBarcos, Virgilio, Yumping, Nautica.it, mycroatiancharter, Smarter Fishing Charters, BIA Australia) are listed once, in their strongest-fit section, and cross-referenced where they reappear.

### 3.1 Scrapeable Operator Directories (Charter, Fishing, Watersports, Broker)

Old-school directories (associations, industry rosters, regional portals) that publish operators' own phone/website/email — unlike P2P marketplaces that gate contact behind internal booking. Verified June 2026.

**Tier 1 — Highest yield (big volume OR inline email/website, easy)**

1. **[CharterWorld — Broker Company Lists 1/2/3](https://www.charterworld.com/index.html?sub=broker-company-list1)** — Worldwide — ~300+ brokers (plus ~450+ via Med/Caribbean company pages) — phone + address (website/email sparse) — fetch 3 static pages, regex-parse comma-delimited lines. **Easy.** Largest pure name+address+phone dump found.
2. **[CYBA — Charter Yacht Brokers Association](https://www.cyba.net/member-directory/)** — Worldwide — ~200–330 members — **email + website + phone + person** — single page; decode Cloudflare `data-cfemail` (XOR first byte as key). Cross-check `cyba.info/cyba-members/directory/`. **Easy.** Best signal-to-noise B2B source.
3. **[TopBarcos — Directorio de Empresas Náuticas](https://www.topbarcos.com/directorio-empresas-nauticas/embarcaciones/alquiler-charter)** — **Spain (Málaga/Cádiz/Baleares — core geo)** — hundreds — phone + website — two-step buscador/per-province → *ficha*. Server-rendered, no JS. **Easy.** *Top regional source for Andalusia; also a submission venue.* (Also appears in §3.2 and §3.3.)
4. **[AYCA — American Yacht Charter Association](https://ayca.net/membership/our-members/)** — US/North America — ~80+ — **email + website + phone + address** — single page, expandable sections; de-obfuscate emails. **Easy.**
5. **[Boaters List — Rentals/Yacht-Charters](https://www.boaterslist.com/store-listing/page/1/?store_categories=rentals-yacht-charters)** — USA nationwide — thousands (170+ pages) — phone + website + often email/form — paginate to ~173, follow store profiles; also `fishing-charters`, `boat-rentals` slugs. 403s plain — real browser UA. **Medium** (downgraded by volume).

**Tier 2 — Strong volume, two-hop or browser needed**

6. **[Central Yacht Agent — Find a Broker](https://www.centralyachtagent.com/findabroker.php)** — Worldwide (heavy US/FL + Caribbean) — hundreds (A–Z) — website + phone + person (email on detail) — iterate each letter filter (~36 requests); follow company link. Verified live (Cruzan, MGM Yachts, Regency). **Easy–Medium.**
7. **[Charter Boats UK (CBUK)](https://www.charterboats-uk.co.uk/)** — UK by port — 450+ skippers — phone + website + email — enumerate port IDs (`/boats/packages/?portId=NNN`). Cloudflare 403 — headless browser, UA, delays. **Medium.** Highest-value single UK fishing source.
8. **[Virgilio Aziende — Nautica · Noleggio Barche](https://www.virgilio.it/italia/elenco/ricerca-aziende/nautica-noleggio-barche_(24))** — Italy nationwide — ~1,031 — phone + address (website/email on detail) — paginate `_(N)` N=1..~27; follow `aziende.virgilio.it/nautica/{city}/{name}`. PagineGialle.it fallback. **Medium.** Strongest Italy source by volume. (Cross-ref §3.2.)
9. **[Fin & Field — Fishing/Hunting Operators by US state](https://www.finandfield.com/directory/CT)** — USA all 50 states — thousands — phone + website + email (detail) — iterate `/directory/<STATE_ABBR>`, filter type=`Charter Boat`. **Medium.**
10. **[FishingBooker — Fishing Charters by Destination](https://fishingbooker.com/destinations)** — Worldwide (110 countries) — 12,000+ boats — name + captain + city only (contact gated) — two-hop crawl `/destinations` → location → `/charters/view/<id>`. Scraping is against ToS. **Use as name+location seed, enrich via search.** **Hard.**

**Tier 3 — Regional fishing-charter associations (members publish own contact)**

11. **[NACO — National Assoc. of Charterboat Operators](https://www.nacocharters.org/directory.html)** — USA all 50 states — hundreds — name + phone + website + email — crawl index for `/directory/<state>.html`. **Easy.** Best nationwide US fishing yield.
12. **[Maryland DNR — Licensed Charter Boats map](https://dnr.maryland.gov/fisheries/pages/charters/map.aspx)** — USA/Maryland (Chesapeake) — hundreds licensed — name + phone + website — mine the backing JSON/GeoJSON feed via devtools/network. Authoritative legal list. **Hard.**
13. **[Ludington (MI) Charter Boat Assoc.](https://charterludington.com/business-directory/wpbdp_category/fishingcharter/)** — USA/Lake Michigan — ~20–40 — captain + phone + website + email — WordPress wpbdp; paginate category. **Easy.** Clean Great Lakes source.
14. **[Upper Bay Charter Captains](http://www.baycaptains.com/captains-directory.html)** — USA/Chesapeake (MD) — ~20–40 — boat + phone + website/email — static page, parse directly. **Easy.**
15. **[Erie County (NY) Charter Captains](https://www3.erie.gov/environment/charter-captains)** — USA/Lake Erie–Niagara — ~30–60 — phone + many websites — parse static gov HTML; follow website links. **Easy.**
16. **[Northeast Charterboat Captains Assoc.](https://www.northeastcharterboatcaptainsassociation.com/membersbusiness)** — USA/New England — 50+ — website + phone + email (per-state subpages) — crawl ME/MA/NH/RI/CT; Wix-style, render if needed. **Medium.**
17. **[Cape Cod Charter Boat Assoc.](https://capecodcharterassociation.com/cccba-captains/)** — USA/Cape Cod — ~30–50 — name + boat + phone + email + website — parse captain cards. 403 — headless browser/real UA. **Medium.**
18. **[Maine Assoc. of Charterboat Captains](http://www.mainechartercaptains.org/)** — USA/Maine — 80+ — captain + phone + website + email — parse member blocks; site flaky (ECONNREFUSED) — browser with retries. **Medium.**

**Tier 4 — International / niche (regional breadth)**

19. **[Canal Junction — UK Day Hire Operators](https://www.canaljunction.com/narrowboat/day_hire.htm)** — UK canals — ~60+ — phone + email + website — single static page grouped by waterway. **Easy.** Net-new self-drive niche.
20. **[Smarter Fishing Charters (AU)](https://www.smarterfishingcharters.com.au/charters)** & **[Fishing Charters Australia](https://fishingchartersaustralia.com.au/directory-of-australian-fishing-charters/)** — Australia by state/region — dozens–hundreds each — phone + website (+ email) — crawl state/region index (JS — render), then listings. **Medium.** (Cross-ref §3.3.)
21. **[Thailand Marine Guide](https://thaimarineguide.com/listings/)** — Thailand (Phuket/Pattaya/Samui/Krabi) — ~60 marine; ~30 charter+broker — phone + website + email — paginate `/listings/?page=1..3`, fetch each detail. **Easy.**
22. **[BIA Australia — Charter Vessels category](https://bia.org.au/directory-category/charter-vessels/)** — Australia (NSW/QLD/VIC/WA) — ~26 in category (600+ all) — phone + website + address (email on detail) — single category page inline; follow `/directory/<slug>/`. Swap category slugs (boat-hire, day-cruises, marine-brokers). **Easy.**

**Tier 5 — Seed lists only (names, no inline contact — enrich externally)**

23. **[Guidesly](https://guidesly.com/sitemap)** — Global/US — 3,500+ guides — name + location only (booking-funneled) — enumerate `/book-a-guide/guide-details/<Name>` from sitemap. **Easy** (enrichment required).
24. **[FishAnywhere](https://fishanywhere.com/charters-guides)** — USA (FL/Gulf heavy) — thousands — name + location only (booking-gated) — scrape seeds, enrich via search. **Easy.**

### 3.2 Regional Tourism Portals & Country B2B Directories

Net-new geographic directories and official tourism registries surfacing operator name + location, and (for top-ranked) website/phone to pivot from for email.

**Tier 1 — High volume, website/phone exposed, easy-to-medium**

1. **[Virgilio Aziende — Nautica · Noleggio Barche (Italy)](https://www.virgilio.it/italia/elenco/ricerca-aziende/nautica-noleggio-barche_(24))** — Italy nationwide — ~1,031 — phone + full address universal; website/email on detail — paginate `_(N)` N=1..~27; follow detail URLs. PagineGialle.it fallback. **Medium.** *(Primary listing in §3.1 #8.)*
2. **[TopBarcos — Directorio de Empresas Náuticas (Spain)](https://www.topbarcos.com/directorio-empresas-nauticas/embarcaciones/alquiler-charter)** — Spain all provinces (best Andalusia + Baleares) — hundreds — phone + website — two-step buscador/per-province → ficha. **Easy. Top pick for home Málaga/Marbella market.** *(Primary listing in §3.1 #3.)*
3. **[Yumping — Boat Rental directory (Spain & Italy)](https://www.yumping.com/en/boat-rental/andalucia)** — Andalucía 274 (Málaga 112 / Cádiz 59 / Almería 46); Sardegna 65 — contact form (name + location; raw email not shown) — region pages paginate 20/page; cards link to company profiles. **Medium.** Name+website-resolution source. (Cross-ref §3.3.)

**Tier 2 — Curated regional lists, website/phone inline, very easy**

4. **[Nautica.it — Noleggio Barche / Charter (Italy)](https://www.nautica.it/noleggio-barche/)** — Italy by region (Sardegna, Liguria, Tirreno) — ~12 paginated pages — outbound link to each agency's own site — paginate `…/noleggio-barche-charter/page/N/` N=1..12. 403 to plain WebFetch — real browser UA. **Medium.** (Cross-ref §3.3.)
5. **[mycroatiancharter.com — Croatia Yacht Charter Providers](https://mycroatiancharter.com/list-of-croatia-yacht-charter-providers/)** — Croatia/Adriatic (Split, Biograd, Zadar, Dubrovnik) — ~12 vetted — website + phone + address (email not inline) — single static HTML table, one fetch; follow each site. **Easy.** Low volume, high precision. (Cross-ref §3.3.)

**Tier 3 — Official government registries (legitimacy/enrichment layer, low direct contact)**

6. **[Junta de Andalucía — Registro de Turismo](https://www.juntadeandalucia.es/organismos/turismoyandaluciaexterior/areas/registro-turismo/buscador-establecimientos-servicios-turisticos.html)** — Andalusia (Málaga/Marbella, Cádiz, Granada, Almería) — unknown count; filter "Turismo Activo" — name + registration nº + municipality + address (no reliable phone/email) — JS/form-driven buscador; drive headless browser (Playwright). **Hard.** Authoritative legality filter; enrichment only.
7. **[Consell de Mallorca / CAIB — Registre d'Empreses i Establiments Turístics (Baleares)](https://www.caib.es/cathosfront/cens?id=138034&lang=ES)** — Balearic Islands (Mallorca) — large census, filter Grup/Categoria — registration nº + commercial name + municipi + address (no phone/email) — JS-driven census, "Veu en taula" view, headless browser. Cross-ref Balearic "Registre de Declaracions Responsables de Xàrter Nàutic" (Decret 44/2025). **Hard.** Cleanest Baleares legitimacy filter; enrichment only.

### 3.3 Listicles, Review Platforms & Social Discovery + Submission Venues

Editorial "best-of" articles, curated round-ups, activity marketplaces, review directories. Lower-volume but clean and fast; the curated ones carry outbound links to operators' own sites. Submission venues (where we can list BoatHire24) are flagged.

1. **[DMA Yachting — Greek Yacht Charter Companies (MyGreekCharter)](https://mygreekcharter.com/list-of-greek-yacht-charter-companies/)** — Greece nationwide — ~80+ — phone + website (outbound per row); email via linked site — single non-paginated page, consistent table; one GET. **Easy. Top pick of this section** — best volume-to-effort.
2. **[TopBarcos — Directorio de Empresas Náuticas](https://www.topbarcos.com/directorio-empresas-nauticas/embarcaciones/alquiler-charter)** — Spain (core Andalusia/Marbella) — hundreds — phone + website — two-step. **Easy.** Doubles as a **submission venue** (operators self-list). *(Primary listing §3.1 #3.)*
3. **[Yumping — Boat-Rental directory](https://www.yumping.com/en/boat-rental/andalucia)** — Andalucía 274; Sardegna 65 — contact form (name + location) — region pages paginate 20/page. **Medium. Submission venue** too. *(Primary listing §3.2 #3.)*
4. **[Bayut MyBayut — Companies for Yacht Rental in Dubai](https://www.bayut.com/mybayut/companies-yacht-rental-dubai/)** — UAE (Dubai) — ~10 named — phone + address (no email/website inline) — single editorial article, per-company blocks; plain HTML. **Easy.** Clean UAE seed set. Low volume.
5. **[mycroatiancharter.com — Croatia Yacht Charter Providers](https://mycroatiancharter.com/list-of-croatia-yacht-charter-providers/)** — Croatia (Split, Biograd, Zadar, Dubrovnik) — ~12 — phone + website + address; email via linked site — single page table. **Easy.** *(Primary listing §3.2 #5.)*
6. **[Smarter Fishing Charters (AU)](https://www.smarterfishingcharters.com.au/charters)** — Australia by state/region — dozens–hundreds — phone + website (mixed) — crawl state/region index then listings; render if JS. **Medium. Submission venue** for AU. *(Cross-ref §3.1 #20.)*
7. **[Ezilon Europe — Croatia Yacht Charter](https://www.ezilon.com/regional/croatia/travel/yacht_charter/index.shtml)** — Croatia (template → Greece/France via `/regional/<country>/travel/yacht_charter`) — ~22/page — website + blurb (no phone/email inline) — static HTML, `previous 1 next` pagination. **Easy.** Same scraper covers three target countries.
8. **[Nautica.it — Noleggio Barche / Charter](https://www.nautica.it/noleggio-barche/)** — Italy by region — ~12 paginated pages — website (outbound to agency site) — paginate `/noleggio-barche-charter/page/N/`. 403 — real browser UA. **Medium.** *(Primary listing §3.2 #4.)*
9. **[Annumer.fr — Location bateau (annuaire nautique)](https://www.annumer.fr/annuaire/location-bateau-moteur)** — France (Med + Atlantic) — ~17/category page — website (direct external URL); occasional phone on detail — scrape category page for external URLs; crawl `/site/<slug>-<id>` detail + sibling sailboat category `location.annumer.fr/location-bateau,27.html`. **Easy. Submission venue** (add-listing flow).
10. **[L'Oeil du Bassin — Location de bateau (Bassin d'Arcachon)](https://www.loeildubassin.com/annuaire/location-de-bateau/)** — France (Arcachon, La Teste-de-Buch, Gujan-Mestras) — ~4 — **EMAIL + website + phone — all inline** — one GET, parse fully-enriched listings; no pagination, no outbound follow. **Easy. Best contact-completeness of any source (email inline)** — only tiny volume drops its rank. Model for hyper-local French annuaires.

## 4. Scrape These 5 First (This Week)

The highest-yield, easiest, email/website-exposing sources to point the scraper at now — prioritized for home-market relevance and inline contact data:

1. **[TopBarcos](https://www.topbarcos.com/directorio-empresas-nauticas/embarcaciones/alquiler-charter)** — **Do this first.** The home Málaga/Marbella/Cádiz/Baleares market, hundreds of operators, server-rendered (no JS), inline phone + outbound website. Two-step buscador → ficha. Easy. Filter `?provincia=malaga` first for immediate local leads.
2. **[CYBA](https://www.cyba.net/member-directory/)** — Single page, ~200–330 members with **inline email + website + phone**. Only work is decoding Cloudflare `data-cfemail` (XOR the hex bytes against the first byte). Best signal-to-noise B2B source anywhere in this playbook.
3. **[AYCA](https://ayca.net/membership/our-members/)** — Single page, ~80 members, **inline email + website + phone + address** (same de-obfuscation trick). Fast complement to CYBA for the US market.
4. **[DMA Yachting — Greek list](https://mygreekcharter.com/list-of-greek-yacht-charter-companies/)** + sister **[mycroatiancharter](https://mycroatiancharter.com/list-of-croatia-yacht-charter-providers/)** — Two single-GET, clean tables (~80 + ~12), inline phone + outbound website. Same scrape template covers both; follow outbound links for email.
5. **[CharterWorld lists 1/2/3](https://www.charterworld.com/index.html?sub=broker-company-list1)** — Three static pages, ~300+ brokers, regex-parse comma-delimited name + address + phone. Largest single bulk dump for minimal effort; phone-first (web-search enrich for email).

**Execution note:** #1–#3 and the two #4 lists are all single-page or near-single-page fetches that yield inline phone/website (and inline email for CYBA/AYCA) — realistically a one-day scraper build. For the website-only sources among them, queue the standard second pass: crawl each operator's own `/contact` (or `/contacto`) page for email. Hold booking-gated platforms (Yumping, FishingBooker) out of this first wave — they need external enrichment and return name+geo only.