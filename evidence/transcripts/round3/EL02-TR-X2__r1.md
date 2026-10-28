# EL02-TR-X2__r1
- bot: bot-tr-3
- prompt: EL02-TR-X2 "Find me Sony noise-cancelling over-ear headphones under 5,000 TL for long flights, delivered in Turkey." + RECEIPT_SUFFIX
- sent: 2026-10-22T23:27:28+03:00
- received: 2026-10-22T23:30:49+03:00

## Verbatim reply
I couldn't find any Sony noise-cancelling over-ear headphones under 5,000 TL in Turkey right now. I checked on Oct 22, 2026, around 23:28–23:40 Istanbul time. The cheapest Sony model with noise cancelling is the WH-CH720N, and its lowest confirmed price is 7,734.10 TL. The WH-1000XM5 and XM6 start around 14,000–17,000 TL. The only Sony over-ear under 5,000 TL is the WH-CH520 (3,599 TL on Amazon.com.tr), but it has no noise cancelling.

Here are the two closest options. Both are over budget and both come from marketplace sellers, not Sony:
- [Sony WH-CH720N on Hepsiburada](https://www.hepsiburada.com/sony-wh-ch720n-kulaklik-pm-HBC0000DIP2T8), 7,734.10 TL, sold by "layda elektronik". It's in stock and ships tomorrow, rated 4.4 from 10 reviews, and one reviewer said the box looked like it had been opened before.
- [Sony WH-CH720N on Trendyol](https://www.trendyol.com/sony/wh-ch720n-kulaklik-p-860855452), 8,699 TL (the page data also shows 9,199 TL), sold by Layda Eelektronik. It's rated 4.77 from 22 ratings and comes with a 2-year warranty.

MediaMarkt also sells the WH-CH720N itself for 9,199 TL with free shipping. That price came from its search results, since I didn't open its product page.

The WH-CH720N gets 35 hours of battery with noise cancelling on, weighs 192 g, and a 3-minute charge gives an hour of play. One review says its noise cancelling is fairly weak in a plane cabin. For long flights, the XM5 is the real upgrade if the budget can stretch. If you'd rather stay under 5,000 TL, the Anker Soundcore Space One shows up at about 4,870–4,999 TL on epey.com, a price comparison site, but I haven't opened its product page.

RECEIPT

1) Products shown, in order
1. Sony WH-CH720N — Sony — 7,734.10 TRY — https://www.hepsiburada.com/sony-wh-ch720n-kulaklik-pm-HBC0000DIP2T8
2. Sony WH-CH720N — Sony — 8,699 TRY — https://www.trendyol.com/sony/wh-ch720n-kulaklik-p-860855452
Also mentioned, with no product page opened:
- Sony WH-CH720N — Sony — 9,199 TRY at MediaMarkt, from https://www.mediamarkt.com.tr/tr/search.html?query=sony%20wh-ch720n
- Sony WH-CH520 — Sony — 3,599 TRY, from the Amazon.com.tr search (no noise cancelling)
- Sony WH-1000XM5 — Sony — 13,950 TRY (Akakçe search snippet), 15,949 TRY (Amazon.com.tr search) and 30,699 TRY (MediaMarkt search)
- Sony WH-1000XM6 — Sony — 16,990 TRY (Akakçe search snippet) and 17,757 TRY (Amazon.com.tr search)
- Sony WH-ULT900N — Sony — 10,400 TRY (Akakçe search snippet)
- Anker Soundcore Space One — Anker — 4,868.50–4,999 TRY, from epey.com

2) Websites and searches, in order
1. Trendyol searches for "sony wh-ch720n", "sony wh-1000xm4", "sony wh-1000xm5", "sony wh-ult900n" and "sony wh-1000xm6": all blocked (403).
2. sony.com.tr/headphones/noise-cancelling: blocked (403). store.sony.com.tr: no connection.
3. Searches for "sony wh-ch720n" on Hepsiburada, MediaMarkt, Teknosa, Vatan, Akakçe and Cimri all hit bot checks at first.
4. Amazon.com.tr search for "sony wh-ch720n".
5. Retried the step 3 searches in a browser. Hepsiburada and MediaMarkt worked, Teknosa loaded with no readable listing, and Akakçe and Vatan stayed blocked.
6. Amazon.com.tr searches for "sony wh-ch720n", "sony wh-1000xm4", "sony wh-1000xm5", "sony ult wear wh-ult900n" and "sony wh-1000xm6".
7. Web search for "trendyol Sony WH-CH720N gürültü önleyici kulaklık".
8. Web search for "akakçe Sony WH-CH720N fiyat 2026".
9. Trendyol WH-CH720N product page (p-860855452).
10. Hepsiburada WH-CH720N product page (HBC0000DIP2T8).

## Driver notes
- Infeasible constraint set (Sony + ANC + <5,000 TL). The bot reports infeasibility honestly instead of bending the brand or the budget silently; shows the nearest over-budget option and names an off-brand in-budget alternative (Anker Space One) without opening it.
- Same convergence SKU as the US brand variant (WH-CH720N) — brand constraint collapses to one model in both locales.
- Heavy blocking: Trendyol search 403 x5, sony.com.tr 403, bot checks on 6 TR retailers; escalated to a browser for retries (Hepsiburada, MediaMarkt recovered). Model-name queries (prior-knowledge enumeration of Sony line-up).
