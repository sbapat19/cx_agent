"""Verified Armani Beauty catalog data (US site), captured 2026-11-02.

Every record carries source_url and last_verified. A value of None means the page did not show it;
nothing here is filled from memory or third-party sites. status: 'verified' or 'partial'.
Brand claims are stored as claims, not as facts.

INDEPENDENT PROJECT: not affiliated with Armani Beauty, L'Oreal, or Sierra.
"""

BASE = "https://www.giorgioarmanibeauty-usa.com"
VERIFIED = "2026-11-02"


def _fnd_shades():
    raw = """1|Fair|Cool Peach
2|Fair|Neutral Golden
3|Fair|Warm Golden
3.5|Light|Neutral Peach
3.75|Fair|Cool Pink
3.8|Light|Warm Peach
4|Light|Neutral Golden
4.1|Light|Warm Golden
4.5|Light|Neutral Peach
5|Light|Neutral Pink
5.1|Light|Cool Pink
5.15|Light Medium|Neutral Golden
5.2|Light Medium|Warm Peach
5.25|Light Medium|Cool Pink
5.3|Light Medium|Neutral Olive
5.5|Light Medium|Cool Peach
5.75|Light Medium|Neutral Golden
5.8|Medium|Warm Golden
5.9|Medium|Neutral Pink
5.95|Medium|Neutral Peach
6|Medium|Neutral Olive
6.25|Medium|Warm Peach
6.5|Medium|Neutral Golden
6.8|Medium Tan|Warm Golden
7|Medium Tan|Cool Peach
7.6|Medium Tan|Neutral Golden
7.8|Medium Tan|Warm Olive
8.1|Medium Tan|Warm Golden
8.25|Tan|Cool Pink
8.6|Tan|Neutral Golden
9|Tan|Neutral Olive
9.1|Tan|Warm Peach
10.1|Tan|Warm Golden
11|Deep|Neutral Olive
11.4|Deep|Warm Golden
11.75|Deep|Neutral Pink
11.8|Deep|Warm Peach
12.1|Deep|Cool Pink
13.25|Deep|Neutral Golden
13.6|Very Deep|Neutral Olive
13.8|Very Deep|Warm Olive
14|Very Deep|Warm Golden
15.5|Very Deep|Cool Red
15.8|Very Deep|Neutral"""
    out = []
    for line in raw.splitlines():
        code, depth, undertone = line.split("|")
        out.append({"code": code, "label": f"{code} - {depth}, {undertone}", "depth": depth, "undertone": undertone})
    return out


def _labels(codes_labels):
    return [{"code": c, "label": l, "depth": None, "undertone": None} for c, l in codes_labels]


CONCEALER_SHADES = _labels([
    ("1.5", "1.5 FAIR NEUTRAL"), ("2", "2 VERY FAIR NEUTRAL"), ("3", "3 VERY FAIR, GOLDEN"),
    ("3.75", "3.75 VERY FAIR, PINK"), ("4", "4 LIGHT, GOLDEN"), ("4.5", "4.5 LIGHT TO MEDIUM, NEUTRAL"),
    ("4.75", "4.75 LIGHT, PINK"), ("5", "5 LIGHT, NEUTRAL"), ("5.25", "5.25 MEDIUM, PINK"),
    ("5.5", "5.5 MEDIUM, PEACH"), ("5.75", "5.75 LIGHT TO MEDIUM, GOLDEN"), ("6", "6 MEDIUM, OLIVE"),
    ("6.5", "6.5 MEDIUM TO TAN, NEUTRAL"), ("7", "7 MEDIUM TO TAN, PEACH"), ("7.5", "7.5 TAN, PEACH"),
    ("8", "8 TAN, NEUTRAL"), ("8.75", "8.75 TAN TO DEEP, GOLDEN"), ("10", "10 DEEP, GOLDEN"),
    ("11.75", "11.75 DEEP, PINK"), ("14", "14 VERY DEEP, OLIVE"), ("15", "15 VERY DEEP, NEUTRAL"),
    ("3.9", "3.9 LIGHT, COOL PEACH"), ("5.4", "5.4 MEDIUM, COOL PEACH"), ("11", "11 DEEP, NEUTRAL OLIVE"),
    ("11.5", "11.5 DEEP, GOLDEN PEACH"),
])

POWDER_SHADES = _labels([
    ("2", "2 - Fair With a Peach Undertone"), ("3", "3 - Very Fair With a Golden Undertone"),
    ("4", "4 - Light To Medium With a Golden Undertone"), ("5.5", "5.5 - Medium With a Peach Undertone"),
    ("6.5", "6.5 - Medium To Tan With a Natural Undertone"), ("7", "7 - Medium To Tan With a Peach Undertone"),
    ("8", "8 - Tan With a Neutral Undertone"), ("9", "9 - Tan To Deep With a Pink Undertone"),
    ("11.5", "11.5 - Deep With a Peach Undertone"), ("14", "14 - Very Deep With a Golden Undertone"),
])

