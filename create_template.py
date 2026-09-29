"""Erzeugt eine leere Finanzen.xlsx-Vorlage: Dashboard + "Transaktionen"-
Tabelle (Excel-Tabelle, waechst automatisch mit) + 12 Monatsblaetter mit
Kennzahlen-Kacheln, Kategorie-Tabellen und Diagrammen -- aber ohne
Buchungen. Fuellen mit `import_kontoauszug.py`.

Nutzung:
    python create_template.py [ziel_pfad.xlsx]

Ohne Argument wird "Finanzen.xlsx" im aktuellen Ordner angelegt.
"""
from __future__ import annotations

import sys

import openpyxl
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.data_source import StrRef
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

import categorizer_rules

MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]

# Kategorienlisten direkt aus categorizer_rules ableiten statt hier
# nochmal von Hand zu pflegen -- neue Kategorien dort tauchen automatisch
# in Vorlage und Dashboard auf.
AUSGABEN_KATEGORIEN = list(categorizer_rules.EXPENSE_KEYWORDS.keys()) + [categorizer_rules.EXPENSE_FALLBACK]
EINNAHMEN_KATEGORIEN = list(categorizer_rules.INCOME_KEYWORDS.keys()) + [categorizer_rules.INCOME_FALLBACK]

# ---------- Farben ("schlicht", + grün, - rot) ----------
GRUEN = "2E9E44"
ROT = "E5342A"
AKZENT = "1F4E5F"
HELLGRAU = "F2F3F5"
RAHMEN_GRAU = "D9DCE1"

# Feste Palette, per Index den Kategorien zugewiesen -- so hat z.B. immer
# die erste Ausgaben-Kategorie dieselbe Farbe, ohne dass hier jede
# Kategorie einzeln benannt werden muss (die Liste kommt ja dynamisch
# aus categorizer_rules).
_PALETTE = ["4E79A7", "F28E2B", "E15759", "76B7B2", "59A14F", "EDC948",
            "B07AA1", "FF9DA7", "9C755F", "BAB0AC", "D37295", "8CD17D",
            "6B4C9A", "499894", "F1CE63"]


def _farben_fuer(kategorien: list[str]) -> dict[str, str]:
    return {kat: _PALETTE[i % len(_PALETTE)] for i, kat in enumerate(kategorien)}


AUSGABEN_FARBEN = _farben_fuer(AUSGABEN_KATEGORIEN)
EINNAHMEN_FARBEN = _farben_fuer(EINNAHMEN_KATEGORIEN)

FONT_TITEL = Font(name="Calibri", size=20, bold=True, color=AKZENT)
FONT_UNTERTITEL = Font(name="Calibri", size=11, color="6B7280")
FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_STAT_LABEL = Font(name="Calibri", size=10, color="6B7280")
FONT_STAT_VALUE = Font(name="Calibri", size=18, bold=True)
FILL_HEADER = PatternFill("solid", fgColor=AKZENT)
FILL_STAT = PatternFill("solid", fgColor=HELLGRAU)
THIN = Side(style="thin", color=RAHMEN_GRAU)
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# D/F/G sind in der Kacheln-Zeile nur schmale Luecken zwischen den 4
# Kennzahlen-Boxen, dienen weiter unten aber auch als Spalten der
# Transaktionsliste (Kategorie/Verwendungszweck/Quelle) -- deshalb breiter
# als eine reine Luecke gewaehlt.
COL_WIDTHS = {"A": 2, "B": 15, "C": 15, "D": 18, "E": 15, "F": 35, "G": 13,
              "H": 15, "I": 15, "J": 2, "K": 15, "L": 15, "M": 3}


def color_pie_slices(pie_chart, kategorien, farben):
    points = [DataPoint(idx=i, spPr=GraphicalProperties(solidFill=farben.get(kat, "9E9E9E")))
              for i, kat in enumerate(kategorien)]
    pie_chart.series[0].data_points = points


def use_text_categories(chart):
    """openpyxl schreibt Kategorie-Achsen standardmaessig als numRef, auch
    wenn die referenzierten Zellen Text enthalten (Monatsnamen,
    Kategorienamen) -- Excel zeigt dann "Datenreihe1" statt der echten
    Namen. Fix: numRef durch strRef ersetzen."""
    for series in chart.series:
        if series.cat is not None and series.cat.numRef is not None:
            f = series.cat.numRef.f
            series.cat.numRef = None
            series.cat.strRef = StrRef(f=f)


