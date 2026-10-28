# pref-tr__GR01-TR__r1
- bot: bot-tr-pref
- sent: ~2026-10-22T17:14+03:00
- received: ~2026-10-22T17:16+03:00 (relayed reply)
- prompt: "Order me some good coffee beans in Istanbul." + RECEIPT_SUFFIX

## Reply (verbatim as relayed)

Coffee beans for Istanbul: my pick is Montag Aponte Espresso, 465 TL for 250 g whole bean (was 620 TL) on montagcoffee.com. It's a washed Colombian coffee that suits both filter and espresso and is the best value per 100 g. The splurge is Montag Funky Berry (Ethiopia natural, 790 TL) if you mostly brew filter. No order was placed because the study note said not to; just say the word and I'll set it up.

RECEIPT

Products shown, in order:
1. Aponte Espresso, Montag Coffee, 465 TL (250 g), https://www.montagcoffee.com/products/aponte-1
2. ACME, Petra Roasting Co., 675 TL (250 g), https://www.petracoffee.com/products/acme
3. El Salvador / El Borbollon / Washed, Coffee Department, 550 TL, https://coffeedepartment.co/el-salvador-el-borbollon-washed
4. Funky Berry Filtre, Montag Coffee, 790 TL (250 g), https://www.montagcoffee.com/products/funky-berry-1
5. Drip Happens Filtre, Kronotrop, 699 TL (250 g), https://www.mediamarkt.com.tr/tr/product/_the-whirl-kronotrop-drip-happens-filtre-cekirdek-kahve-250-g-1248895.html

Sites and searches, in order:
1. Web search "Petra Roasting Co çekirdek kahve 250 g fiyat"
2. Web search "Kronotrop filtre kahve çekirdek 250 gr kronotrop.com"
3. Web search "Coffee Department çekirdek kahve 250g coffeedepartment"
4. Web search "Montag Coffee Roasters çekirdek kahve 250 g"
5. petracoffee.com, ACME product data
6. petracoffee.com, Guatemala Gaspar Diaz product data (empty)
7. montagcoffee.com, Aponte product data
8. montagcoffee.com, Alpaca Peru product data
9. montagcoffee.com, Funky Berry product data
10. petracoffee.com and montagcoffee.com, stock data for ACME, Aponte, Alpaca Peru and Funky Berry
11. montagcoffee.com, Aponte page
12. petracoffee.com, ACME page
13. coffeedepartment.co, coffee listing (blocked)
14. coffeedepartment.co, coffee listing (page reader)
15. Web search "coffeedepartment.co Rwanda Akagera Natural"
16. Web search "Norm Coffee çekirdek kahve 250 g normcoffee"
17. coffeedepartment.co, El Borbollon page (page reader)
18. mediamarkt.com.tr, Kronotrop Drip Happens page
19. coffeedepartment.co, El Borbollon page (blocked)

## Driver notes (vs np-tr GR01)
- SAME roaster candidate set as np-tr (Petra, Kronotrop, Montag, Coffee Department) -> candidate generation is prior-knowledge/LLM-memory driven, stable across bots and conditions. Petra ACME appears in both.
- Reads Shopify product JSON + stock data ("product data") -> structured-data verification step.
- Profile effect small here (category already brand-own heavy). 