PRODUCTS = [
    {
        "id": "ww-01019-arm", "name": "Luminous Silk Natural Glow Blurring Foundation", "category": "foundation",
        "collection": "Luminous Silk", "url": f"{BASE}/makeup/face/foundation/luminous-silk-natural-glow-blurring-foundation/ww-01019-arm.html",
        "description": "A silky, lightweight foundation with medium buildable coverage and a natural glow finish.",
        "coverage": "medium, buildable", "finish": "natural glow", "texture": "silky, lightweight",
        "claims": ["non-comedogenic (brand claim)", "enriched with niacinamide (brand claim)",
                   "clinically proven to even skin tone, refine texture and boost luminosity after 14 days (brand claim)",
                   "transfer resistant after dry down, shade stays true-to-skin (brand claim)",
                   "dermatologist tested for all skin types incl. sensitive and acne-prone (brand claim)",
                   "24-hour wear claim: consumer test on 106 volunteers; 24-hour hydration claim: instrumental test on 24 volunteers"],
        "application": "For an airbrushed finish apply at center of face and blend outward with a foundation brush. For a dewy finish apply with a damp sponge. Apply in layers. The page suggests Luminous Silk Glow Setting Powder and Luminous Silk Hydrating & Brightening Concealer to complete the routine.",
        "ingredients": "AQUA / WATER / EAU, DIMETHICONE, C15-19 ALKANE, ISODODECANE, GLYCERIN, SORBITOL, ALCOHOL DENAT., CETYL PEG/PPG-10/1 DIMETHICONE, POLYGLYCERYL-4 ISOSTEARATE, ALUMINUM STARCH OCTENYLSUCCINATE, SYNTHETIC FLUORPHLOGOPITE, DISTEARDIMONIUM HECTORITE, PHENOXYETHANOL, MAGNESIUM SULFATE, CELLULOSE GUM, DIMETHICONOL, SILICA SILYLATE, DISODIUM STEAROYL GLUTAMATE, CAPRYLYL GLYCOL, PROPYLENE CARBONATE, PARFUM / FRAGRANCE, PEG/PPG-18/18 DIMETHICONE, TRIHYDROXYSTEARIN, NIACINAMIDE, ALUMINUM HYDROXIDE, HYDROLYZED LUPINE PROTEIN, ACETYLATED GLYCOL STEARATE, SILICA, BENZYL SALICYLATE, HEXYL CINNAMAL, KAOLIN, BENZYL ALCOHOL, PANCRATIUM MARITIMUM EXTRACT, LIMONENE, SODIUM BENZOATE, LINALOOL, PENTAERYTHRITYL TETRA-DI-T-BUTYL HYDROXYHYDROCINNAMATE, TOCOPHEROL",
        "sizes_prices": [{"size": "1.0 oz / 30 mL", "usd": 69.00}, {"size": "0.6 oz / 18 mL", "usd": 48.00}],
        "shades": _fnd_shades(), "shade_note": "44 shades; 18 are new in this enhanced formula (page text), including olive tones. Use these shade numbers only.",
        "status": "verified",
    },
    {
        "id": "A2266", "name": "Luminous Silk Hydrating & Brightening Concealer", "category": "concealer", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/concealer/luminous-silk-hydrating-brightening-concealer/A2266.html",
        "description": "Buildable coverage with a skin-like, naturally radiant finish; precise tip applicator.",
        "coverage": "medium to buildable", "finish": "naturally radiant, skin-like", "texture": "lightweight, hydrating",
        "claims": ["formulated with glycerin, caffeine and vitamin E to visibly hydrate and reduce under-eye puffiness (brand claim)"],
        "application": "Start with Luminous Silk Foundation or bare skin; use the tip to target areas or the flat side for larger areas; layer for coverage; set with Luminous Silk Glow Setting Powder.",
        "ingredients": "AQUA / WATER, COCO-CAPRYLATE/CAPRATE, HYDROGENATED POLYISOBUTENE, SORBITAN ISOSTEARATE, GLYCERIN, PROPANEDIOL, PROPYLENE GLYCOL, SYNTHETIC FLUORPHLOGOPITE, ALUMINA, PHENOXYETHANOL, MAGNESIUM SULFATE, DISODIUM STEAROYL GLUTAMATE, PARAFFIN, HYDROXYACETOPHENONE, DISTEARDIMONIUM HECTORITE, CERA MICROCRISTALLINA / MICROCRYSTALLINE WAX, CAPRYLYL GLYCOL, SILICA SILYLATE, SYNTHETIC WAX, CAFFEINE, TRISODIUM ETHYLENEDIAMINE DISUCCINATE, ALUMINUM HYDROXIDE, TOCOPHEROL, TIN OXIDE, HELIANTHUS ANNUUS SEED OIL / SUNFLOWER SEED OIL, [+/- MAY CONTAIN CI 77891 / TITANIUM DIOXIDE, CI 77491, CI 77492, CI 77499 / IRON OXIDES]",
        "sizes_prices": [{"size": None, "usd": 42.00}], "shades": CONCEALER_SHADES, "shade_note": "25 shades; undertone is embedded in each label.",
        "status": "verified",
    },
    {
        "id": "ww-01020-arm", "name": "Luminous Silk Hydrating Glow Extending Primer", "category": "primer", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/face-primer/luminous-silk-hydrating-glow-extending-primer/ww-01020-arm.html",
        "description": "An ultra-smooth, hydrating water-based gel primer with a fresh-dewy finish.",
        "coverage": None, "finish": "fresh, dewy", "texture": "water-based gel",
        "claims": ["formulated with hyaluronic acid and LHA skincare actives (brand claim)", "pairs with Luminous Silk Foundation (page text)"],
        "application": "Apply evenly to clean, moisturized skin before foundation. Can be worn alone or mixed with skincare or makeup.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 48.00}], "shades": [], "shade_note": "Not a shaded product.",
        "status": "partial",
    },
    {
        "id": "ww-01060-arm", "name": "Dolci Blush", "category": "blush", "collection": "Dolci",
        "url": f"{BASE}/makeup/face/blush-bronzer/dolci-blush/ww-01060-arm.html",
        "description": "Hybrid cream-to-powder blush with a soft-matte finish; can be used on cheeks and lips.",
        "coverage": None, "finish": "soft-matte", "texture": "smoothing cream-to-powder",
        "claims": ["buildable, non-cakey colour (brand claim)", "multi-use: cheek and lip application (page text)"],
        "application": "Warm up with fingers or the back of the hand; apply with a fluffy semi-dense brush using tapping motions; buildable and can be layered over or under makeup.",
        "ingredients": "ISOTRIDECYL ISONONANOATE, SILICA, C12-15 ALKYL BENZOATE, CAPRYLIC/CAPRIC TRIGLYCERIDE, DIISOSTEARYL MALATE, SYNTHETIC WAX, ALUMINUM STARCH OCTENYLSUCCINATE, CI 77891 / TITANIUM DIOXIDE, C13-15 ALKANE, TRIETHYLHEXANOIN, ISONONYL ISONONANOATE, DICALCIUM PHOSPHATE, DIMETHICONE/VINYL DIMETHICONE CROSSPOLYMER, CANDELILLA CERA / CANDELILLA WAX, AMYLOPECTIN, POLYGLYCERYL-2 TRIISOSTEARATE, OCTYLDODECYL STEAROYL STEARATE, CI 15850 / RED 6, POLYETHYLENE, PARFUM / FRAGRANCE, ALUMINA, TOCOPHERYL ACETATE, CI 45410 / RED 28 LAKE, CI 15850 / RED 7 LAKE, POLYGLYCERYL-2 DIISOSTEARATE, COLOPHONIUM / ROSIN / COLOPHANE",
        "sizes_prices": [{"size": None, "usd": 39.00}],
        "shades": _labels([("1", "1 - Rose Blush"), ("2", "2 - Caramel Blush"), ("3", "3 - Apricot Blush"), ("4", "4 - Cinnamon Blush"), ("5", "5 - Mauve Blush")]),
        "shade_note": "Five shades. Shade descriptions beyond names are only given for Cinnamon (bold rich brown with subtle red hints) and Mauve (refined mauve).",
        "status": "verified",
    },
    {
        "id": "3614274380026", "name": "Luminous Silk Cheek Tint Blush", "category": "blush", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/blush-bronzer/luminous-silk-cheek-tint-blush/3614274380026.html",
        "description": "Up to 12h skin-fusing liquid blush for just-pinched cheeks.",
        "coverage": "light", "finish": "natural or radiant", "texture": "liquid",
        "claims": ["lasts up to 12 hours (brand claim)", "made with Micro-fil technology (brand claim)", "can also be applied to lips (page text)"],
        "application": "One dot on the apples of the cheeks blended with fingertips or brush for a natural flush; two dots on high points for a sun-kissed look.",
        "ingredients": "AQUA / WATER / EAU, DIMETHICONE, ISODODECANE, BUTYLENE GLYCOL, ALCOHOL DENAT., ACRYLATES/POLYTRIMETHYLSILOXYMETHACRYLATE COPOLYMER, CETYL PEG/PPG-10/1 DIMETHICONE, TRIMETHYL PENTAPHENYL TRISILOXANE, DISTEARDIMONIUM HECTORITE, POLYGLYCERYL-4 ISOSTEARATE, MAGNESIUM SULFATE, PHENOXYETHANOL, SYNTHETIC FLUORPHLOGOPITE, PROPYLENE CARBONATE, PEG/PPG-18/18 DIMETHICONE, LAUROYL LYSINE, DISODIUM STEAROYL GLUTAMATE, ALUMINUM HYDROXIDE, PENTAERYTHRITYL TETRA-DI-T-BUTYL HYDROXYHYDROCINNAMATE, TOCOPHEROL [+/- MAY CONTAIN: MICA, CI 77891, CI 77491, CI 77492, CI 77499, CI 15850 / RED 7, CI 15985 / YELLOW 6 LAKE]",
        "sizes_prices": [{"size": None, "usd": 40.00}],
        "shades": _labels([("31", "31 - Vivid Coral (Natural)"), ("41", "41 - Flaming Red (Natural)"), ("42S", "42S - Sunlit Sienna (Radiant)"),
                           ("50S", "50S - Starlit Peach (Radiant)"), ("50.5", "50.5 - Rosy Peach (Natural)"), ("53", "53 - Bold Pink (Natural)"),
                           ("53S", "53S - Cosmic Pink (Radiant)"), ("62", "62 - Delicate Mauve (Natural)"), ("62S", "62S - Magnetic Mauve (Radiant)"),
                           ("65", "65 - Intense Berry (Natural)"), ("43S", "43S - Berry Red (Radiant)"), ("12", "12 - Rosy Nude (Natural)"),
                           ("13", "13 - Brick Brown (Natural)"), ("54", "54 - Orchid Fuchsia (Natural)"), ("63", "63 - Rosewood Pink (Natural)")]),
        "shade_note": "15 shades. One variation showed as out of stock on the listing page on 2026-11-02; stock changes, do not promise availability.",
        "status": "verified",
    },
    {
        "id": "A2594", "name": "Luminous Silk Glow Blush", "category": "blush", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/blush-bronzer/luminous-silk-glow-blush/A2594.html",
        "description": "Silky powder blush for natural colour and a subtle glow.",
        "coverage": None, "finish": "radiant", "texture": "pressed powder",
        "claims": ["ultra-finely milled with light-reflecting pigments (brand claim)", "buildable and blendable (brand claim)"],
        "application": "Swirl a blush brush in the pan, tap off excess and apply in sweeping or circular motions; a light dusting on high points gives an all-over sun-kissed look.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 40.00}],
        "shades": _labels([("11", "11 - IN LOVE"), ("30", "30 - OFFBEAT"), ("40", "40 - MANIA"), ("50", "50 - EUPHORIC"), ("51", "51 - AMORE"),
                           ("52", "52 - ECSTASY"), ("60", "60 - MYSTERY"), ("61", "61 - DESIRE")]),
        "shade_note": "8 shades (names only).", "status": "partial",
    },
    {
        "id": "A2344", "name": "Luminous Silk Glow Setting Powder", "category": "setting powder", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/foundation/luminous-silk-glow-setting-powder/A2344.html",
        "description": "A long-wearing setting powder that gives skin a radiant finish.",
        "coverage": "sheer veil", "finish": "radiant", "texture": "lightweight powder",
        "claims": ["translucent formula that becomes a skin-matching veil (brand claim)", "does not cake or settle into fine lines (brand claim)"],
        "application": "Apply with a sponge, powder brush or the included applicator over foundation, or wear alone as a translucent powder.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 69.00}], "shades": POWDER_SHADES, "shade_note": "10 shades.",
        "status": "partial",
    },
    {
        "id": "A2340", "name": "Fluid Sheer Glow Enhancer", "category": "highlighter", "collection": "Fluid Sheer",
        "url": f"{BASE}/makeup/face/highlighter/fluid-sheer-glow-enhancer/A2340.html",
        "description": "Multi-purpose liquid highlighter, bronzer and blush.",
        "coverage": "light", "finish": "radiant", "texture": "liquid",
        "claims": ["can be mixed with foundation for a radiance boost (page text)"],
        "application": "Wear alone or under foundation as a thin layer, or on top as highlighter, blush or bronzer. Page: shade 2 for light to medium skin, shade 10 for tan to deep skin.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 43.00}],
        "shades": _labels([("2", "2 - Champagne"), ("5", "5 - Coral"), ("7", "7 - Light Pink"), ("8", "8 - Pink"), ("10", "10 - Bronze"), ("11", "11 - Peach")]),
        "shade_note": "Some shades showed out of stock on 2026-11-02.", "status": "partial",
    },
    {
        "id": "ww-00892-arm", "name": "Luminous Silk Acqua Highlighter", "category": "highlighter", "collection": "Luminous Silk",
        "url": f"{BASE}/makeup/face/highlighter/luminous-silk-acqua-highlighter/ww-00892-arm.html",
        "description": "Lightweight liquid light for a blendable pearly glow.",
        "coverage": None, "finish": "pearly glow", "texture": "watery, creamy liquid",
        "claims": ["buildable (brand claim)"],
        "application": "Apply 1-2 dots on each cheekbone with the applicator and blend with fingertips; build for more shimmer.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 39.00}],
        "shades": _labels([("Halo", "Halo"), ("Stellar", "Stellar"), ("Dawn", "Dawn"), ("Sunrise", "Sunrise"), ("Sunset", "Sunset")]),
        "shade_note": "5 shades (names only).", "status": "partial",
    },
    {
        "id": "A2597", "name": "Power Fabric+ Multi-Retouch Concealer", "category": "concealer", "collection": "Power Fabric+",
        "url": f"{BASE}/makeup/face/concealer/power-fabric--multi-retouch-concealer/A2597.html",
        "description": "High-coverage longwear matte concealer with a multi-use applicator.",
        "coverage": "high", "finish": "natural matte", "texture": "liquid",
        "claims": ["high coverage up to 24 hours (consumer test on 105 women; brand claim)", "resists creasing (brand claim)"],
        "application": "Use the pointed tip for targeted retouching and the flat surface for larger areas.",
        "ingredients": None, "sizes_prices": [{"size": None, "usd": 44.00}], "shades": [],
        "shade_note": "Shade list was not on the captured page; do not state shades.", "status": "partial",
    },
    {
        "id": "3614273580106", "name": "Power Fabric+ Foundation", "category": "foundation", "collection": "Power Fabric+",
        "url": f"{BASE}/power-fabric-foundation/3614273580106.html",
        "description": "24-hour longwear foundation with a soft matte finish; medium to full coverage; formulated with SPF 25.",
        "coverage": "medium to full, buildable", "finish": "natural matte", "texture": "liquid-to-powder",
        "claims": ["transfer-, sweat-, heat- and water-resistant (brand claim)", "up to 24 hours of wear (brand claim)"],
        "application": "Apply with a foundation brush from the center of the face outward; dab with fingertips to blend.",
        "ingredients": None, "sizes_prices": [], "shades": _labels([
            ("2", "2 FAIR WITH OLIVE UNDERTONE"), ("2.5", "2.5 FAIR WITH PINK UNDERTONE"), ("2.75", "2.75 FAIR WITH PINK UNDERTONE"),
            ("3.25", "3.25 LIGHT WITH GOLDEN UNDERTONE"), ("3.5", "3.5 LIGHT WITH NEUTRAL UNDERTONE"), ("4.25", "4.25 LIGHT WITH PEACH UNDERTONE"),
            ("4.5", "4.5 LIGHT TO MEDIUM WITH OLIVE UNDERTONE"), ("5.25", "5.25 MEDIUM WITH PINK UNDERTONE"),
            ("5.75", "5.75 LIGHT TO MEDIUM WITH GOLDEN UNDERTONE"), ("6.5", "6.5 MEDIUM TO TAN WITH PEACH UNDERTONE"),
            ("7", "7 MEDIUM TO TAN WITH PEACH UNDERTONE"), ("8", "8 TAN WITH NEUTRAL UNDERTONE"),
            ("10", "10 DEEP WITH GOLDEN UNDERTONE"), ("15", "15 VERY DEEP WITH NEUTRAL UNDERTONE")]),
        "shade_note": "Shade list is 'from the site's variant list' as pasted (14 shades); price not captured.", "status": "partial",
    },
]

