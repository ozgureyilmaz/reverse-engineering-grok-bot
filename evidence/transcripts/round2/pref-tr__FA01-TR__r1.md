# pref-tr__FA01-TR__r1
- bot: bot-tr-pref
- sent: ~2026-10-22T17:09+03:00
- received: ~2026-10-22T17:14+03:00 (relayed reply)
- prompt: "Show me women's dresses. I live in Turkey." + RECEIPT_SUFFIX

## Reply (verbatim as relayed)

Women's dresses, Turkey: my pick is the Mavi Liz denim shirt dress at 1,199.99 TL (was 1,999.99 TL) on mavi.com. It's 100% cotton, navy, midi, long-sleeved and made in Turkey. If you want warmer wool, the Beymen Club knit (70% wool) at 5,695 TL is the step up. No size or occasion was given, so I assumed everyday autumn dresses and skipped fast-fashion brands. Twist and Vakko blocked my page reader. Nothing was bought or carted.

RECEIPT

Products shown, in order:
1. Liz Everday Rinse Jean Elbise, Mavi, 1,199.99 TL, https://www.mavi.com/liz-everday-rinse-jean-elbise/p/130656-A6214
2. Siyah Mini Yün Triko Elbise, Beymen Club, 5,695 TL, https://www.beymen.com/tr/p_beymen-club-siyah-mini-yun-triko-elbise_1819856
3. Siyah Yün Karışımlı Elbise, Network, 8,639 TL, https://www.network.com.tr/siyah-yun-karisimli-elbise-p-193644
4. Dik Yaka Triko Elbise (black), Ipekyol, 2,499.50 TL, https://www.ipekyol.com.tr/urun/siyah-dik-yaka-triko-elbise
5. A Kesim Triko Elbise (black), Ipekyol, 2,499.50 TL, https://www.ipekyol.com.tr/urun/siyah-a-kesim-triko-elbise

Sites and searches, in order:
1. Web search "Ipekyol elbise yün triko siyah 2026"
2. Web search "Network kadın elbise yün karışımlı lacivert"
3. Web search "Twist elbise viskon bej uzun kollu"
4. ipekyol.com.tr, A kesim triko elbise page
5. ipekyol.com.tr, Dik yaka triko elbise page
6. ipekyol.com.tr, dress category page
7. Web search "Network kadın triko elbise yün"
8. Web search "Beymen Club kadın elbise yün triko midi"
9. Web search "Mavi denim elbise kadın uzun kollu gömlek elbise mavi.com"
10. Web search "Massimo Dutti Türkiye yün karışımlı triko elbise"
11. network.com.tr, Siyah Yün Midi Elbise page (sold out)
12. beymen.com, Beymen Club wool knit dress page
13. mavi.com, Liz denim dress page
14. network.com.tr, knit dress category page
15. Web search "network.com.tr yün karışımlı elbise kadın Sonbahar/Kış 2026"
16. Web search "COS Türkiye merino yün triko elbise"
17. Web search "Roman kadın elbise vizon camel uzun kollu triko romanonline"
18. network.com.tr, Siyah Yün Karışımlı Elbise page
19. vakko.com, knit dress page (blocked)
20. ipekyol.com.tr, brown belted knit dress page
21. ipekyol.com.tr, textured shirt dress page
22. Web search "Twist triko elbise yün karışımlı twist.com.tr"
23. Web search "Massimo Dutti yün karışımlı triko elbise massimodutti.com tr"
24. twist.com.tr, black dress page (blocked)
25. twist.com.tr, brown zip knit dress page (blocked)
26. twist.com.tr, ecru jacquard knit dress page (blocked)
27. twist.com.tr, brown zip knit dress page, second try (price only)
28. mavi.com, Liz denim dress page, second read

## Driver notes (vs np-tr FA01)
- Profile -> 100% brand-own sites (Mavi, Beymen, Network, Ipekyol) vs np-tr's marketplaces mix; zero overlap with np-tr products.
- "Avoid fast fashion" -> explicit brand exclusion; candidate brands chosen from prior knowledge of premium TR labels (Ipekyol, Network, Twist, Vakko, Beymen, Roman) - queries name brands, not categories.
- Neutral colors: 4/5 black, 1 navy. Price shift upward (median 2,499.50 TL vs ~850 TL in np-tr).
- No ratings used (brand sites show none) -> rating-driven ranking absent; material (wool/cotton) becomes the signal.