def _styled_pie(title: str, height: float, width: float) -> PieChart:
    pie = PieChart()
    pie.title = title
    pie.height = height
    pie.width = width
    pie.legend.position = "r"
    pie.legend.overlay = False
    pie.dataLabels = DataLabelList()
    pie.dataLabels.showCatName = True
    pie.dataLabels.showPercent = True
    pie.dataLabels.showVal = False
    pie.dataLabels.showSerName = False
    pie.dataLabels.showLegendKey = False
    pie.dataLabels.numFmt = "0%"
    pie.dataLabels.dLblPos = "bestFit"
    return pie


def build(dst_path: str) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ---------- Sheet: Transaktionen (leer, nur Header) ----------
    tx_ws = wb.create_sheet("Transaktionen")
    headers = ["Datum", "Monat", "Typ", "Kategorie", "Betrag", "Verwendungszweck", "Quelle"]
    for col, h in enumerate(headers, start=1):
        tx_ws.cell(row=1, column=col, value=h)

    tx_ws.column_dimensions["A"].width = 12
    tx_ws.column_dimensions["B"].width = 11
    tx_ws.column_dimensions["C"].width = 10
    tx_ws.column_dimensions["D"].width = 20
    tx_ws.column_dimensions["E"].width = 13
    tx_ws.column_dimensions["F"].width = 45
    tx_ws.column_dimensions["G"].width = 12
    tx_ws.freeze_panes = "A2"

    table = Table(displayName="Transaktionen", ref="A1:G1")
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False,
        showLastColumn=False, showColumnStripes=False,
    )
    tx_ws.add_table(table)

    green_rule = CellIsRule(operator="greaterThan", formula=["0"], font=Font(color=GRUEN, bold=True))
    red_rule = CellIsRule(operator="lessThan", formula=["0"], font=Font(color=ROT, bold=True))
    tx_ws.conditional_formatting.add("E2:E1048576", green_rule)
    tx_ws.conditional_formatting.add("E2:E1048576", red_rule)

    # ---------- Sheet: Dashboard ----------
    dash = wb.create_sheet("Dashboard", 0)
    dash.sheet_view.showGridLines = False
    for col, w in COL_WIDTHS.items():
        dash.column_dimensions[col].width = w

    dash["B2"] = "Finanzen – Übersicht"
    dash["B2"].font = FONT_TITEL
    dash["B3"] = "Automatisch aus deinen Kontoauszügen befüllt"
    dash["B3"].font = FONT_UNTERTITEL

    tiles = [
        ("EINNAHMEN GESAMT", '=SUMIFS(Transaktionen[Betrag],Transaktionen[Typ],"Einnahme")', "B", "C", GRUEN),
        ("AUSGABEN GESAMT", '=SUMIFS(Transaktionen[Betrag],Transaktionen[Typ],"Ausgabe")', "E", "F", ROT),
        ("NETTO", "=B6+E6", "H", "I", None),
        ("Ø SPARQUOTE", '=IFERROR(-SUMIFS(Transaktionen[Betrag],Transaktionen[Kategorie],"Sparen/Invest")/B6,0)', "K", "L", None),
    ]
    for label, formula, c1, c2, color in tiles:
        dash.merge_cells(f"{c1}5:{c2}5")
        lbl = dash[f"{c1}5"]
        lbl.value = label
        lbl.font = FONT_STAT_LABEL
        lbl.alignment = Alignment(horizontal="left")

        dash.merge_cells(f"{c1}6:{c2}7")
        val = dash[f"{c1}6"]
        val.value = formula
        val.number_format = "0.0%" if "Sparquote" in label else '#,##0.00" €"'
        val.font = Font(name="Calibri", size=18, bold=True, color=color) if color else FONT_STAT_VALUE
        val.alignment = Alignment(horizontal="left", vertical="center")

        for row in (5, 6, 7):
            for c in (c1, c2):
                dash[f"{c}{row}"].fill = FILL_STAT
        dash[f"{c1}5"].border = Border(left=THIN, top=THIN)
        dash[f"{c2}5"].border = Border(right=THIN, top=THIN)
        dash[f"{c1}7"].border = Border(left=THIN, bottom=THIN)
        dash[f"{c2}7"].border = Border(right=THIN, bottom=THIN)

    dash.conditional_formatting.add("H6", CellIsRule(operator="greaterThanOrEqual", formula=["0"], font=Font(size=18, bold=True, color=GRUEN)))
    dash.conditional_formatting.add("H6", CellIsRule(operator="lessThan", formula=["0"], font=Font(size=18, bold=True, color=ROT)))

    dash["B10"] = "Monatsübersicht"
    dash["B10"].font = Font(name="Calibri", size=13, bold=True, color=AKZENT)
    month_headers = ["Monat", "Einnahmen", "Ausgaben", "Netto", "Sparquote"]
    for col, h in enumerate(month_headers, start=2):
        c = dash.cell(row=11, column=col, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.alignment = Alignment(horizontal="center")
        c.border = BORDER_ALL

    for i, monat in enumerate(MONTHS_DE):
        row = 12 + i
        dash.cell(row=row, column=2, value=monat).border = BORDER_ALL
        e = dash.cell(row=row, column=3, value=f'=SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],B{row},Transaktionen[Typ],"Einnahme")')
        a = dash.cell(row=row, column=4, value=f'=SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],B{row},Transaktionen[Typ],"Ausgabe")')
        n = dash.cell(row=row, column=5, value=f"=C{row}+D{row}")
        s = dash.cell(row=row, column=6, value=f'=IFERROR(-SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],B{row},Transaktionen[Kategorie],"Sparen/Invest")/C{row},0)')
        for cell, fmt in [(e, '#,##0" €"'), (a, '#,##0" €"'), (n, '#,##0" €"'), (s, "0%")]:
            cell.number_format = fmt
            cell.border = BORDER_ALL
        if (i + 1) % 2 == 0:
            for col in range(2, 7):
                dash.cell(row=row, column=col).fill = FILL_STAT

    month_first_row, month_last_row = 12, 12 + len(MONTHS_DE) - 1

    dash["B26"] = "Ausgaben nach Kategorie (gesamter Zeitraum)"
    dash["B26"].font = Font(name="Calibri", size=13, bold=True, color=AKZENT)
    dash.cell(row=27, column=2, value="Kategorie").font = FONT_HEADER
    dash.cell(row=27, column=2).fill = FILL_HEADER
    dash.cell(row=27, column=3, value="Summe").font = FONT_HEADER
    dash.cell(row=27, column=3).fill = FILL_HEADER
    for c in (2, 3):
        dash.cell(row=27, column=c).border = BORDER_ALL
        dash.cell(row=27, column=c).alignment = Alignment(horizontal="center")

    for i, kat in enumerate(AUSGABEN_KATEGORIEN):
        row = 28 + i
        dash.cell(row=row, column=2, value=kat).border = BORDER_ALL
        v = dash.cell(row=row, column=3, value=f'=-SUMIFS(Transaktionen[Betrag],Transaktionen[Kategorie],B{row},Transaktionen[Typ],"Ausgabe")')
        v.number_format = '#,##0" €"'
        v.border = BORDER_ALL
        if (i + 1) % 2 == 0:
            for col in (2, 3):
                dash.cell(row=row, column=col).fill = FILL_STAT

    kat_first_row, kat_last_row = 28, 28 + len(AUSGABEN_KATEGORIEN) - 1

    trend_bar = BarChart()
    trend_bar.type = "col"
    trend_bar.title = "Einnahmen & Ausgaben pro Monat"
    trend_bar.y_axis.title = "EUR"
    trend_bar.x_axis.title = "Monat"
    trend_bar.style = 10
    trend_bar.gapWidth = 40
    trend_bar.height = 9
    trend_bar.width = 22

    cats = Reference(dash, min_col=2, min_row=month_first_row, max_row=month_last_row)
    einnahmen_ref = Reference(dash, min_col=3, min_row=11, max_row=month_last_row)
    ausgaben_ref = Reference(dash, min_col=4, min_row=11, max_row=month_last_row)
    trend_bar.add_data(einnahmen_ref, titles_from_data=True)
    trend_bar.add_data(ausgaben_ref, titles_from_data=True)
    trend_bar.set_categories(cats)
    trend_bar.series[0].graphicalProperties.solidFill = GRUEN
    trend_bar.series[1].graphicalProperties.solidFill = ROT
    trend_bar.legend.position = "b"
    trend_bar.legend.overlay = False
    use_text_categories(trend_bar)
    dash.add_chart(trend_bar, "H5")

    spar_line = LineChart()
    spar_line.title = "Sparquote pro Monat"
    spar_line.y_axis.title = "Sparquote"
    spar_line.y_axis.numFmt = "0%"
    spar_line.x_axis.title = "Monat"
    spar_line.height = 7
    spar_line.width = 22
    sparquote_ref = Reference(dash, min_col=6, min_row=11, max_row=month_last_row)
    spar_line.add_data(sparquote_ref, titles_from_data=True)
    spar_line.set_categories(cats)
    spar_line.series[0].graphicalProperties.line.solidFill = AKZENT
    spar_line.series[0].graphicalProperties.line.width = 20000
    spar_line.series[0].smooth = False
    spar_line.series[0].marker.symbol = "circle"
    spar_line.series[0].marker.size = 6
    spar_line.legend = None
    use_text_categories(spar_line)
    dash.add_chart(spar_line, "H23")

    pie = _styled_pie("Ausgaben nach Kategorie", 12.5, 19)
    kat_cats = Reference(dash, min_col=2, min_row=kat_first_row, max_row=kat_last_row)
    kat_vals = Reference(dash, min_col=3, min_row=kat_first_row, max_row=kat_last_row)
    pie.add_data(kat_vals, titles_from_data=False)
    pie.set_categories(kat_cats)
    color_pie_slices(pie, AUSGABEN_KATEGORIEN, AUSGABEN_FARBEN)
    use_text_categories(pie)
    dash.add_chart(pie, "H37")

    # ---------- Monatsblaetter ----------
    for monat in MONTHS_DE:
        ms = wb.create_sheet(monat)
        ms.sheet_view.showGridLines = False
        for col, w in COL_WIDTHS.items():
            ms.column_dimensions[col].width = w

        ms["B2"] = monat
        ms["B2"].font = FONT_TITEL
        ms["B3"] = "Monatsübersicht"
        ms["B3"].font = FONT_UNTERTITEL

        monat_idx = MONTHS_DE.index(monat)
        prev_monat = MONTHS_DE[monat_idx - 1] if monat_idx > 0 else None

        m_tiles = [
            ("EINNAHMEN", f'=SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],"{monat}",Transaktionen[Typ],"Einnahme")', "B", "C", GRUEN, False),
            ("AUSGABEN", f'=SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],"{monat}",Transaktionen[Typ],"Ausgabe")', "E", "F", ROT, False),
            ("NETTO", "=B6+E6", "H", "I", None, False),
            ("SPARQUOTE", f'=IFERROR(-SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],"{monat}",Transaktionen[Kategorie],"Sparen/Invest")/B6,0)', "K", "L", None, True),
        ]
        for label, formula, c1, c2, color, is_percent in m_tiles:
            ms.merge_cells(f"{c1}5:{c2}5")
            lbl = ms[f"{c1}5"]
            lbl.value = label
            lbl.font = FONT_STAT_LABEL

            ms.merge_cells(f"{c1}6:{c2}7")
            val = ms[f"{c1}6"]
            val.value = formula
            val.number_format = "0.0%" if "SPARQUOTE" in label else '#,##0.00" €"'
            val.font = Font(name="Calibri", size=16, bold=True, color=color) if color else FONT_STAT_VALUE
            val.alignment = Alignment(horizontal="left", vertical="center")

            ms.merge_cells(f"{c1}8:{c2}8")
            delta_cell = ms[f"{c1}8"]
            if prev_monat is None:
                delta_cell.value = "Erster Monat"
                delta_cell.font = FONT_UNTERTITEL
            else:
                delta_cell.value = f"=IFERROR({c1}6-'{prev_monat}'!{c1}6,\"–\")"
                delta_cell.number_format = '+0.0%;-0.0%' if is_percent else '+#,##0" €";-#,##0" €"'
                delta_cell.font = FONT_UNTERTITEL
            delta_cell.alignment = Alignment(horizontal="left")

            for row in (5, 6, 7):
                for c in (c1, c2):
                    ms[f"{c}{row}"].fill = FILL_STAT
            ms[f"{c1}5"].border = Border(left=THIN, top=THIN)
            ms[f"{c2}5"].border = Border(right=THIN, top=THIN)
            ms[f"{c1}7"].border = Border(left=THIN, bottom=THIN)
            ms[f"{c2}7"].border = Border(right=THIN, bottom=THIN)

        ms.conditional_formatting.add("H6", CellIsRule(operator="greaterThanOrEqual", formula=["0"], font=Font(size=16, bold=True, color=GRUEN)))
        ms.conditional_formatting.add("H6", CellIsRule(operator="lessThan", formula=["0"], font=Font(size=16, bold=True, color=ROT)))

        ms["B10"] = "Ausgaben nach Kategorie"
        ms["B10"].font = Font(name="Calibri", size=13, bold=True, color=AKZENT)
        ms.cell(row=11, column=2, value="Kategorie").font = FONT_HEADER
        ms.cell(row=11, column=2).fill = FILL_HEADER
        ms.cell(row=11, column=3, value="Betrag").font = FONT_HEADER
        ms.cell(row=11, column=3).fill = FILL_HEADER
        for c in (2, 3):
            ms.cell(row=11, column=c).border = BORDER_ALL
            ms.cell(row=11, column=c).alignment = Alignment(horizontal="center")

        for i, kat in enumerate(AUSGABEN_KATEGORIEN):
            row = 12 + i
            ms.cell(row=row, column=2, value=kat).border = BORDER_ALL
            v = ms.cell(row=row, column=3,
                        value=f'=-SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],"{monat}",Transaktionen[Kategorie],B{row},Transaktionen[Typ],"Ausgabe")')
            v.number_format = '#,##0" €"'
            v.border = BORDER_ALL
            if (i + 1) % 2 == 0:
                for col in (2, 3):
                    ms.cell(row=row, column=col).fill = FILL_STAT
        a_kat_first, a_kat_last = 12, 12 + len(AUSGABEN_KATEGORIEN) - 1

        ei_start_row = a_kat_last + 3
        ms.cell(row=ei_start_row - 1, column=2, value="Einnahmen nach Kategorie").font = Font(name="Calibri", size=13, bold=True, color=AKZENT)
        ms.cell(row=ei_start_row, column=2, value="Kategorie").font = FONT_HEADER
        ms.cell(row=ei_start_row, column=2).fill = FILL_HEADER
        ms.cell(row=ei_start_row, column=3, value="Betrag").font = FONT_HEADER
        ms.cell(row=ei_start_row, column=3).fill = FILL_HEADER
        for c in (2, 3):
            ms.cell(row=ei_start_row, column=c).border = BORDER_ALL
            ms.cell(row=ei_start_row, column=c).alignment = Alignment(horizontal="center")

        for i, kat in enumerate(EINNAHMEN_KATEGORIEN):
            row = ei_start_row + 1 + i
            ms.cell(row=row, column=2, value=kat).border = BORDER_ALL
            v = ms.cell(row=row, column=3,
                        value=f'=SUMIFS(Transaktionen[Betrag],Transaktionen[Monat],"{monat}",Transaktionen[Kategorie],B{row},Transaktionen[Typ],"Einnahme")')
            v.number_format = '#,##0" €"'
            v.border = BORDER_ALL
            if (i + 1) % 2 == 0:
                for col in (2, 3):
                    ms.cell(row=row, column=col).fill = FILL_STAT
        e_kat_first, e_kat_last = ei_start_row + 1, ei_start_row + len(EINNAHMEN_KATEGORIEN)

        m_pie = _styled_pie("Ausgaben nach Kategorie", 12.5, 19)
        m_pie.add_data(Reference(ms, min_col=3, min_row=a_kat_first, max_row=a_kat_last), titles_from_data=False)
        m_pie.set_categories(Reference(ms, min_col=2, min_row=a_kat_first, max_row=a_kat_last))
        color_pie_slices(m_pie, AUSGABEN_KATEGORIEN, AUSGABEN_FARBEN)
        use_text_categories(m_pie)
        ms.add_chart(m_pie, "H5")

        m_pie2 = _styled_pie("Einnahmen nach Kategorie", 9, 17)
        m_pie2.add_data(Reference(ms, min_col=3, min_row=e_kat_first, max_row=e_kat_last), titles_from_data=False)
        m_pie2.set_categories(Reference(ms, min_col=2, min_row=e_kat_first, max_row=e_kat_last))
        color_pie_slices(m_pie2, EINNAHMEN_KATEGORIEN, EINNAHMEN_FARBEN)
        use_text_categories(m_pie2)
        ms.add_chart(m_pie2, "H32")

        tx_section_row = 55
        ms.cell(row=tx_section_row, column=2, value="Transaktionen").font = Font(name="Calibri", size=13, bold=True, color=AKZENT)
        tx_headers = ["Datum", "Typ", "Kategorie", "Betrag", "Verwendungszweck", "Quelle"]
        header_row = tx_section_row + 1
        for col, h in enumerate(tx_headers, start=2):
            c = ms.cell(row=header_row, column=col, value=h)
            c.font = FONT_HEADER
            c.fill = FILL_HEADER
            c.alignment = Alignment(horizontal="center")
        ms.cell(row=header_row + 1, column=2, value="Keine Buchungen in diesem Monat.").font = FONT_UNTERTITEL

    wb.save(dst_path)
    print(f"Vorlage gespeichert: {dst_path}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Finanzen.xlsx"
    build(target)