FRAGRANCES = [
    {
        "id": "A218", "name": "Sì Eau de Parfum", "concentration": "Eau de Parfum", "audience": "women's",
        "url": f"{BASE}/fragrances/womens-perfume/si/si-eau-de-parfum/A218.html",
        "family": "Fruity Floral", "scent_type": None,
        "published_notes": "Description: opens with blackcurrant nectar and mandarin; orange blossom forms the heart; warm vanilla anchors the blend. Key Notes line: Blackcurrant Nectar, Rose de Mai, White Musk, Freesia.",
        "notes_caveat": "The description names orange blossom as the heart while the Key Notes line lists Rose de Mai, White Musk and Freesia; the page does not reconcile them. Quote both as published.",
        "sizes_prices": [{"size": "0.34 oz / 10 mL", "usd": 37.00}, {"size": "1.0 oz / 30 mL", "usd": 105.00}, {"size": "1.6 oz / 50 mL", "usd": 145.00}, {"size": "3.4 oz / 100 mL", "usd": 180.00}],
        "status": "verified",
    },
    {
        "id": "A2104", "name": "Sì Passione Eau de Parfum", "concentration": "Eau de Parfum", "audience": "women's",
        "url": f"{BASE}/fragrances/womens-perfume/si/si-passione-eau-de-parfum/A2104.html",
        "family": "Floral", "scent_type": "Fruity Floral",
        "published_notes": "Description: opens with a burst of sparkling pear, a deep rose-petal heart and a smoldering woody-vanilla base. Key Notes line: Jasmine Absolute, Blackcurrant Nectar Accord, Cedarwood Essence.",
        "notes_caveat": "Description and Key Notes line differ; quote both as published.",
        "sizes_prices": [{"size": "0.34 oz / 10 mL", "usd": 37.00}, {"size": "1.0 oz / 30 mL", "usd": 105.00}, {"size": "1.6 oz / 50 mL", "usd": 145.00, "note": "out of stock on capture date"}, {"size": "3.4 oz / 100 mL", "usd": 180.00}, {"size": "5 oz / 150 mL", "usd": 195.00, "note": "out of stock on capture date"}],
        "status": "verified",
    },
    {
        "id": "A2259", "name": "My Way Eau de Parfum", "concentration": "Eau de Parfum", "audience": "women's",
        "url": f"{BASE}/fragrances/womens-perfume/my-way/my-way-eau-de-parfum/A2259.html",
        "family": "Floral Woody", "scent_type": "Bright and Radiant",
        "published_notes": "Description: bergamot meets Egyptian orange blossom in a sparkling start amplified by Indian tuberose and jasmine; at the base, white musk and Virginia cedarwood combine with Madagascar vanilla. Key Notes line: Bergamot, Tuberose, Jasmine, Vanilla, Cedarwood.",
        "notes_caveat": None,
        "sizes_prices": [{"size": "0.34 oz / 10 mL", "usd": 37.00}, {"size": "1.0 oz / 30 mL", "usd": 99.00}, {"size": "1.7 oz / 50 mL", "usd": 140.00}, {"size": "3.04 oz / 90 mL", "usd": 174.00}],
        "status": "verified",
    },
    {
        "id": "A378", "name": "Acqua di Gioia Eau de Parfum", "concentration": "Eau de Parfum", "audience": "women's",
        "url": f"{BASE}/fragrances/womens-perfume/acqua-di-gioia/acqua-di-gioia-eau-de-parfum/A378.html",
        "family": "Fresh", "scent_type": "Fresh Aquatics",
        "published_notes": "Description: opens with clean, fresh citrus, reveals a heart of jasmine and lingers with warm cedarwood. Key Notes line: Jasmine, Gardenia, Warm Woods.",
        "notes_caveat": None,
        "sizes_prices": [{"size": "0.34 oz / 10 mL", "usd": 36.00}, {"size": "1.0 oz / 30 mL", "usd": 85.00}, {"size": "1.7 oz / 50 mL", "usd": 120.00}, {"size": "3.4 oz / 100 mL", "usd": 148.00, "note": "out of stock on capture date"}],
        "status": "verified",
    },
    {
        "id": "A005", "name": "Acqua di Giò Eau de Toilette", "concentration": "Eau de Toilette", "audience": "men's",
        "url": f"{BASE}/fragrances/mens-cologne/acqua-di-gio/acqua-di-gio-eau-de-toilette/A005.html",
        "family": "Fresh", "scent_type": "Fresh Aquatics",
        "published_notes": "Description: opens with marine notes including Calabrian bergamot, neroli and green tangerine, blended with rosemary, persimmon and Indonesian patchouli. Key Notes line: Marine, Bergamot, Cedarwood.",
        "notes_caveat": "No top/heart/base pyramid is published; do not assign notes to layers beyond what the description says.",
        "sizes_prices": [{"size": "1.0 oz / 30 mL", "usd": 62.00}, {"size": "1.7 oz / 50 mL", "usd": 99.00}, {"size": "3.4 oz / 100 mL", "usd": 130.00}, {"size": "5 oz / 150 mL refill", "usd": 156.00}, {"size": "6.7 oz / 200 mL", "usd": 175.00}],
        "status": "verified",
    },
    {
        "id": "A2608", "name": "Acqua di Giò Parfum", "concentration": "Parfum", "audience": "men's",
        "url": f"{BASE}/fragrances/mens-cologne/acqua-di-gio/acqua-di-gio-parfum/A2608.html",
        "family": "Earthy & Woody", "scent_type": "Citrus & Woods",
        "published_notes": "Description: distinguished by bergamot, rosemary essence and incense notes. Key Notes line: Bergamot, Rosemary, Woods.",
        "notes_caveat": "No pyramid published.",
        "sizes_prices": [{"size": "listed price (default size not stated)", "usd": 186.00}],
        "price_note": "Sizes listed (30, 50, 75, 100, 200 mL) but per-size prices were not captured.", "status": "partial",
    },
    {
        "id": "A020", "name": "Armani Code Eau de Toilette", "concentration": "Eau de Toilette", "audience": "men's",
        "url": f"{BASE}/fragrances/mens-cologne/armani-code/armani-code-eau-de-toilette/A020.html",
        "family": "Earthy & Woody", "scent_type": "Citrus & Woods",
        "published_notes": "Top: bright citrus with green mandarin from Italy. Heart: lavandin. Base: warm tonka bean absolute and cedarwood. Key Notes line: Green Mandarin, Tonka Bean, Cedarwood.",
        "notes_caveat": None,
        "sizes_prices": [{"size": "2.5 oz / 75 mL", "usd": 120.00}, {"size": "4.3 oz / 125 mL", "usd": 139.00}, {"size": "6.7 oz / 200 mL", "usd": 190.00}],
        "price_note": "Sizes 30, 50 mL are also listed on the page but their prices were not captured.", "status": "partial",
    },
    {
        "id": "A2061", "name": "Stronger With You Eau de Toilette", "concentration": "Eau de Toilette", "audience": "men's",
        "url": f"{BASE}/fragrances/view-all-fragrances/stronger-with-you-eau-de-toilette/A2061.html",
        "family": "Warm & Spicy", "scent_type": "Warm & Sweet Gourmand",
        "published_notes": "Description: nutty, rich notes of chestnut and cardamom; spicy pink peppercorn accord in the top notes with cardamom, chestnut and violet leaves. Key Notes line: Pink Pepper Accord, Sage Essence, Candied Chestnut Accord.",
        "notes_caveat": "The page also shows a 'Find Your Fragrance' line (chestnut, lavender & tender sage, vanilla) that differs from the description; quote as published.",
        "sizes_prices": [{"size": "listed price (default size not stated)", "usd": 120.00}],
        "price_note": "Sizes 30, 50, 100, 150 mL listed; per-size prices not captured.", "status": "partial",
    },
    {
        "id": "ww-00180-arm", "name": "Stronger With You Intensely Eau de Parfum", "concentration": "Eau de Parfum", "audience": "men's",
        "url": f"{BASE}/fragrances/stronger-with-you-intensely-eau-de-parfum/ww-00180-arm.html",
        "family": "Warm & Spicy", "scent_type": "Woody Spices",
        "published_notes": "Top: spicy pink pepper essence with a chestnut accord. Heart: lavender and sage. Base: amber wood and vanilla essence. Key Notes line: Pink Pepper Essence, Lavender Essence, Vanilla Essence.",
        "notes_caveat": None,
        "sizes_prices": [{"size": "listed price (default size not stated)", "usd": 130.00}],
        "price_note": "Sizes 10, 50, 100, 150 mL listed; per-size prices not captured.", "status": "partial",
    },
]

