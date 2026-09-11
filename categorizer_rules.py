"""Regelbasierte (kostenlose) Kategorisierung -- keine KI-API noetig.

Keyword-Listen wurden aus der echten Buchungshistorie in Finanzen.xlsx
abgeleitet (Januar-Mai). Bei Unklarheit/keinem Treffer faellt es auf
"Sonstiges" zurueck -- der Nutzer bestaetigt/korrigiert ohnehin jede
Zeile vor dem Eintragen."""
from __future__ import annotations

EXPENSE_KEYWORDS: dict[str, list[str]] = {
    "Essen/Trinken": [
        "rewe", "edeka", "kaufland", "aldi", "lidl", "netto", "penny", "real",
        "globus", "hit", "e center", "supermarkt", "baecker", "bäcker",
        "cafe", "café", "doener", "döner", "mcdonalds", "mc donalds",
        "burger king", "kfc", "restaurant", "imbiss", "kaugummi",
        "monster energy", "bistro",
    ],
    "Klamotten": [
        "zara", "h&m", "cos", "primark", "vinted", "second hand", "schuhe",
        "zalando", "about you", "c&a", "bershka", "pull&bear",
    ],
    "Flüge": ["flug ", "flugüber", "ryanair", "lufthansa", "eurowings", "easyjet", "condor"],
    "Hotel": ["hotel", "airbnb", "booking.com", "booking "],
    "Freizeit": ["kino", "cinema", "therme", "schwimmbad", "freizeitpark", "konzert", "concert"],
    "Online": ["amazon", "ebay", "parfuem", "parfüm", "otto", "aliexpress", "shein"],
    "Tank": ["tank", "tanken", "aral", "shell", "esso", " jet ", "star tankstelle", "total energies"],
    "Abos": [
        "spotify", "netflix", "disney", "apple", "prime video", "dazn",
        "kickboxen", "fitnessstudio", "mcfit", "urban sports", "adobe",
        "icloud", "venice",
    ],
    "Selfcare": [
        "friseur", "haare", "nagelstudio", "kosmetik", "drogerie", "dm ",
        "rossmann", "serum", "adapalen", "zahnseide",
    ],
    "Transport": ["parken", "parkhaus", "deutsche bahn", "db vertrieb", "strafzettel", "bus", "bahn", "uber", "taxi"],
    "Sparen/Invest": ["trade republic", " tr ", "scalable", "etf", "depot", "sparplan"],
}

INCOME_KEYWORDS: dict[str, list[str]] = {
    "Gehalt": ["gehalt", "lohn", "urlaubsgeld", "bonus"],
    "Taschengeld": ["taschengeld"],
    "Minijob": ["minijob"],
}

EXPENSE_FALLBACK = "Sonstiges"
INCOME_FALLBACK = "Sonstiges"


def _match(text: str, keywords: dict[str, list[str]]) -> str | None:
    lowered = f" {text.lower()} "
    for category, terms in keywords.items():
        for term in terms:
            if term in lowered:
                return category
    return None


def categorize(text: str, is_income: bool) -> str:
    """text: Verwendungszweck/Zahlungsempfaenger-Text aus dem Kontoauszug."""
    if is_income:
        return _match(text, INCOME_KEYWORDS) or INCOME_FALLBACK
    return _match(text, EXPENSE_KEYWORDS) or EXPENSE_FALLBACK
