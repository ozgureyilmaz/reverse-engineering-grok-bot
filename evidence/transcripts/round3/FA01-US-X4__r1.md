# FA01-US-X4__r1
- bot: bot-us-3
- prompt: FA01-US-X4 "Show me women's dresses under $60." + RECEIPT_SUFFIX
- sent: 2026-10-22T23:22:23+03:00
- received: 2026-10-22T23:24:19+03:00

## Verbatim reply
Here are 8 women's dresses under $60 from Target. All are on sale right now. My pick is the A New Day Slip Maxi Dress: it's $24.50 with a 4.59 rating from 24 reviews. If you want a print, the Lascana Sleeveless Print Maxi is the best-reviewed one here (4.87 from 36 reviews, $47.96).

- [Lascana Women's Short Sleeve V-Neck Dress](https://www.target.com/p/lascana-women-s-short-sleeve-v-neck-dress/-/A-1000899936), $51.96 (was $64.95), 3.75 from 4 reviews
- [Lascana Women's Floral V-Neck Maxi Dress](https://www.target.com/p/lascana-women-s-floral-v-neck-maxi-dress-sundress-summer-floral/-/A-93631960), $51.96 (was $64.95), 3.0 from 6 reviews
- [A New Day Women's Ruched 3/4 Sleeve Midi Dress](https://www.target.com/p/women-s-ruched-3-4-sleeve-midi-dress-a-new-day/-/A-95265408), $28.00 (was $40.00), 2.62 from 21 reviews
- [A New Day Women's Slip Maxi Dress](https://www.target.com/p/women-s-slip-maxi-dress-a-new-day/-/A-95249315), $24.50 (was $35.00), 4.59 from 24 reviews
- [A New Day Women's Button-Up Midi Sweater Dress](https://www.target.com/p/women-s-button-up-midi-sweater-dress-a-new-day/-/A-95191494), $28.00 (was $40.00), 3.43 from 21 reviews
- [Attraco Women's Scalloped Hem Tennis Dress](https://www.target.com/p/attraco-women-s-scalloped-hem-tennis-dress-with-built-in-bra-and-shorts-pockets-adjustable-crisscross-back-active-dress/-/A-1009990661), $48.85 (was $81.41), an active dress with a built-in bra and shorts, 4.8 from 5 reviews
- [Lascana Women's Sleeveless Print Maxi Dress](https://www.target.com/p/lascana-women-s-sleeveless-print-maxi-dress-sundress-summer/-/A-91379573), $47.96 (was $59.95), 4.87 from 36 reviews
- [Lascana Women's Animal Print Dress](https://www.target.com/p/lascana-women-s-animal-print-dress-sundress-summer-abstract/-/A-94152996), $51.96 (was $64.95), 4.0 from 3 reviews

Nothing was added to a cart and I didn't start a checkout.

RECEIPT
1) Products shown, in order:
1. Lascana Women's Short Sleeve V-Neck Dress | Lascana | $51.96 USD | https://www.target.com/p/lascana-women-s-short-sleeve-v-neck-dress/-/A-1000899936
2. Lascana Women's Floral V-Neck Maxi Dress | Lascana | $51.96 USD | https://www.target.com/p/lascana-women-s-floral-v-neck-maxi-dress-sundress-summer-floral/-/A-93631960
3. A New Day Women's Ruched 3/4 Sleeve Midi Dress | A New Day (Target) | $28.00 USD | https://www.target.com/p/women-s-ruched-3-4-sleeve-midi-dress-a-new-day/-/A-95265408
4. A New Day Women's Slip Maxi Dress | A New Day (Target) | $24.50 USD | https://www.target.com/p/women-s-slip-maxi-dress-a-new-day/-/A-95249315
5. A New Day Women's Button-Up Midi Sweater Dress | A New Day (Target) | $28.00 USD | https://www.target.com/p/women-s-button-up-midi-sweater-dress-a-new-day/-/A-95191494
6. Attraco Women's Scalloped Hem Tennis Dress with Built-in Bra and Shorts Pockets Adjustable Crisscross Back Active Dress | Attraco | $48.85 USD | https://www.target.com/p/attraco-women-s-scalloped-hem-tennis-dress-with-built-in-bra-and-shorts-pockets-adjustable-crisscross-back-active-dress/-/A-1009990661
7. Lascana Women's Sleeveless Print Maxi Dress | Lascana | $47.96 USD | https://www.target.com/p/lascana-women-s-sleeveless-print-maxi-dress-sundress-summer/-/A-91379573
8. Lascana Women's Animal Print Dress | Lascana | $51.96 USD | https://www.target.com/p/lascana-women-s-animal-print-dress-sundress-summer-abstract/-/A-94152996

2) Websites and searches, in order:
1. Target redsky search API (redsky.target.com plp_search_v2), keyword "womens dresses". It was blocked with HTTP 435 and returned no results.
2. Target.com search page https://www.target.com/s?searchTerm=womens+dresses, search terms "womens dresses". Results were filtered to items under $60 by hand. I skipped one card priced as a range of $51.96 to $64.95.

## Driver notes
- Fresh bot, first prompt. Single-store (Target) retrieval, like np-us r1 — not the editorial-first pattern of np-us-r2. Budget term not put into the query; applied as a post-filter on result cards.
- List is Target's result order (not ranked by the bot); pick is rank 4, stated separately. 8 products, highest count so far for US FA01.
- Target redsky API attempted first (HTTP 435), same block as pilot.
