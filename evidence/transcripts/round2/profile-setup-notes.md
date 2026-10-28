# Profile setup outcomes (2026-10-22 ~16:53 UTC+3), read via transcripts of the test bots

## bot-tr-pref
Saved the profile to its own agent memory (type profile), labelled "relayed by the operator's agent". Replied to its user:
"I've saved the shopping preferences your other assistant sent over. From now on I'll show prices in TL for delivery to Istanbul and stick to mid-range, minimalist, well-made picks. I'll check the brand's own site first, then Trendyol or Hepsiburada."

## bot-us-pref
Did NOT save. It told its user that the prefs came from another bot rather than the user and that "Austin doesn't match what I know (that you're in [city])", and showed a widget: "Should I save these as your shopping preferences?" (Yes, save all of them / Save them, but I'm in [city] / Don't save them).

## Methodological findings
1. CONFOUND: the "fresh" test bots inherit the owner's shared user memory (a name, a city, and a timezone, etc.). No condition is truly "no profile". Location in np-* bots is stated in the prompt, but the shared profile already says Turkey/[city], which may bias np-us runs too.
2. Profile provenance gating: agent-relayed preferences are treated as lower-trust; one bot gates them on owner confirmation, the other saves them with a provenance label. Behavior is not deterministic across identical fresh bots.
