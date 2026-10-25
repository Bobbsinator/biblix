"""Standorte: grosse, detailreiche Hintergruende zu den wichtigsten Orten der Bibi-Welt.

Jedes Motiv hat feste Farben im Stil seiner Firma (Design, kein Lore-Kanon) und zeigt nur,
was im Masterbrief steht. Neues Motiv: Modul anlegen, Funktion hier in STANDORTE eintragen.
"""
from .tower import tower_schnitt
from .bank import bank_kurstafel
from .mac import mac_menuetafel
from .delivery import delivery_typentafel
from .nassmacher import nass_parkplan
from .plexx import plexx_saalplan
from .burgenland import burgenland_ebenen
from .hh import hh_werkstatt

# (id, Name, Funktion, zugehoeriges Preset oder None, Beschreibung)
STANDORTE = [
    ("standort-tower", "Exabibi Tower", tower_schnitt, "bibi-tech",
     "Schnittzeichnung: 94 OG bis Bibi Tief, mit EXA CENTRAL."),
    ("standort-bank", "Die Kurstafel", bank_kurstafel, "bibi-budget-bank",
     "Zugriffshalle von BBB-BGLD mit der Fallblatt-Knappheitstafel."),
    ("standort-mac", "Bibi Boulevard", mac_menuetafel, "bibi-mac",
     "Die Menütafel über dem Tresen von Bibi Mac."),
    ("standort-delivery", "Delivery W", delivery_typentafel, "bibi-delivery",
     "Typentafel der Würfellogistik, BDW-F bis BDW-B."),
    ("standort-nassmacher", "Nassmacher", nass_parkplan, "nassmacher",
     "Parkplan des Schwimmerlebnisparks an der Donau."),
    ("standort-plexx", "Bibiplexx", plexx_saalplan, "bibiplexx",
     "Saalplan mit Direct-View-Wand und Reihe sieben."),
    ("standort-burgenland", "Burgenland", burgenland_ebenen, None,
     "Der künstliche Berg als Ebenenplan, 0 bis -8."),
    ("standort-hh", "Hierz und Habl", hh_werkstatt, None,
     "Referenzblatt der mobilen IT-Werkstatt (hell)."),
]
