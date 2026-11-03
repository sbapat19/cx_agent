# Data verification (supersedes the "blocked" status in source_access.md)

Captured 2026-11-02 from the official US site `giorgioarmanibeauty-usa.com`. Stored as structured summaries with source URL and date in `backend/app/catalog_data.py`.

## Two capture routes
1. **Read directly** in the built-in browser as a normal visitor (a Cloudflare verification page appeared once and was not interacted with; later requests loaded). Pages: shipping & returns policy (read from the page's DOM; its sections are collapsed), the foundation category, Luminous Silk foundation (44 shades, sizes, full ingredients), concealer, Dolci blush, Skin Tint, fragrances Sì EDP, My Way EDP, Acqua di Giò EDT, Armani Code EDT, and the gift-set listings (name/price/description).
2. **Pasted by the project owner** (`9ac7dc25-attachment.txt`, produced with another tool on the same date): 25 page captures incl. primer, Cheek Tint, Glow Blush, setting powder, Fluid Sheer, Acqua Highlighter, bronzers, Power Fabric+ foundation and concealer, 5 more fragrances, 5 gift-set pages with contents, a gift-set listing, and a New York store-locator list.

Cross-check: fields present in both routes (foundation shades and ingredients, concealer, Dolci, My Way, Sì, Acqua di Giò EDT, Armani Code, gift-set prices) matched. Pasted-only fields were **not** independently re-read.

## Known gaps and flags (kept visible in the data)
- Not stored: bronzers (the paste says their text is from older crawls, Aug 2026), Neo Nude items (discontinued / last chance), Skin Tint (direct read only; not loaded into the DB), Power Fabric+ concealer shades, Power Fabric+ foundation price.
- Several fragrances list sizes but only some per-size prices (Acqua di Giò Parfum, Stronger With You EDT, Stronger With You Intensely, Armani Code 30/50 mL).
- Gift-set listing page returned a server error for the pasting tool; its prices come from the crawl text. Contents are known for 5 sets only.
- The store locator is interactive; only a New York list was captured and warehouse entries were dropped.
- Policy page ambiguities are stored as written (see README).
- Prices, promotions and stock change; every record carries a capture date.

## Not allowed / not done
No bot protection was bypassed, no third-party site was used to fill a gap, and no field was filled from memory.
