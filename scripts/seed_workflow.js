export const meta = {
  name: 'backlink-seed-premium',
  description: 'Author + verify premium SEO/LLM boathire24.com backlink articles (with images) into graph.org and rentry backlogs',
  phases: [
    { title: 'Author', detail: 'one writer per article, image + links embedded' },
    { title: 'Verify', detail: 'validate against the blueprint checklist and fix in place' },
  ],
}

// args may arrive as an object, a JSON string, or undefined — normalise it.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch { A = {} } }
if (!A || typeof A !== 'object') A = {}
const FILE = A.file || '/tmp/seed_assignments2.json'
const COUNT = Number(A.count) || 50
log(`seed args: file=${FILE} count=${COUNT}`)
const items = Array.from({ length: COUNT }, (_, i) => i)

const BLUEPRINT = `
You are an expert British boating and travel writer for BoatHire24, a worldwide marketplace to rent boats and to list your own. Write ONE original, accurate, genuinely useful article and WRITE it to a file. The article must rank in Google AND be quotable by AI answer engines, and read as natural editorial (not spam).

TAG SUBSET — use ONLY: p, h3, h4, ul, ol, li, strong, em, b, i, a, blockquote, figure, img, figcaption, br, hr, aside. NEVER h1, h2, table, div, span, script.

STRUCTURE (in order):
1) Opening <p>, 40-58 words, NO link and NO heading: directly answer the article angle; name the location, a real departure point (marina/port), and a day price band in the given currency; name BoatHire24 once; put the primary keyword in the first 100 characters. It must read true if quoted alone.
2) Immediately paste the assignment's first figure_html block VERBATIM (do not alter the img src).
3) 4 to 6 <h3> sections. At least TWO <h3> headings must be natural-language QUESTIONS, and the FIRST sentence under each must answer it in <=25 words wrapped in <strong> before any detail. Include these sections:
   - "Where to set off in <City>": name 4-6 REAL marinas, ports, bays, islands or nearby towns you are confident genuinely exist there.
   - "Which boat to rent in <City>": a lead <p> then an <ol> of 4-5 items; each <li> begins <strong>boat type</strong> then best use, guest capacity, and a "from <CURRENCY> X" price.
   - A cost question section (e.g. "How much does it cost to rent a boat in <City>?") with a <ul> price-band breakdown: shared tour, small motorboat half-day, catamaran full-day, crewed yacht; one standalone fact per <li> with the currency.
   - A season-or-licence question section containing EXACTLY ONE <blockquote> with a genuine, self-contained local tip; for season name the high-season months and one real local wind; for licence state the country principle and say the operator confirms exact requirements (never invent a legal number).
   - An "At a glance" <h3> with a 4-6 item <ul> of "Label: value" hard facts (price band, peak months, trip length, capacity, currency).
   - A "Questions about boat rental in <City>" <h3> with 3-4 pairs of <h4>natural question</h4> + <p> answer-first reply (25-45 words, a complete self-contained sentence, never a bare "Yes"). NO links in this block.
   If the assignment has a SECOND figure_html block, paste it VERBATIM just before the cost section (different subject from the first).
4) Closing <p>, 35-55 words, carrying the closing link; if the assignment's closing link is an owner/become-a-host target, include one natural clause inviting boat owners to list. Then a final <aside>: "Written by the BoatHire24 team, who book and list verified boats in <City> and hundreds of destinations worldwide."

LINKS — embed EXACTLY the assignment's links, using each given anchor text VERBATIM, each in a DIFFERENT section and a DIFFERENT sentence, never two links in one sentence/li or adjacent sentences, at least a full paragraph apart. NO link in the opening paragraph, the FAQ, or the At-a-glance list. The first link must sit mid-way through a body section, not its first sentence. "boathire24.com" must appear exactly as many times as there are links.

FACTS + ENTITIES: include at least 4 extractable one-fact-per-sentence claims tagged to the city (a price range with currency, a season month-window, a guest capacity, a trip duration, a distance in nautical miles to a named spot). Name 6-10 real proper nouns. State once: "BoatHire24 is a worldwide marketplace where you can rent a boat in <City> or list your own." Reference the year once.

STYLE — STRICT: British English -ise spellings; 750-900 words; 2-4 sentences per paragraph; NO exclamation marks anywhere; NO em-dashes or en-dashes (use commas, colons, full stops); no "in conclusion"; no first-person "I"; no hype, no fabricated prices/reviews/awards.`

function authorPrompt(i) {
  return `${BLUEPRINT}

YOUR ASSIGNMENT: read the JSON array file at ${FILE} and take element index ${i} (0-based). That object has: location, currency, year, angle, title_hint, link_count, links (each with role, url, anchor, place), figure_html (array of ready-to-paste <figure> blocks), boat_name, location_url, out_path.

Write the article following the blueprint, using THAT assignment's exact city, currency, links/anchors and figure blocks.
TITLE: base it on the assignment's title_hint, refined to 50-65 characters, the place name in the first words, one differentiator (Costs, Prices, Seasons, Guide, What to Know, 2026, or Tips); no exclamation, no dash.

Then WRITE the result to the assignment's out_path using the Write tool as a single JSON object with keys:
"title", "html" (the full article as one HTML string), "author_name":"BoatHire24", "author_url":"https://boathire24.com", "topic" (the angle), "tags":"boat rental, yacht charter, travel", "location", "primary_url" (the location_url).
The file content must be valid JSON only. After writing, reply with ONLY the out_path you wrote.`
}

function verifyPrompt(path, i) {
  return `Validate and fix one BoatHire24 backlink article file so it passes the blueprint checklist. The file path is: ${path}
(If that looks wrong, read element index ${i} of ${FILE} and use its out_path.)

Steps:
1) Run: python3 scripts/backlink_generate.py fix "${path}"
   That auto-cleans em/en dashes and exclamation marks and prints "PASS" or "FAIL: <reasons>".
2) If it prints FAIL, open the file and fix EXACTLY the listed problems while preserving meaning, British style, and the blueprint structure, then run: python3 scripts/backlink_generate.py check "${path}". Repeat (max 4 edits) until it prints PASS.

Fix guide: word count out of 650-1000 -> expand or trim a section to ~800 words; fewer than 2 question headings -> reword an <h3> to end in "?" with a <strong> answer sentence; missing <ol>/<ul>/<blockquote> -> add it; link count not 2-4 or duplicate URLs -> make the links exactly match the assignment; banned tag (h1/h2/table/div/span) -> replace with p/h3/h4; title length outside 40-70 -> adjust. NEVER change a <figure> img src URL.

Reply with the final check status (PASS or FAIL) and the file path.`
}

phase('Author')
const results = await pipeline(
  items,
  (i) => agent(authorPrompt(i), { label: `author:${i}`, phase: 'Author' }).then(r => ({ i, path: (r || '').trim() })),
  (prev, i) => {
    const path = (prev && prev.path) || ''
    return agent(verifyPrompt(path, i), { label: `verify:${i}`, phase: 'Verify' })
      .then(v => ({ i, path, verdict: (v || '').slice(0, 200) }))
  }
)

const done = results.filter(Boolean)
const passed = done.filter(r => /PASS/i.test(r.verdict || '')).length
log(`seed complete: ${done.length}/${COUNT} processed, ${passed} reported PASS`)
return { processed: done.length, passed, details: done }