GIFT_SETS = [
    # name, usd, category, description, includes (None = contents not captured), url
    ("Advent Calendar", 325, "any", "24-Piece Gift Set Featuring Our Bestsellers", None, f"{BASE}/fragrances/advent-calendar/ww-01100-arm.html"),
    ("Power Of You Eau De Parfum 3-Piece Holiday Gift Set", 145, "women's fragrance", "A fruity floral perfume for women", None, f"{BASE}/fragrances/womens-perfume/power-of-you/power-of-you-eau-de-parfum-3-piece-holiday-gift-set/ww-01067-arm.html"),
    ("Power Of You Eau De Parfum 2-Piece Holiday Gift Set", 85, "women's fragrance", "A fruity floral perfume for women", None, f"{BASE}/fragrances/womens-perfume/power-of-you/power-of-you-eau-de-parfum-2-piece-holiday-gift-set/ww-01065-arm.html"),
    ("My Way Eau de Parfum 3-Piece Holiday Gift Set", 178, "women's fragrance", "A citrus floral perfume for women", None, f"{BASE}/fragrances/womens-perfume/my-way/my-way-eau-de-parfum-3-piece-holiday-gift-set/ww-01071-arm.html"),
    ("My Way Eau de Parfum 2-Piece Holiday Gift Set", 100, "women's fragrance", "A citrus floral perfume for women (listing: 30 mL + 10 mL)", None, f"{BASE}/fragrances/womens-perfume/my-way/my-way-eau-de-parfum-2-piece-holiday-gift-set/ww-01070-arm.html"),
    ("Acqua di Gioia Eau de Parfum 2-Piece Holiday Gift Set", 95, "women's fragrance", "A zesty, vibrant, and fresh women's fragrance", None, f"{BASE}/fragrances/womens-perfume/acqua-di-gioia/acqua-di-gioia-eau-de-parfum-2-piece-holiday-gift-set/ww-01080-arm.html"),
    ("Acqua di Gioia Eau de Parfum 3-Piece Holiday Gift Set", 155, "women's fragrance", "Listed in the gift-set listing", None, None),
    ("Armani Women's Fragrance Sampler Gift Set", 50, "women's fragrance", "Listed in the gift-set listing", None, None),
    ("Stronger With You 3-Piece Discovery Holiday Gift Set", 65, "men's fragrance", "3-Piece Cologne Gift Set",
     ["Stronger With You Eau de Toilette 15 mL", "Stronger With You Intensely Eau de Parfum 15 mL", "Stronger With You Parfum 15 mL"],
     f"{BASE}/fragrances/stronger-with-you-3-piece-discovery-holiday-gift-set/ww-01087-arm.html"),
    ("Acqua di Giò 3-Piece Discovery Holiday Gift Set", 80, "men's fragrance", "3-Piece Cologne Gift Set", None, f"{BASE}/fragrances/mens-cologne/acqua-di-gio/acqua-di-gio-3-piece-discovery-holiday-gift-set/ww-01096-arm.html"),
    ("Acqua di Giò Eau de Toilette 2-Piece Holiday Gift Set", 100, "men's fragrance", "2-Piece Cologne Gift Set", None, f"{BASE}/fragrances/mens-cologne/acqua-di-gio/acqua-di-gio-eau-de-toilette-2-piece-holiday-gift-set/ww-01092-arm.html"),
    ("Acqua di Giò Eau de Toilette 3-Piece Holiday Gift Set", 138, "men's fragrance", "3-Piece Cologne Gift Set",
     ["Acqua di Giò Eau de Toilette 100 mL", "Acqua di Giò Eau de Toilette 15 mL", "Acqua di Giò Deodorant 75 mL"],
     f"{BASE}/fragrances/mens-cologne/acqua-di-gio/acqua-di-gio-eau-de-toilette-3-piece-holiday-gift-set/ww-01093-arm.html"),
    ("Stronger With You Intensely Eau de Parfum 2-Piece Holiday Gift Set", 108, "men's fragrance", "2-Piece Cologne Gift Set",
     ["Stronger With You Intensely Eau de Parfum 50 mL", "Stronger With You Intensely Eau de Parfum 15 mL"],
     f"{BASE}/fragrances/mens-cologne/stronger-with-you/stronger-with-you-intensely-eau-de-parfum-2-piece-holiday-gift-set/ww-01088-arm.html"),
    ("Armani Code Eau de Toilette 3-Piece Holiday Gift Set", None, "men's fragrance", "Price not captured",
     ["Armani Code Eau de Toilette 100 mL", "Armani Code Eau de Toilette 15 mL", "Armani Code Shower Gel 75 mL"],
     f"{BASE}/fragrances/mens-cologne/armani-code/armani-code-eau-de-toilette-3-piece-holiday-gift-set/ww-01098-arm.html"),
    ("I Will Eau de Parfum Holiday Gift Set", 125, "men's fragrance", "A long-lasting woody vanilla Eau de Parfum for men", None, f"{BASE}/fragrances/mens-cologne/i-will/i-will-eau-de-parfum-holiday-gift-set/ww-01062-arm.html"),
    ("Luminous Silk Cheek Tint Blush Holiday Gift Set", 55, "makeup", "2-Piece Makeup Set",
     ["Luminous Silk Cheek Tint Blush - 63 Rosewood Pink", "Luminous Silk Cheek Tint Blush - 13 Brick Brown"],
     f"{BASE}/makeup/luminous-silk-cheek-tint-blush-holiday-gift-set/A2815.html"),
    ("Eye Tint Liquid Eyeshadow & Vertigo Mascara Holiday Gift Set", 82, "makeup", "3-Piece Makeup Set", None,
     f"{BASE}/makeup/eye-tint-liquid-eyeshadow-vertigo-mascara-holiday-gift-set/ww-01101-arm.html"),
]

