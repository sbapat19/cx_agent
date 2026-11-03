# Source access log

Tested 2026-11-02 from the build session. Tools: WebFetch (restricted by an allowlist) and WebSearch. I did not try to bypass any block, bot protection, or allowlist.

Official US beauty domain found via search: `giorgioarmanibeauty-usa.com`. A separate fashion site, `armani.com/en-us`, has its own return policy. It is **not** the beauty site policy and must not be used for Armani Beauty answers.

| Page | Result | Detail |
|---|---|---|
| giorgioarmanibeauty-usa.com (homepage) | Not fetched | Direct fetch refused (URL not on session allowlist). Hosts reached only through search results. |
| `/customer-service/shipping-returns/customer-service-shipping-and-returns.html` | **Partial / stale** | Fetched, but content is an old COVID-era shipping notice. Contains no return window, refund method, exchange, or damaged-item rules. Cannot be used as a policy source. |
| `/customer-service/shipping-and-delivery.html` | **Blocked** | Fetch failed (client_error), nothing retrieved. A search snippet quotes it (30-day returns, pre-paid label, "cannot accept exchanges at this time", 30-minute cancellation window, phone 1.877.276.2643). **A search snippet is not a verified read.** Status: `unverified`. |
| Foundation product page (Luminous Silk) | **Not reached** | Search returned only third-party retailers, not the official product page. |
| Concealer, blush, fragrance product pages | **Not tested yet** | Same limitation expected. |
| Counter / retailer locator | **Not tested yet** | |

## Conflicts and risks found
- The snippet and a third-party coupon site both say 30-day returns and no exchanges. The fetched official page says nothing of the sort. Nothing here is stored as policy until a page is read directly.
- Luminous Silk was reformulated. A UK retailer page describes 44 shades, 18 of them new, and a chart of "if you wore shade X, your new match is Y". That is third-party text for the UK. The US shade list may differ. This matters for foundation matching and must come from the US official page.
- Third-party sources were NOT used to fill any field.

## Options (need your decision)
1. **You paste page text** (or save pages as PDF/txt) for the returns/shipping policy and the 10-15 products and 3-5 fragrances. Most reliable. I would verify and store each with URL and date you captured it.
2. **You approve a different official source**, e.g. add specific `giorgioarmanibeauty-usa.com` URLs to my fetch allowlist, if your setup allows it.
3. **Run the data step on your machine** in Claude Code, where the browser can open the pages.
4. **Smaller verified set** if some pages stay unreachable. The spec's rule applies: blank fields, no gaps filled from memory.
