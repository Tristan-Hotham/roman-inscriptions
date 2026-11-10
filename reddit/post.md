**Title:** [OC] I mapped 203,466 Latin inscriptions from the Roman Empire. Under the Severan emperors Romans carved 2.2x as many a year as two generations later.

**Body:**

Every Latin inscription in the LIRE dataset (tombstones, altars, honours, milestones), placed by findspot and spread over its date range.

- 61% of the inscriptions in the dataset come from Rome (75,301) and the rest of Italy.
- AD 193 to 235 produced 2.2 times as many inscriptions a year as AD 250 to 300. But the empire-wide peak is AD 68: Italy wrote first, and 10 of 27 big provinces peaked in AD 175 to 250.
- 29,598 ages at death on tombstones: ages ending in 0 or 5 are hugely over-represented (Whipple index 303, where 100 = no rounding, 500 = all rounded).
- 154 ages on tombstones in Roman Africa are 100 or more. Tombstones are not life tables.
- 865 soldiers' stones name the man's home: median 674 km away, 68% more than 500 km.

Caveats: these are the inscriptions that survived, were found and were digitised, so Rome and Italy dominate and Greek inscriptions are not included. Dates are editors' ranges.

Interactive map with a time slider: https://maps.tristanhotham.com/roman-inscriptions/

**Source comment:**

Data: LIRE v2.1 (Kaše, Heřmánková and Sobotková, Aarhus University; built from the Epigraphik-Datenbank Clauss/Slaby and the Epigraphic Database Heidelberg), CC BY 4.0. Provinces and ancient places: Digital Atlas of the Roman Empire (Lund University). Method: aoristic counts with Monte Carlo dating; ages read with a fixed rule checked by hand; analysis pre-specified in a written plan. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/roman-inscriptions