RETURNS_URL = f"{BASE}/customer-service/shipping-returns/customer-service-shipping-and-returns.html"

# Policy text is a faithful structured summary of the official page, read 2026-11-02. Each topic keeps
# ambiguity visible; the agent must state it as written and must not resolve it.
POLICIES = [
    ("returns_window", "Returns window",
     "Returns are accepted for any purchase made on giorgioarmanibeauty-usa.com within 30 days of the transaction. A pre-paid return label is generated when the return is started online. Items should be packed in original packaging if possible with the return packing slip."),
    ("refund", "Refund method and deduction",
     "Once the package is received the return takes 1-2 business days to complete and 3-5 business days to post to the account. The page says order credit 'along with an $8.00 deduction to the return process' is issued to the original payment method, and the customer is notified by email. A separate section says original shipping and handling charges are not refunded and that credit can take up to 7 business days to appear. The page does not say whether the $8.00 and the shipping charge are the same thing; state both as written without adding them together."),
    ("exchanges", "Exchanges",
     "The page states that exchanges cannot be accepted at this time."),
    ("return_exclusions", "Items not eligible for return",
     "Final sale items, engraved items, promotional gift items and e-gift cards are not eligible for return. Purchases from unauthorized retailers get no money-back guarantee or assistance. The page does not say whether holiday gift sets count as 'promotional gift items'; say that this is unclear and refer the customer to customer care."),
    ("damaged_missing_wrong", "Damaged, missing or wrong items",
     "If an order is missing a product, contains a damaged item or has any other concern, the customer should contact Armani Beauty customer care (live chat, phone 1.877.276.2643, or email) with the order confirmation number. The page does not state a photo requirement, a replacement guarantee, or a specific remedy for damaged or wrong items, so no automatic remedy is authorized by the policy text: open a support case for human review."),
    ("cancellation", "Cancelling or changing an order",
     "An order can be cancelled within 30 minutes of submission from the account's order history. After that the return process applies."),
    ("shipping", "Shipping",
     "Ground shipping is complimentary on orders of $75+ (the page says 'currently'). Charges: Ground $8.00, 2 Day $15.00, Next Day $20.00. Processing takes 1-4 days; ground generally takes 3-6 business days (guidance only, no guaranteed delivery dates). Orders are processed Monday to Friday; orders after 12:00 PM EST wait until the next business day. Express carrier does not deliver on weekends or to PO boxes. Alaska, Hawaii, USVI, APO/FPO and PO Box orders take 10-14 business days. Ships to the 50 US states and select territories, not Puerto Rico or internationally."),
    ("gifts", "Gifts and gift options",
     "The page says gift collections include unique gift boxing and complimentary product samples. It does not mention gift receipts, gift messages, or shipping to a different address, so those are not offered as available. Some fragrance pages show a 'Complimentary 2-Piece Fragrance Gift on $150+' line; its terms were not captured, so do not offer it as available."),
    ("contact", "Customer care contact",
     "Phone 1.877.276.2643 (1.877.ARMANI-3) or live chat or email. The page gives two different sets of hours, so hours are not stated here."),
]

