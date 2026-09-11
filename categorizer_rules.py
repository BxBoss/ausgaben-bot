"""Regelbasierte (kostenlose) Kategorisierung -- keine KI-API noetig.

Keyword-Listen wurden aus der echten Buchungshistorie in Finanzen.xlsx
abgeleitet (Januar-Mai). Bei Unklarheit/keinem Treffer faellt es auf
"Sonstiges" zurueck -- der Nutzer bestaetigt/korrigiert ohnehin jede
Zeile vor dem Eintragen."""
from __future__ import annotations

EXPENSE_KEYWORDS: dict[str, list[str]] = {
    "Essen/Trinken": [
        "rewe", "edeka", "kaufland", "aldi", "lidl", "netto", "penny", "real",
        "globus", "hit", "e center", "supermarkt", "spar", "baecker", "bäcker",
        "cafe", "café", "doener", "döner", "mcdonalds", "mc donalds", "mc donald",
        "burger king", "kfc", "restaurant", "imbiss", "kaugummi",
        "monster energy", "bistro", "snack bar", "mini market", "kiosk",
        "self service", "vending", "wolt", "lieferando", "pastizzeria",
        "foodstore", "food store", "acai", "myconvenience", "convenience",
        "nom nom", "little greens", "kebab", "8 till late", "instastore",
        "onami", "dave's", "daves", "biergarten", "superfood",
        # aus der vollstaendigen Girokonto/Kreditkarten-Historie (Jan-Sep)
        "ruhls bestes", "maxims", "habibis", "good food better", "mensa",
        "chapeau", "aquamarina", "food source", "gelateria", "flox burger",
        "green midi", "burger n shake", "merzenich", "diamond taste",
        "medasia", "big g", "tiffany s gelateria",
        # zweite Runde: Griechenland-/Amsterdam-/Strasbourg-Reise
        "star coffee", "burger colony", "bengels", "weinbar", "franz josef",
        "elaia", "tavern", "aladdin", "kalamaki", "tzatzi", "albert heijn",
        "horeca", "jumbo amsterdam", "bunsbar",
    ],
    "Klamotten": [
        "zara", "h&m", "cos", "primark", "vinted", "second hand", "schuhe",
        "zalando", "about you", "c&a", "bershka", "pull&bear", "boutique",
        "vintage", "fashion retail", "intersport", "hennes", "secondplus",
        "decathlon",
    ],
    "Flüge": ["flug ", "flugüber", "ryanair", "lufthansa", "eurowings", "easyjet", "condor"],
    "Hotel": ["hotel", "airbnb", "booking.com", "booking ", "bravonext"],
    "Freizeit": [
        "kino", "cinema", "therme", "schwimmbad", "freizeitpark", "konzert",
        "concert", "getyourguide", "hive club", "paceville ent", "club ",
        # Museen/Sehenswuerdigkeiten/Ausflugsziele -- z.B. "Fort St Elmo
        # National (War Museum)" ist ein Museumsbesuch, keine "Sonstiges"-Buchung.
        "museum", "fort st elmo", "blue grotto", "bluegrotto", "national war",
        "smash tag", "footloose", "stadtpark", "eventim", "gianpula",
        "jlm marketing", "eventworks", "geisterklamm", "salinarium",
        "tripass", "toyroom", "billard", "natura artis", "bulldog",
    ],
    "Online": ["amazon", "ebay", "parfuem", "parfüm", "otto", "aliexpress", "shein"],
    "Tank": [
        "tank", "tanken", "aral", "shell", "esso", " jet ", "star tankstelle",
        "total energies", "agip", "couche-tard",
    ],
    "Abos": [
        "spotify", "netflix", "disney", "apple", "prime video", "dazn",
        "kickboxen", "fitnessstudio", "mcfit", "urban sports", "adobe",
        "icloud", "venice", "anthropic", "claude sub", "openai", "chatgpt",
        "higgsfield", "kampfsportzentrum", "sportzentrum",
        "shopify international", "adac medien",
    ],
    "Selfcare": [
        "friseur", "haare", "nagelstudio", "kosmetik", "drogerie", "dm ",
        "rossmann", "serum", "adapalen", "zahnseide", "pharmacy", "apotheke",
        "medical", "niche beauty lab", "mueller bad",
    ],
    "Transport": [
        "parken", "parkhaus", "deutsche bahn", "db vertrieb", "strafzettel",
        "bus", "bahn", "uber", "taxi", "public trans", "easypark",
        "parkgarage", "bußgeldstelle", "polizeiverwaltungsamt", "triwo hahn",
        "ktel", "cts-", "ovpay",
    ],
    "Sparen/Invest": [
        "trade republic", " tr ", "scalable", "etf", "depot", "sparplan",
        "bitget",
        # eigene Ueberweisung aufs andere Konto zaehlt laut Nils ebenfalls als
        # Sparen/Invest. Im echten Kontoauszug taucht das als Ueberweisung an
        # "Nils Bendinger" (eigener Name, anderes Konto) auf -- Annahme: JEDE
        # solche Selbst-Ueberweisung ist eine Sparbuchung. Falls das im
        # Einzelfall nicht stimmt (z.B. Geld fuers Ausgeben verschoben),
        # muss die Zeile manuell korrigiert werden.
        "umbuchung", "eigenes konto", "sparkonto", "tagesgeld", "nils bendinger",
    ],
    "Bankgebühren/Steuern": ["kapitalertragsteuer", "wiederpräg", "kontoführung"],
}

INCOME_KEYWORDS: dict[str, list[str]] = {
    "Gehalt": ["gehalt", "lohn", "urlaubsgeld", "bonus"],
    "Taschengeld": ["taschengeld"],
    "Minijob": ["minijob"],
    # Bareinzahlungen sind laut Nils immer Trinkgeld (Bargeld aus dem Job,
    # das aufs Konto eingezahlt wird). " bar " mit Leerzeichen drumherum,
    # damit es nicht versehentlich in anderen Woertern matcht.
    "Trinkgeld": [" bar ", "einzahlung"],
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
