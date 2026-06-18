"""
BEBIS (Hacettepe Universitesi Beslenme Bilgi Sistemi) degerlerine dayali
Turk ev yemekleri ve yerel urunler veritabani.
Cikti: turkish_foods.csv  (food_db.csv ile ayni format)
Kaynak: BEBIS 8.1, TURKKOMP, ilgili akademik yayinlar
"""

from pathlib import Path
import csv

OUT = Path(__file__).parent / "turkish_foods.csv"

# (isim, kategori, kcal, protein_g, carb_g, fat_g, fiber_g) — 100g basina
FOODS = [

    # ── CORBALAR ────────────────────────────────────────────────────────────
    ("Mercimek corbasi",                "Corbalar",  55,  3.5,  8.5,  1.0, 2.0),
    ("Ezogelin corbasi",                "Corbalar",  60,  3.2,  9.8,  1.0, 1.8),
    ("Tarhana corbasi",                 "Corbalar",  52,  2.8,  8.0,  1.2, 0.8),
    ("Domates corbasi",                 "Corbalar",  45,  1.5,  7.0,  1.2, 0.8),
    ("Yayla corbasi",                   "Corbalar",  65,  3.5,  7.5,  2.5, 0.2),
    ("Sehriye corbasi",                 "Corbalar",  68,  2.5, 11.0,  1.5, 0.3),
    ("Iskembe corbasi",                 "Corbalar",  78,  6.0,  4.5,  4.0, 0.0),
    ("Dugun corbasi",                   "Corbalar",  85,  5.5,  6.0,  4.0, 0.2),
    ("Paca corbasi",                    "Corbalar",  92,  7.0,  3.0,  5.5, 0.0),
    ("Sebze corbasi",                   "Corbalar",  42,  1.8,  6.5,  1.0, 1.5),
    ("Patates corbasi",                 "Corbalar",  58,  1.5,  9.5,  1.5, 0.8),
    ("Kremalı mantar corbasi",          "Corbalar",  75,  2.0,  8.0,  3.5, 0.5),
    ("Bezelye corbasi",                 "Corbalar",  72,  4.5, 10.5,  1.5, 3.5),
    ("Tutmac corbasi",                  "Corbalar",  80,  4.5, 10.5,  2.5, 1.5),
    ("Kirmizi mercimek corbasi",        "Corbalar",  58,  3.8,  9.0,  1.0, 2.2),
    ("Taze fasulye corbasi",            "Corbalar",  48,  2.5,  7.5,  1.0, 2.0),
    ("Ispanak corbasi",                 "Corbalar",  55,  2.8,  6.0,  2.5, 1.8),

    # ── PILAVLAR ────────────────────────────────────────────────────────────
    ("Pirinc pilavi (sade)",            "Pilavlar", 130,  2.5, 26.0,  2.0, 0.3),
    ("Bulgur pilavi",                   "Pilavlar", 120,  3.5, 22.5,  2.0, 3.5),
    ("Nohutlu pilav",                   "Pilavlar", 140,  4.5, 25.0,  2.5, 2.0),
    ("Sehriyeli pilav",                 "Pilavlar", 135,  3.0, 26.5,  2.2, 0.4),
    ("Domatesli bulgur pilavi",         "Pilavlar", 118,  3.0, 21.0,  2.5, 3.0),
    ("Ic pilav (curuklu)",              "Pilavlar", 185,  4.0, 24.0,  8.0, 1.5),
    ("Tavuklu pilav",                   "Pilavlar", 155,  8.5, 22.0,  3.5, 0.5),
    ("Pidesiz doner pilav",             "Pilavlar", 180,  9.5, 22.5,  5.5, 0.5),
    ("Mercimekli bulgur pilavi",        "Pilavlar", 128,  5.5, 22.0,  2.0, 4.5),
    ("Kavurma pilav",                   "Pilavlar", 175, 10.0, 21.0,  5.5, 0.5),

    # ── MAKARNA ─────────────────────────────────────────────────────────────
    ("Makarna (haslama, sade)",         "Makarna",  155,  5.5, 30.5,  1.0, 1.5),
    ("Makarna (kiymali sos)",           "Makarna",  175,  9.5, 22.5,  5.5, 1.8),
    ("Makarna (domates soslu)",         "Makarna",  150,  5.0, 27.5,  2.5, 2.0),
    ("Makarna (beyaz soslu)",           "Makarna",  190,  6.5, 24.5,  8.0, 0.8),
    ("Manti (pismis, yogurtlu)",        "Makarna",  195,  9.0, 25.5,  6.5, 1.0),
    ("Manti (pismis, sade)",            "Makarna",  155,  6.5, 25.5,  3.0, 1.0),
    ("Eriste (ev yapimi)",              "Makarna",  165,  5.5, 30.0,  2.5, 2.0),

    # ── ET YEMEKLERİ ────────────────────────────────────────────────────────
    ("Kofte (izgara)",                  "Et Yemekleri", 230, 18.0,  5.0, 15.0, 0.3),
    ("Kofte (pismis, ortalama)",        "Et Yemekleri", 220, 17.0,  6.0, 14.0, 0.5),
    ("Izmir koftesi",                   "Et Yemekleri", 195, 14.0,  8.5, 11.5, 1.0),
    ("Et sote",                         "Et Yemekleri", 185, 16.0,  4.0, 11.0, 1.2),
    ("Kuzu guvec",                      "Et Yemekleri", 195, 15.0,  8.0, 11.0, 2.0),
    ("Dana kavurma",                    "Et Yemekleri", 220, 18.0,  2.0, 15.0, 0.5),
    ("Tas kebabi",                      "Et Yemekleri", 170, 14.0,  7.0,  9.5, 1.5),
    ("Et haslama",                      "Et Yemekleri", 165, 16.5,  1.0, 10.0, 0.0),
    ("Kuzu pirzola (pismis)",           "Et Yemekleri", 260, 20.0,  0.0, 20.0, 0.0),
    ("Dana biftek (pismis)",            "Et Yemekleri", 245, 26.0,  0.0, 15.0, 0.0),
    ("Adana kebabi",                    "Et Yemekleri", 265, 19.0,  3.0, 20.0, 0.5),
    ("Urfa kebabi",                     "Et Yemekleri", 250, 18.0,  3.5, 18.5, 0.5),
    ("Sis kebabi (kuzu)",               "Et Yemekleri", 220, 19.0,  2.0, 15.0, 0.3),
    ("Doner kebabi (dana/kuzulu)",      "Et Yemekleri", 235, 18.0,  4.0, 16.0, 0.2),
    ("Iskender kebabi",                 "Et Yemekleri", 220, 14.0, 15.0, 12.0, 0.8),
    ("Hunkar begendi",                  "Et Yemekleri", 185, 12.0, 10.0, 11.0, 2.5),
    ("Karniyarik (etli)",               "Et Yemekleri", 155,  9.0, 10.5,  9.0, 3.0),
    ("Dana haslama",                    "Et Yemekleri", 180, 22.0,  0.5, 10.0, 0.0),
    ("Kuzu haslama",                    "Et Yemekleri", 195, 19.5,  0.5, 13.0, 0.0),
    ("Beyin tava",                      "Et Yemekleri", 165, 10.5,  5.0, 12.0, 0.0),
    ("Ciger tava (kuzu)",               "Et Yemekleri", 195, 22.0,  5.0, 10.0, 0.0),
    ("Etli yaprak sarma",               "Et Yemekleri", 160,  8.5, 15.5,  7.5, 1.5),
    ("Etli biber dolmasi",              "Et Yemekleri", 135,  7.5, 12.0,  6.0, 2.0),
    ("Etli lahana dolmasi",             "Et Yemekleri", 140,  8.0, 12.5,  6.5, 2.5),
    ("Patlican musakka",                "Et Yemekleri", 140,  8.5,  9.0,  8.0, 2.5),
    ("Firinda kofte",                   "Et Yemekleri", 210, 16.5,  6.5, 13.0, 0.8),
    ("Tekirdag koftesi",                "Et Yemekleri", 245, 19.0,  5.5, 16.5, 0.3),
    ("Kiyma (sotelenmiş)",             "Et Yemekleri", 200, 17.0,  2.5, 14.0, 0.0),

    # ── TAVUK YEMEKLERİ ─────────────────────────────────────────────────────
    ("Doner kebabi (tavuklu)",          "Tavuk Yemekleri", 185, 17.0,  3.5, 11.5, 0.2),
    ("Tavuk kavurma",                   "Tavuk Yemekleri", 195, 20.0,  2.5, 11.5, 0.5),
    ("Tavuk sote",                      "Tavuk Yemekleri", 165, 19.5,  3.5,  8.0, 0.8),
    ("Firin tavuk",                     "Tavuk Yemekleri", 175, 22.0,  1.5,  9.0, 0.0),
    ("Tavuk haslama",                   "Tavuk Yemekleri", 155, 23.0,  0.5,  6.5, 0.0),
    ("Tavuk sis",                       "Tavuk Yemekleri", 175, 20.5,  2.0,  9.5, 0.3),
    ("Tavuk guvec",                     "Tavuk Yemekleri", 160, 18.0,  6.5,  7.0, 1.5),
    ("Kizarmis tavuk",                  "Tavuk Yemekleri", 265, 20.0,  8.0, 17.0, 0.3),
    ("Tavuk baget (pismis)",            "Tavuk Yemekleri", 185, 21.5,  0.0, 11.0, 0.0),
    ("Tavuk gogus (haslama)",           "Tavuk Yemekleri", 125, 26.0,  0.5,  2.0, 0.0),
    ("Tavuk gogus (firin)",             "Tavuk Yemekleri", 155, 24.5,  1.5,  5.5, 0.0),
    ("Tavuk kanat (pismis)",            "Tavuk Yemekleri", 220, 19.0,  0.5, 16.0, 0.0),
    ("Circir tavuk (sis)",              "Tavuk Yemekleri", 180, 20.0,  3.0, 10.0, 0.5),

    # ── BALIKLAR ────────────────────────────────────────────────────────────
    ("Izgara levrek",                   "Balik",     140, 22.5,  0.0,  5.5, 0.0),
    ("Izgara cupra",                    "Balik",     155, 21.0,  0.0,  8.0, 0.0),
    ("Izgara hamsi",                    "Balik",     175, 19.5,  0.0, 11.0, 0.0),
    ("Hamsi tava",                      "Balik",     210, 18.5,  5.5, 12.5, 0.5),
    ("Izgara palamut",                  "Balik",     185, 21.0,  0.0, 11.5, 0.0),
    ("Izgara uskumru",                  "Balik",     195, 19.5,  0.5, 12.5, 0.0),
    ("Kilic sis",                       "Balik",     180, 22.0,  1.0,  9.5, 0.0),
    ("Midye dolma (pismis)",            "Balik",     190, 10.0, 22.5,  6.0, 1.5),
    ("Karides sote",                    "Balik",     120, 18.5,  2.5,  4.0, 0.0),
    ("Balik (haslama, genel)",          "Balik",     130, 21.0,  0.0,  5.0, 0.0),
    ("Ton baligi (konserve, su)",       "Balik",     110, 25.0,  0.0,  1.0, 0.0),
    ("Ton baligi (konserve, yag)",      "Balik",     185, 22.0,  0.0, 11.0, 0.0),
    ("Sardalye (konserve)",             "Balik",     210, 22.5,  0.0, 13.0, 0.0),

    # ── SEBZE YEMEKLERİ ─────────────────────────────────────────────────────
    ("Kuru fasulye yemegi (pismis)",    "Sebze Yemekleri", 110,  7.5, 17.0,  0.8, 6.5),
    ("Mercimek yemegi (pismis)",        "Sebze Yemekleri", 105,  7.0, 16.5,  0.5, 5.5),
    ("Nohut yemegi (pismis)",           "Sebze Yemekleri", 120,  7.0, 18.5,  1.5, 6.0),
    ("Barbunya pilaki",                 "Sebze Yemekleri", 115,  6.5, 16.0,  2.5, 5.0),
    ("Zeytinyagli fasulye",             "Sebze Yemekleri",  95,  3.5, 10.5,  4.0, 3.5),
    ("Zeytinyagli enginar",             "Sebze Yemekleri",  85,  2.0,  8.0,  4.5, 4.0),
    ("Zeytinyagli kereviz",             "Sebze Yemekleri",  78,  1.5,  9.5,  3.5, 2.5),
    ("Zeytinyagli biber dolmasi",       "Sebze Yemekleri",  95,  2.0, 12.5,  4.0, 2.0),
    ("Imam bayildi",                    "Sebze Yemekleri", 120,  1.8,  9.0,  8.5, 3.0),
    ("Turlu (sebze guvec)",             "Sebze Yemekleri",  85,  2.5, 11.5,  3.5, 3.0),
    ("Taze fasulye yemegi (pismis)",    "Sebze Yemekleri",  65,  2.0,  9.5,  1.5, 3.5),
    ("Ispanak yemegi",                  "Sebze Yemekleri",  75,  3.5,  5.5,  4.0, 2.5),
    ("Kapuska (lahana yemegi)",         "Sebze Yemekleri",  70,  3.0,  8.0,  2.5, 3.0),
    ("Semizotu yemegi",                 "Sebze Yemekleri",  60,  2.0,  5.5,  3.0, 1.8),
    ("Patlican yemegi (zeytinyagli)",   "Sebze Yemekleri", 105,  1.5,  8.5,  7.0, 3.5),
    ("Kabak yemegi",                    "Sebze Yemekleri",  70,  2.5,  9.5,  2.5, 2.0),
    ("Bamya yemegi",                    "Sebze Yemekleri",  80,  3.0, 10.0,  2.5, 3.5),
    ("Pirasa yemegi",                   "Sebze Yemekleri",  85,  2.5, 11.0,  3.0, 2.5),
    ("Havuc yemegi",                    "Sebze Yemekleri",  90,  1.8, 14.5,  2.5, 3.0),
    ("Patates yemegi (sulu)",           "Sebze Yemekleri",  90,  2.5, 15.0,  2.5, 2.0),
    ("Patates kizartmasi",              "Sebze Yemekleri", 312,  3.5, 41.0, 15.0, 3.5),
    ("Haslanmis patates",               "Sebze Yemekleri",  78,  2.0, 17.0,  0.2, 1.8),
    ("Firin patates",                   "Sebze Yemekleri",  88,  2.2, 18.5,  0.5, 2.0),
    ("Piyaz",                           "Sebze Yemekleri", 130,  5.5, 16.0,  4.5, 5.0),
    ("Zeytinyagli pirasa",              "Sebze Yemekleri",  78,  1.5, 10.0,  3.5, 2.5),
    ("Muhlama (misir unlu)",            "Sebze Yemekleri", 290,  8.5, 20.0, 19.5, 0.5),
    ("Mısır (haslama)",                 "Sebze Yemekleri",  86,  3.2, 19.0,  1.2, 2.0),

    # ── BÖREKLER VE HAMUR İŞLERİ ────────────────────────────────────────────
    ("Su boregi (peynirli)",            "Borek ve Hamur Isleri", 240,  9.0, 25.0, 11.5, 0.8),
    ("Kol boregi (peynirli)",           "Borek ve Hamur Isleri", 310, 10.0, 30.0, 16.0, 1.0),
    ("Sigara boregi (peynirli)",        "Borek ve Hamur Isleri", 290,  9.5, 28.0, 15.0, 0.8),
    ("Gozleme (peynirli)",              "Borek ve Hamur Isleri", 265,  9.5, 32.0, 11.0, 1.2),
    ("Gozleme (kiymali)",               "Borek ve Hamur Isleri", 278, 11.5, 31.0, 12.0, 1.0),
    ("Gozleme (patatesli)",             "Borek ve Hamur Isleri", 240,  6.5, 35.0,  8.5, 2.0),
    ("Gozleme (ispanakli)",             "Borek ve Hamur Isleri", 230,  8.5, 30.0, 10.5, 2.5),
    ("Pogaca (sade)",                   "Borek ve Hamur Isleri", 320,  8.0, 42.0, 13.0, 1.5),
    ("Pogaca (peynirli)",               "Borek ve Hamur Isleri", 330, 10.0, 40.0, 14.0, 1.2),
    ("Acma",                            "Borek ve Hamur Isleri", 290,  7.5, 42.0, 10.0, 1.5),
    ("Simit",                           "Borek ve Hamur Isleri", 280,  8.5, 53.0,  3.5, 2.5),
    ("Pide (sade)",                     "Borek ve Hamur Isleri", 250,  8.0, 47.0,  2.5, 2.0),
    ("Pide (kasarli)",                  "Borek ve Hamur Isleri", 290, 13.5, 38.0,  9.5, 1.5),
    ("Pide (sucuklu)",                  "Borek ve Hamur Isleri", 320, 14.0, 38.5, 12.5, 1.5),
    ("Pide (kiymali)",                  "Borek ve Hamur Isleri", 260, 11.5, 32.0,  9.5, 1.5),
    ("Lahmacun",                        "Borek ve Hamur Isleri", 275, 12.0, 35.0,  9.0, 1.5),
    ("Borek (ispanakli)",               "Borek ve Hamur Isleri", 230,  7.5, 26.0, 11.0, 2.0),
    ("Borek (patatesli)",               "Borek ve Hamur Isleri", 215,  5.5, 29.5,  9.0, 2.0),
    ("Cig borek",                       "Borek ve Hamur Isleri", 295, 12.5, 31.0, 13.5, 1.5),
    ("Katmer (sade)",                   "Borek ve Hamur Isleri", 340,  7.5, 50.0, 13.0, 1.5),
    ("Bazlama",                         "Borek ve Hamur Isleri", 260,  8.0, 50.0,  3.0, 2.0),

    # ── EKMEKLER ────────────────────────────────────────────────────────────
    ("Beyaz ekmek",                     "Ekmekler", 265,  9.0, 52.0,  2.5, 2.5),
    ("Kepekli ekmek",                   "Ekmekler", 245,  9.5, 48.0,  2.5, 6.5),
    ("Tam bugday ekmegi",               "Ekmekler", 252, 10.5, 48.5,  2.8, 7.5),
    ("Cavdar ekmegi",                   "Ekmekler", 258,  8.5, 50.0,  2.5, 6.0),
    ("Lavas",                           "Ekmekler", 270,  8.5, 53.0,  2.5, 2.5),
    ("Yufka",                           "Ekmekler", 360, 10.0, 72.0,  3.5, 2.5),
    ("Mısır ekmegi",                    "Ekmekler", 250,  6.5, 50.0,  3.5, 3.5),
    ("Somun ekmegi",                    "Ekmekler", 268,  9.0, 52.5,  2.5, 2.5),
    ("Pide (sade, tandır)",             "Ekmekler", 255,  8.5, 49.5,  2.8, 2.0),

    # ── KAHVALTI ────────────────────────────────────────────────────────────
    ("Beyaz peynir (olgun)",            "Kahvalti",  245, 16.0,  2.5, 19.0, 0.0),
    ("Beyaz peynir (taze)",             "Kahvalti",  200, 14.5,  2.0, 15.5, 0.0),
    ("Kasar peyniri",                   "Kahvalti",  380, 25.0,  1.0, 31.0, 0.0),
    ("Lor peyniri",                     "Kahvalti",   95, 10.5,  3.5,  4.5, 0.0),
    ("Cokelek",                         "Kahvalti",   70, 12.0,  2.0,  1.5, 0.0),
    ("Tulum peyniri",                   "Kahvalti",  285, 20.0,  2.5, 22.0, 0.0),
    ("Cerkez peyniri",                  "Kahvalti",  320, 22.0,  2.0, 25.0, 0.0),
    ("Dil peyniri",                     "Kahvalti",  260, 20.0,  1.5, 20.0, 0.0),
    ("Sucuk",                           "Kahvalti",  450, 22.0,  2.0, 38.5, 0.0),
    ("Pastirma",                        "Kahvalti",  295, 30.5,  1.5, 18.5, 0.0),
    ("Salam (Turk)",                    "Kahvalti",  285, 14.0,  3.5, 24.0, 0.0),
    ("Sosis",                           "Kahvalti",  305, 13.5,  4.5, 26.5, 0.0),
    ("Zeytin (siyah, salamura)",        "Kahvalti",  115,  0.8,  6.0, 10.5, 3.2),
    ("Zeytin (yesil, salamura)",        "Kahvalti",  125,  0.8,  3.5, 12.0, 2.8),
    ("Tereyagi",                        "Kahvalti",  735,  0.5,  0.5, 82.0, 0.0),
    ("Bal",                             "Kahvalti",  305,  0.3, 82.0,  0.0, 0.2),
    ("Pekmez (uzum)",                   "Kahvalti",  280,  2.5, 70.0,  0.2, 0.5),
    ("Pekmez (dut)",                    "Kahvalti",  265,  2.0, 67.5,  0.2, 0.5),
    ("Tahin",                           "Kahvalti",  595, 17.0, 21.5, 53.0, 9.5),
    ("Tahin pekmez (karisik)",          "Kahvalti",  440,  9.5, 52.0, 22.0, 4.5),
    ("Recal (genel)",                   "Kahvalti",  255,  0.5, 65.0,  0.1, 1.0),
    ("Findik ezmesi (tuzsuz)",          "Kahvalti",  628, 15.0, 17.0, 59.0, 9.5),
    ("Yumurta (haslama)",               "Kahvalti",  155, 13.0,  1.1, 11.0, 0.0),
    ("Yumurta (sahanda, tereyagi)",     "Kahvalti",  170, 12.0,  0.5, 13.5, 0.0),
    ("Menemen",                         "Kahvalti",  130,  7.5,  6.0,  8.5, 1.5),
    ("Omlet (sade)",                    "Kahvalti",  160, 11.5,  1.0, 12.5, 0.0),
    ("Sucuklu yumurta",                 "Kahvalti",  285, 17.5,  1.5, 23.5, 0.0),
    ("Kavurma (kahvalti icin)",         "Kahvalti",  310, 20.5,  2.0, 25.0, 0.0),

    # ── MEZELER VE SALATALAR ─────────────────────────────────────────────────
    ("Cacik",                           "Mezeler",   55,  2.5,  4.5,  3.0, 0.3),
    ("Haydari",                         "Mezeler",  130,  5.5,  4.5, 10.5, 0.2),
    ("Humus",                           "Mezeler",  165,  8.5, 18.0,  7.0, 5.0),
    ("Patlican salatas (kozlenm.)",     "Mezeler",   95,  1.5,  8.0,  6.0, 3.0),
    ("Mercimek koftesi",                "Mezeler",  180,  7.5, 28.0,  4.5, 5.0),
    ("Kisir",                           "Mezeler",  145,  4.0, 22.5,  4.5, 4.5),
    ("Tabule",                          "Mezeler",  120,  2.5, 16.0,  5.5, 3.0),
    ("Coban salatasi",                  "Mezeler",   45,  1.5,  7.5,  1.5, 2.0),
    ("Mevsim salatasi (zeytinyagli)",   "Mezeler",   75,  1.5,  6.0,  5.0, 2.0),
    ("Roka salatasi",                   "Mezeler",   65,  2.0,  5.5,  4.0, 1.5),
    ("Tarator (cevizli)",               "Mezeler",  185,  4.5,  8.5, 15.5, 1.5),
    ("Zeytinyagli yaprak sarma",        "Mezeler",  125,  2.5, 18.5,  5.0, 2.0),
    ("Atom (acili ezme)",               "Mezeler",   55,  1.5,  8.5,  2.0, 2.5),
    ("Acili ezme",                      "Mezeler",   48,  1.5,  8.0,  1.5, 2.5),
    ("Muhammara (cevizli biber)",       "Mezeler",  245,  6.5, 18.0, 17.5, 3.5),
    ("Patates salatasi",                "Mezeler",  120,  2.5, 16.0,  5.0, 1.8),
    ("Beyin salatasi",                  "Mezeler",  140,  9.5,  2.5, 10.5, 0.5),
    ("Deniz borulcesi (zeytinyagli)",   "Mezeler",   60,  1.8,  6.0,  3.5, 2.0),

    # ── TATLILAR ────────────────────────────────────────────────────────────
    ("Baklava (fistikli)",              "Tatlilar", 430,  6.5, 52.0, 22.0, 1.5),
    ("Baklava (cevizli)",               "Tatlilar", 415,  6.0, 52.5, 21.0, 2.0),
    ("Kadayif (firinda)",               "Tatlilar", 380,  7.0, 55.0, 15.0, 2.0),
    ("Sutlac",                          "Tatlilar", 130,  3.5, 23.5,  3.0, 0.2),
    ("Muhallebi",                       "Tatlilar", 120,  3.0, 22.0,  2.5, 0.0),
    ("Kazandibi",                       "Tatlilar", 165,  4.5, 27.5,  5.0, 0.0),
    ("Firın sutlac",                    "Tatlilar", 140,  4.0, 24.0,  3.5, 0.2),
    ("Helva (tahin)",                   "Tatlilar", 495, 11.0, 55.0, 27.0, 3.5),
    ("Helva (irmik)",                   "Tatlilar", 350,  5.0, 52.0, 14.0, 1.5),
    ("Revani",                          "Tatlilar", 340,  5.5, 56.0, 11.0, 1.0),
    ("Sekerpare",                       "Tatlilar", 360,  5.0, 58.0, 13.0, 0.8),
    ("Tulumba tatlisi",                 "Tatlilar", 385,  4.5, 60.0, 15.0, 0.5),
    ("Lokma",                           "Tatlilar", 370,  5.0, 60.0, 13.5, 0.8),
    ("Asure",                           "Tatlilar", 155,  4.0, 32.0,  2.0, 3.0),
    ("Gullac",                          "Tatlilar", 145,  4.5, 28.0,  2.5, 0.5),
    ("Lokum",                           "Tatlilar", 345,  0.5, 84.5,  0.5, 0.3),
    ("Cevizli sucuk (Antep)",           "Tatlilar", 365,  8.0, 65.0,  9.5, 3.0),
    ("Dondurma (fistikli)",             "Tatlilar", 215,  4.5, 28.5, 10.0, 0.8),
    ("Komposto (kayisi)",               "Tatlilar",  62,  0.5, 16.5,  0.1, 1.2),
    ("Hoşaf (kuru meyve)",              "Tatlilar",  85,  0.8, 22.0,  0.1, 1.5),
    ("Asure (geleneksel)",              "Tatlilar", 160,  4.5, 33.0,  2.5, 3.5),
    ("Kabak tatlisi",                   "Tatlilar", 145,  0.8, 36.5,  0.5, 2.0),
    ("Incir tatlisi",                   "Tatlilar", 195,  2.5, 40.0,  4.0, 3.5),

    # ── SÜT ÜRÜNLERİ VE YOĞURT ──────────────────────────────────────────────
    ("Yogurt (tam yagliı)",             "Sut Urunleri",  62,  3.5,  5.0,  3.3, 0.0),
    ("Yogurt (yagsiz)",                 "Sut Urunleri",  40,  4.0,  5.5,  0.5, 0.0),
    ("Yogurt (meyveli)",                "Sut Urunleri",  85,  3.0, 14.5,  1.5, 0.2),
    ("Ayran",                           "Sut Urunleri",  35,  2.2,  3.8,  1.0, 0.0),
    ("Kefir (tam yagliı)",              "Sut Urunleri",  62,  3.3,  4.8,  3.5, 0.0),
    ("Sut (tam yagliı, %3.5)",          "Sut Urunleri",  65,  3.3,  4.8,  3.6, 0.0),
    ("Sut (yarim yagliı, %1.5)",        "Sut Urunleri",  46,  3.3,  5.0,  1.5, 0.0),
    ("Sut (yagsiz)",                    "Sut Urunleri",  34,  3.4,  5.0,  0.1, 0.0),
    ("Kaymak",                          "Sut Urunleri", 338,  2.5,  3.0, 35.0, 0.0),

    # ── İÇECEKLER ────────────────────────────────────────────────────────────
    ("Cay (sutsuz, sade)",              "Icecekler",   1,  0.0,  0.2,  0.0, 0.0),
    ("Turk kahvesi (sekersiz)",         "Icecekler",   5,  0.3,  0.5,  0.2, 0.0),
    ("Turk kahvesi (sekerli, 1 fink.)", "Icecekler",  40,  0.3,  9.5,  0.2, 0.0),
    ("Salep",                           "Icecekler",  90,  2.5, 18.0,  1.5, 0.0),
    ("Boza",                            "Icecekler",  70,  0.8, 15.5,  0.5, 0.8),
    ("Limonata (ev yapimi)",            "Icecekler",  35,  0.2,  9.0,  0.0, 0.1),
    ("Salgam suyu",                     "Icecekler",  18,  0.8,  3.5,  0.1, 0.5),
    ("Nane limon (bitki cay)",          "Icecekler",   3,  0.1,  0.6,  0.0, 0.0),
    ("Ihlamur (bitki cay)",             "Icecekler",   2,  0.1,  0.4,  0.0, 0.0),
    ("Adacayi (bitki cay)",             "Icecekler",   2,  0.1,  0.4,  0.0, 0.0),

    # ── KURUYEMIŞLER ─────────────────────────────────────────────────────────
    ("Fistik (Antep, kavrulmus)",       "Kuruyemisler", 568, 20.5, 27.0, 46.5, 8.5),
    ("Ceviz (ic)",                      "Kuruyemisler", 655, 15.0, 13.5, 65.5, 7.0),
    ("Badem (kavrulmus)",               "Kuruyemisler", 589, 21.5, 22.0, 51.5, 12.5),
    ("Findik (kavrulmus)",              "Kuruyemisler", 628, 14.5, 17.0, 59.0, 9.5),
    ("Leblebi (nohut, kavrulmus)",      "Kuruyemisler", 355, 18.0, 54.0,  5.0, 7.5),
    ("Cekirdek (gunebakan, kavrulm.)",  "Kuruyemisler", 582, 20.5, 20.0, 50.0, 8.5),
    ("Kuru uzum",                       "Kuruyemisler", 300,  2.5, 78.0,  0.5, 3.5),
    ("Kuru kayisi",                     "Kuruyemisler", 241,  3.5, 62.5,  0.5, 7.5),
    ("Kuru incir",                      "Kuruyemisler", 249,  3.5, 63.5,  1.0, 9.5),
    ("Kuru erik",                       "Kuruyemisler", 240,  2.0, 63.5,  0.5, 7.0),

    # ── FAST FOOD / SOKAK YEMEKLERİ ─────────────────────────────────────────
    ("Doner durum (tavuklu)",           "Sokak Yemekleri", 235, 14.5, 28.5,  7.0, 2.0),
    ("Doner durum (etli)",              "Sokak Yemekleri", 265, 15.0, 29.0,  9.5, 2.0),
    ("Kofte durum",                     "Sokak Yemekleri", 248, 13.5, 28.0,  8.5, 2.0),
    ("Lahmacun durum",                  "Sokak Yemekleri", 220, 10.5, 29.5,  7.0, 2.5),
    ("Midye dolma (1 adet, ~30g)",      "Sokak Yemekleri",  57,  3.5,  9.0,  1.0, 0.5),
    ("Kumpir (sade, 100g)",             "Sokak Yemekleri", 120,  3.0, 22.5,  2.5, 2.5),
    ("Islak burger",                    "Sokak Yemekleri", 275, 11.5, 30.5, 12.5, 1.5),
    ("Tost (kasar, domates)",           "Sokak Yemekleri", 280, 12.5, 30.0, 12.0, 1.5),
    ("Kumpir (butun, 400g tah.)",       "Sokak Yemekleri", 480, 12.0, 90.0, 10.0, 9.0),

    # ── BAHARATLİ / FERMANTE ─────────────────────────────────────────────────
    ("Tursu (karisik, salamura)",       "Fermante",   15,  0.8,  2.5,  0.2, 1.5),
    ("Lahana tursusu",                  "Fermante",   18,  1.0,  3.5,  0.2, 1.8),
    ("Biber tursusu",                   "Fermante",   22,  1.0,  4.5,  0.3, 1.5),
    ("Tarhana (kuru)",                  "Fermante",  355, 14.5, 68.0,  3.5, 5.5),
    ("Biberiye (baharatı)",             "Baharat",   331,  4.9, 64.0, 15.0, 43.0),
    ("Nane (taze)",                     "Baharat",    44,  3.7,  8.5,  0.7,  8.0),

    # ── YAĞLAR ──────────────────────────────────────────────────────────────
    ("Zeytinyagi",                      "Yaglar",    884,  0.0,  0.0, 100.0, 0.0),
    ("Aycicek yagi",                    "Yaglar",    884,  0.0,  0.0, 100.0, 0.0),
    ("Margarin",                        "Yaglar",    720,  0.2,  0.5,  79.0, 0.0),
    ("Tereyagi (tuzsuz)",               "Yaglar",    735,  0.5,  0.5,  82.0, 0.0),
    ("Misir yagi",                      "Yaglar",    884,  0.0,  0.0, 100.0, 0.0),
    ("Hindistan cevizi yagi",           "Yaglar",    862,  0.0,  0.0,  95.0, 0.0),

    # ── TAHILLAR VE BAKLIYATLAR ─────────────────────────────────────────────
    ("Bulgur (pismis)",                 "Tahillar",   83,  3.0, 18.5,  0.2, 4.5),
    ("Pirinc (pismis, beyaz)",          "Tahillar",  130,  2.7, 28.2,  0.3, 0.4),
    ("Arpa (pismis)",                   "Tahillar",   88,  2.3, 19.5,  0.4, 4.5),
    ("Yulaf (pismis)",                  "Tahillar",   68,  2.4, 12.0,  1.4, 1.7),
    ("Kuru fasulye (pismis)",           "Tahillar",  110,  7.5, 17.0,  0.8, 6.5),
    ("Kirmizi mercimek (pismis)",       "Tahillar",  105,  7.0, 16.5,  0.5, 5.5),
    ("Yesil mercimek (pismis)",         "Tahillar",  116,  9.0, 20.0,  0.4, 7.5),
    ("Nohut (pismis)",                  "Tahillar",  120,  7.0, 18.5,  1.5, 6.0),
    ("Barbunya (pismis)",               "Tahillar",  112,  7.5, 18.5,  0.5, 6.0),
    ("Bakla (pismis)",                  "Tahillar",  110,  7.5, 18.0,  0.6, 6.5),
    ("Bezelye (pismis)",                "Tahillar",   84,  5.4, 15.0,  0.4, 5.5),
]


def build():
    rows = []
    for i, (name, cat, kcal, prot, carb, fat, fib) in enumerate(FOODS, start=1):
        rows.append({
            'fdc_id':    9_000_000 + i,   # USDA ile cakismasin
            'name':      name,
            'category':  cat,
            'data_type': 'turkish_food',
            'kcal':      kcal,
            'protein_g': prot,
            'carb_g':    carb,
            'fat_g':     fat,
            'fiber_g':   fib,
        })

    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['fdc_id','name','category','data_type',
                                          'kcal','protein_g','carb_g','fat_g','fiber_g'])
        w.writeheader()
        w.writerows(rows)

    print("Kaydedildi: %s" % OUT)
    print("Toplam: %d Turk yemegi" % len(rows))

    # Kategori ozeti
    cats = {}
    for r in rows:
        cats[r['category']] = cats.get(r['category'], 0) + 1
    print("\nKategori dagilimi:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print("  %-35s %d" % (c, n))


if __name__ == '__main__':
    build()