# Counters: New York list pasted from the official locator on 2026-11-02 (address only; no city/ZIP shown by the locator).
# Warehouse/distribution entries removed. distances are from the locator's New York, NY search centre.
COUNTERS_NY = [
    ("G. ARMANI BOUTIQUE-FIFTH AVENUE", "717 FIFTH AVENUE", None, "Armani boutique", 3.77),
    ("G. ARMANI BOUTIQUE-NEW YORK", "601 MADISON AVE", None, "Armani boutique", 3.88),
    ("G. ARMANI BOUTIQUE-NEW YORK", "760 MADISON AVE", None, "Armani boutique", 4.26),
    ("EMPORIO ARMANI-SOHO", "410 WEST BROADWAY", None, "Emporio Armani", 0.86),
    ("EMPORIO ARMANI-FIFTH AVE NY", "110 FIFTH AVENUE", "212-727-3240", "Emporio Armani", 1.85),
    ("SEPHORA-BROADWAY", "150 BROADWAY", None, "Sephora", 0.33),
    ("BLOOMINGDALES-SOHO", "504 BROADWAY", None, "department store", 0.74),
    ("SEPHORA/SOHO", "555 BROADWAY", None, "Sephora", 0.86),
    ("MACY'S-HERALD SQUARE", "135 W 34TH ST", "212-695-4400", "department store", 2.74),
    ("LORD & TAYLOR/NEW YORK", "424 5TH AVE", "212-391-3344", "department store", 2.93),
    ("SAKS FIFTH AVENUE-NEW YORK", "611 FIFTH AVENUE", "212-753-4000", "department store", 3.48),
    ("BERGDORF GOODMAN-NY #1", "2 W 58TH ST", "212-753-7300", "department store", 3.88),
    ("BLOOMINGDALES-NEW YORK 59TH STREET", "1000 THIRD AVE", "212-705-2886", "department store", 3.96),
    ("SEPHORA-34TH STREET", "130 WEST 34TH STREET", "212 629 9135", "Sephora", 2.72),
    ("SEPHORA-FIFTH AVENUE", "597 5TH AVENUE", None, "Sephora", 3.42),
    ("SEPHORA-COLUMBUS CIRCLE", "10 COLUMBUS CIRCLE, SP 204", None, "Sephora", 4.03),
    ("SEPHORA-76th & BROADWAY", "2103 BROADWAY", "212 362-1500", "Sephora", 4.81),
]
STORE_LOCATOR_URL = f"{BASE}/store-finder/"
RETAILERS_URL = f"{BASE}/authorized-retailers/customer-service-armani-stores.html"
AUTHORIZED_RETAILERS = "Prestige department stores (Saks Fifth Avenue, Neiman Marcus, Nordstrom, Bloomingdales, Bergdorf Goodman); Macy's and Dillards; Sephora, Sephora in Kohls and Ulta."
