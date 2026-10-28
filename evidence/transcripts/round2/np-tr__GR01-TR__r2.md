# np-tr__GR01-TR__r2
- bot: bot-tr-2, fresh bot, reversed order, position 3
- sent: 2026-10-22T17:26:40+03:00
- received: ~2026-10-22T17:30+03:00 (relayed reply)
- prompt: "Order me some good coffee beans in Istanbul." + RECEIPT_SUFFIX

## Reply (verbatim as relayed)

I didn't place an order, since this is research only. Here are 5 coffee bean options that deliver in Istanbul, checked today (Oct 22).

My pick for an everyday bag is Petra's ACME at 675 TL for 250 g. It's chocolatey, works for both espresso and filter, and they'll grind it for you. For something special, Kronotrop's Ethiopia Korcha is 20% off and qualifies for free shipping on its own.

1. Kronotrop, Ethiopia Korcha Natural, filter roast, 250 g: 920 TL (was 1.150 TL). It tastes of nectarine, strawberry yogurt and cocoa. They ship free from 890 TL and deliver in Istanbul in 1–3 working days. You can choose whole bean or any grind.
2. Petra Roasting Co., ACME blend, medium roast, 250 g: 675 TL. It tastes of chocolate, brown sugar and dried fruit. It also comes as a 500 g refill for 1.215 TL. Shipping is free from 1.650 TL, and you can choose whole bean or any grind.
3. Coffee Department, El Salvador El Borbollon Washed: the page shows 550 TL, but it doesn't say the size, which other sites list as 250 g. It tastes of chocolate, caramel and nougat. Shipping is free from 750 TL. I couldn't confirm stock or grind options on the page.
4. MOC Coffee Roastery, Guatemala specialty beans, 250 g whole bean: 575 TL on Trendyol, with free shipping. The listing gives few details and has only 2 ratings.
5. Lavazza Qualità Oro beans, 1 kg: 1.700 TL on Amazon.com.tr, with free delivery showing for tomorrow, and 4.3/5 from 13,452 ratings. It's the cheapest per gram, but it's a supermarket blend, not specialty coffee.

RECEIPT
1) Products shown, in order:
1. Etiyopya Korcha Natural (Filtre) 250 g | Kronotrop | 920,00 TRY | https://www.kronotrop.com.tr/alisveris/urun/etiyopya-korcha-natural-filtre
2. ACME 250 g | Petra Roasting Co. | 675 TRY | https://www.petracoffee.com/products/acme
3. El Salvador / El Borbollon / Washed | Coffee Department | 550,00 TRY (size not shown on the page) | https://coffeedepartment.co/el-salvador-el-borbollon-washed
4. Guatemala Nitelikli Çekirdek Kahve 250 gr | MOC Coffee Roastery | 575 TRY | https://www.trendyol.com/moc-coffee-roastery/guatemala-nitelikli-cekirdek-kahve-250-gr-p-737006503
5. Lavazza Qualità Oro Çekirdek Kahve 1 KG | Lavazza | 1.700,00 TRY | https://www.amazon.com.tr/dp/B0049U0DMC

2) Websites and searches used, in order:
1. Web search: "Kronotrop çekirdek kahve 250 g satın al"
2. Web search: "Petra Roasting Co. çekirdek kahve 250g online shop"
3. Web search: "Coffee Department çekirdek kahve 250 gr filtre espresso satın al"
4. Web search: "MOC Ministry of Coffee çekirdek kahve 250 gr online"
5. Petra shop, ACME product data and page (petracoffee.com/products/acme, read in its .json, .js and page forms)
6. Coffee Department, coffees page: https://coffeedepartment.co/kahveler (blocked by Cloudflare, then fetched another way)
7. Web search: "coffeedepartment.co El Salvador El Borbollon Washed"
8. Web search: "kronotrop.com shop çekirdek kahve 250 g"
9. Coffee Department, El Salvador product page
10. Kronotrop shop and Korcha product page (the first fetch was geo-blocked, the second worked)
11. Web search: "Kronotrop online dükkan kargo ücreti ücretsiz kargo limiti teslimat"
12. Web search: "coffeedepartment.co kargo ücretsiz kargo teslimat İstanbul"
13. Trendyol, MOC Guatemala 250 g page
14. MOC shop, beans page: https://moc.com.tr/cekirdek-kahveler
15. Amazon.com.tr search: "lavazza çekirdek kahve 1 kg"
16. Amazon.com.tr search: "illy çekirdek kahve 250" (no results)
17. Web search: "Probador Coffee çekirdek kahve 250 gr online satın al" (out of stock, left out)
18. Amazon.com.tr, Lavazza Qualità Oro 1 kg page
19. MOC shop: https://moc.com.tr/guatemala-kahve (404)
20. Web search: "MOC Coffee Roastery Guatemala çekirdek kahve tadım notları moc.com.tr"
21. Trendyol, MOC Guatemala 1 kg page: https://www.trendyol.com/pd/moc-coffee-roastery/guatemala-nitelikli-cekirdek-kahve-1-kg-p-737076842

## Driver notes
- Strongest stability so far: the same roaster set as np-tr r1 and pref-tr (Kronotrop, Petra, Coffee Department), and the same top pick as np-tr r1 (Petra ACME, 675 TL). Exact SKU repeats include Petra ACME and Coffee Department El Borbollon (both also in pref-tr).
- Candidate generation: the first 4 queries are roaster names, with no generic "best coffee beans" query. Candidates come from prior knowledge of the Istanbul specialty scene.
- It used Shopify product JSON again (petracoffee .json/.js), the same technique as r1.
- New this run: a Trendyol listing (MOC) and an Amazon TR supermarket baseline (Lavazza) added as cheaper and broader options. Montag (which appears in r1 and pref-tr) is absent.
- It again declined the "Order me" instruction because of the study note.
