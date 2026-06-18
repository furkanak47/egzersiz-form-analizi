#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tez PDF Oluşturucu v2 — ReportLab, Times New Roman, BUÜ logosu dahil
"""

import html
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
pt = 1.0  # 1 point = 1 ReportLab unit
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import black, white, HexColor, Color
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak, KeepTogether,
    NextPageTemplate, HRFlowable, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import KeepInFrame

# ── Font kaydı ────────────────────────────────────────────────────────────────

FONT_DIR = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('TNR',     FONT_DIR + r'\times.ttf'))
pdfmetrics.registerFont(TTFont('TNR-B',   FONT_DIR + r'\timesbd.ttf'))
pdfmetrics.registerFont(TTFont('TNR-I',   FONT_DIR + r'\timesi.ttf'))
pdfmetrics.registerFont(TTFont('TNR-BI',  FONT_DIR + r'\timesbi.ttf'))
pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-B',
                               italic='TNR-I', boldItalic='TNR-BI')

OUTPUT = r'C:\Users\Furkan\Desktop\egzersiz-form-analizi\tez_dosyalari\TEZ_Furkan_Akdemir.pdf'
LOGO   = r'C:\Users\Furkan\Desktop\egzersiz-form-analizi\tez_dosyalari\buu_logo.png'

# ── Sayfa düzeni ──────────────────────────────────────────────────────────────

W, H     = A4
ML       = 3.5*cm   # sol kenar
MR       = 2.5*cm   # sağ kenar
MT       = 2.5*cm   # üst kenar
MB       = 2.5*cm   # alt kenar
FW       = W - ML - MR
FH       = H - MT - MB

# ── Sayfa numarası izleme ─────────────────────────────────────────────────────

roman_start  = [None]
arabic_start = [None]
ROMAN = {1:'i',2:'ii',3:'iii',4:'iv',5:'v',6:'vi',7:'vii',8:'viii'}

def _footer(canvas, text):
    canvas.saveState()
    canvas.setFont('TNR', 12)
    canvas.drawCentredString(W/2, 1.5*cm, text)
    canvas.restoreState()

def on_cover(canvas, doc):
    pass

def on_roman(canvas, doc):
    if roman_start[0] is None:
        roman_start[0] = doc.page
    n = doc.page - roman_start[0] + 1
    _footer(canvas, ROMAN.get(n, str(n)))

def on_arabic(canvas, doc):
    if arabic_start[0] is None:
        arabic_start[0] = doc.page
    n = doc.page - arabic_start[0] + 1
    _footer(canvas, str(n))

# ── Belge şablonu ─────────────────────────────────────────────────────────────

def build_doc():
    doc = BaseDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB,
        allowSplitting=1,
        title='Egzersiz Form Analizi — Furkan Akdemir',
        author='Furkan Akdemir',
    )

    body_frame = Frame(ML, MB, FW, FH, id='body', showBoundary=0)

    doc.addPageTemplates([
        PageTemplate(id='Cover',  frames=body_frame, onPage=on_cover),
        PageTemplate(id='Roman',  frames=body_frame, onPage=on_roman),
        PageTemplate(id='Arabic', frames=body_frame, onPage=on_arabic),
    ])
    return doc

# ── Stiller ───────────────────────────────────────────────────────────────────

LINE = 18   # 12pt * 1.5 = 18pt leading

S = lambda **kw: ParagraphStyle('_', **kw)

normal = S(fontName='TNR', fontSize=12, leading=LINE,
           alignment=TA_JUSTIFY, spaceAfter=LINE, spaceBefore=0,
           leftIndent=0, firstLineIndent=0)

normal_left = S(fontName='TNR', fontSize=12, leading=LINE,
                alignment=TA_LEFT, spaceAfter=LINE, spaceBefore=0)

cover_uni = S(fontName='TNR-B', fontSize=13, leading=20,
              alignment=TA_CENTER, spaceAfter=4)

cover_title = S(fontName='TNR-B', fontSize=18, leading=26,
                alignment=TA_CENTER, spaceAfter=8)

cover_small = S(fontName='TNR', fontSize=12, leading=LINE,
                alignment=TA_CENTER, spaceAfter=4)

h1_style = S(fontName='TNR-B', fontSize=14, leading=21,
             alignment=TA_CENTER, spaceAfter=LINE, spaceBefore=LINE,
             textTransform='uppercase')

h2_style = S(fontName='TNR-B', fontSize=12, leading=LINE,
             alignment=TA_LEFT, spaceAfter=6, spaceBefore=LINE,
             leftIndent=0.4*cm)

toc_main = S(fontName='TNR-B', fontSize=12, leading=LINE,
             alignment=TA_LEFT, spaceAfter=2, spaceBefore=2)

toc_sub = S(fontName='TNR', fontSize=12, leading=LINE,
            alignment=TA_LEFT, spaceAfter=1, spaceBefore=1,
            leftIndent=0.8*cm)

table_hdr = S(fontName='TNR-B', fontSize=10, leading=14,
              alignment=TA_CENTER)

table_cell = S(fontName='TNR', fontSize=10, leading=14,
               alignment=TA_CENTER)

table_cell_l = S(fontName='TNR', fontSize=10, leading=14,
                 alignment=TA_LEFT)

caption_style = S(fontName='TNR', fontSize=12, leading=LINE,
                  alignment=TA_LEFT, spaceAfter=4, spaceBefore=LINE)

ref_style = S(fontName='TNR', fontSize=12, leading=LINE,
              alignment=TA_JUSTIFY, spaceAfter=10, spaceBefore=0,
              leftIndent=1.0*cm, firstLineIndent=-1.0*cm)

ek_body = S(fontName='TNR', fontSize=11, leading=16,
            alignment=TA_JUSTIFY, spaceAfter=8, spaceBefore=0)

ozet_title = S(fontName='TNR-B', fontSize=12, leading=LINE,
               alignment=TA_CENTER, spaceAfter=LINE)

h3_style = S(fontName='TNR-B', fontSize=12, leading=LINE,
             alignment=TA_LEFT, spaceAfter=4, spaceBefore=LINE,
             leftIndent=0.8*cm)

fig_caption = S(fontName='TNR', fontSize=11, leading=15,
                alignment=TA_CENTER, spaceAfter=LINE, spaceBefore=4)

# ── Yardımcı ─────────────────────────────────────────────────────────────────

def E(text):
    """HTML escape — & < > karakterlerini koru."""
    return html.escape(str(text), quote=False)

def P(text, style=None):
    if style is None:
        style = normal
    return Paragraph(E(text), style)

def SP(h=LINE):
    return Spacer(1, h)

def page_break():
    return PageBreak()

def section_break(template_name):
    return [NextPageTemplate(template_name), PageBreak()]

def H1(text):
    return Paragraph(E(text), h1_style)

def H2(text):
    return Paragraph(E(text), h2_style)

def H3(text):
    return Paragraph(E(text), h3_style)

def make_fig(fig_no, caption_text, content_elements):
    """Şekil başlıklı blok — içerik ortalanmış, başlık altında."""
    elems = [SP(LINE)]
    elems.extend(content_elements)
    elems.append(Paragraph(f'<b>Şekil {fig_no}.</b> {E(caption_text)}', fig_caption))
    elems.append(SP(LINE))
    return elems

def box_row(labels, widths, bg='#F0F4F8'):
    """Tek satır kutu — blok diyagram için."""
    data = [[Paragraph(f'<b>{E(l)}</b>', S(fontName='TNR-B', fontSize=9, leading=12,
             alignment=TA_CENTER)) for l in labels]]
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor(bg)),
        ('BOX',        (0,0), (-1,-1), 1.0, HexColor('#336699')),
        ('INNERGRID',  (0,0), (-1,-1), 0.5, HexColor('#336699')),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    return t

def make_tbl(caption_text, headers, rows, col_widths=None):
    """Başlıklı, kenarlıklı tablo."""
    data = [[Paragraph(E(h), table_hdr) for h in headers]]
    for row in rows:
        data_row = []
        for ci, cell in enumerate(row):
            st = table_cell_l if ci == 0 else table_cell
            data_row.append(Paragraph(E(str(cell)), st))
        data.append(data_row)

    if col_widths is None:
        col_widths = [FW / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  HexColor('#E8E8E8')),
        ('TEXTCOLOR',    (0,0), (-1,0),  black),
        ('FONTNAME',     (0,0), (-1,0),  'TNR-B'),
        ('FONTSIZE',     (0,0), (-1,0),  10),
        ('FONTNAME',     (0,1), (-1,-1), 'TNR'),
        ('FONTSIZE',     (0,1), (-1,-1), 10),
        ('GRID',         (0,0), (-1,-1), 0.5, black),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [white, HexColor('#F8F8F8')]),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
        ('LEFTPADDING',  (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))

    elements = [SP(LINE)]
    if caption_text:
        elements.append(Paragraph(E(caption_text), caption_style))
    elements.append(t)
    elements.append(SP(LINE))
    return elements

def toc_entry(label, pg, level=0):
    style = toc_main if level == 0 else toc_sub
    p = Paragraph(
        f'<font name="TNR-B">{E(label)}</font>'
        + ' ' * 3
        + f'<font name="TNR">{"." * 60}</font>'
        + f' <font name="TNR">{pg}</font>',
        style
    )
    return p

# ── İÇERİK ───────────────────────────────────────────────────────────────────

story = []


# ══════════════════════════════════════════════════════════════════════════════
# KAPAK
# ══════════════════════════════════════════════════════════════════════════════

story.append(NextPageTemplate('Cover'))

cover_items = [
    SP(1.0*cm),
    Image(LOGO, width=3.2*cm, height=3.2*cm),
    SP(0.2*cm),
    Paragraph('BURSA ULUDAĞ ÜNİVERSİTESİ', cover_uni),
    Paragraph('İNEGÖL İŞLETME FAKÜLTESİ', cover_uni),
    Paragraph('YÖNETİM BİLİŞİM SİSTEMLERİ BÖLÜMÜ', cover_uni),
    SP(2.0*cm),
    Paragraph(
        'BİLGİSAYARLI GÖRÜ VE MAKİNE ÖĞRENMESİ TABANLI<br/>'
        'GERÇEK ZAMANLI EGZERSİZ FORM ANALİZİ VE<br/>'
        'KİŞİSEL PERFORMANS REHBERLİK SİSTEMİ',
        cover_title),
    SP(2.0*cm),
    Paragraph('LİSANS TEZİ', cover_small),
    SP(1.5*cm),
    Paragraph('Furkan AKDEMİR', cover_small),
    Paragraph('132230044', cover_small),
    SP(1.5*cm),
    Paragraph('Danışman: Prof. Dr. Melih ENGİN', cover_small),
    SP(2.0*cm),
    Paragraph('Bursa, 2026', cover_small),
]
story.append(KeepInFrame(FW, FH, cover_items, mode='shrink'))

# ══════════════════════════════════════════════════════════════════════════════
# ÖN MATTER — Roman rakamları
# ══════════════════════════════════════════════════════════════════════════════

story += section_break('Roman')

# ── ÖZET ─────────────────────────────────────────────────────────────────────

story.append(H1('ÖZET'))
story.append(Paragraph(
    'Bilgisayarlı Görü ve Makine Öğrenmesi Tabanlı Gerçek Zamanlı Egzersiz Form\n'
    'Analizi ve Kişisel Performans Rehberlik Sistemi',
    ozet_title))

story.append(P(
    'Bu çalışmada egzersiz yapan bireylerin hareket kalitesini profesyonel bir antrenöre '
    'başvurmadan gerçek zamanlı izleyip geliştirebilmelerine olanak tanıyan, veri odaklı '
    've modüler bir bilgisayarlı görü sistemi tasarlanmış ve Python ekosistemi üzerinde '
    'çalışır hâle getirilmiştir. Google\'ın BlazePose mimarisine dayanan MediaPipe Pose '
    'kütüphanesi, standart bir web kamerasından saniyede 30\'un üzerinde karede 33 eklem '
    'noktasını çıkarabilmekte ve GPU gerektirmemektedir; 480×270 çözünürlükte yürütülen '
    'pose işleme 1280×720 ekran çıkışıyla eş zamanlı çalışmakta, böylece görüntü donması '
    'yaşanmamaktadır. Sistem yedi birbirinden bağımsız modülden oluşmaktadır: egzersiz '
    'form analiz motorları, makine öğrenmesi sınıflandırıcısı, vücut yağ tahmini, güç '
    'profili, beslenme takibi, ilerleme kaydedicisi ve görsel/sesli geri bildirim '
    'katmanı. Veri hattı, YouTube\'dan yt-dlp ile derlenen 652 egzersiz videosunu '
    'işleyerek medyan-kesişim tabanlı adaptif tekrar tespiti yöntemiyle 19 egzersiz '
    'kategorisinde 1.139 etiketli tekrar üretmiştir. Her tekrar 40 boyutlu bir özellik '
    'vektörüyle temsil edilmektedir; bu vektör sekiz eklem açısının istatistiksel '
    'özetleri (32 özellik), sol-sağ simetri ölçütleri (4 özellik) ve hareket aralığı '
    'göstergelerinden (4 özellik) oluşmaktadır. class_weight=\'balanced\' ve '
    'n_estimators=300 ile yapılandırılan Random Forest sınıflandırıcısı 19 modelin '
    'ortalamasında yüzde 76,1 test doğruluğu sağlamıştır. Form analizinin ötesinde '
    'sistem; 74.511 kayıtlık NHANES, ANSUR II ve Kaggle verisiyle eğitilmiş, test '
    'MAE\'si 3,7 yüzde puan olan Gradient Boosting vücut yağ tahmin modeli; 1,3 milyon '
    'OpenPowerlifting yarışma kaydından türetilen güç persentil hesaplayıcısı; 455.100 '
    'USDA kaydına ek olarak 1.357 Türkiye\'ye özgü gıda kaydını barındıran beslenme '
    'takip modülü ve JSON tabanlı antrenman ilerleme kaydedicisiyle bütüncül bir '
    'performans rehberliği sunmaktadır. Tüm bileşenler tek bir uygulama çatısında '
    'birleştirilmiş; düşük donanım gereksinimi ve açık kaynak kütüphane yığını '
    'sayesinde bireysel spor senaryolarına uyarlanabilir bir ekosistem '
    'oluşturulmuştur.'))

story.append(Paragraph(
    '<b>Anahtar Kelimeler:</b> Bilgisayarlı Görü, Egzersiz Form Analizi, '
    'Makine Öğrenmesi, MediaPipe, Performans Takibi', normal_left))

# ── ABSTRACT ─────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('ABSTRACT'))
story.append(Paragraph(
    'Real-Time Exercise Form Analysis and Personal Performance Guidance System\n'
    'Based on Computer Vision and Machine Learning',
    ozet_title))

story.append(P(
    'Poor exercise technique accounts for a large share of weight-training injuries, '
    'yet qualified coaching remains out of reach for most recreational athletes due to '
    'cost and availability constraints. This thesis describes the design and '
    'implementation of a modular, data-driven computer vision platform that delivers '
    'real-time exercise form feedback via a standard laptop camera, requiring no '
    'dedicated hardware or subscription service. The system comprises seven loosely '
    'coupled modules: a rule-based form analysis engine covering 19 exercises, a '
    'machine learning classifier, a body fat estimator, a strength profiler, a '
    'nutrition tracker, a session progress recorder, and a visual/audio feedback layer; '
    'modules communicate only through a shared configuration file and JSON user records, '
    'so any single component can be disabled without breaking the rest of the '
    'application. Skeleton extraction relies on Google\'s MediaPipe Pose library '
    '(BlazePose, model_complexity=0), which outputs 33 body landmarks at over 30 frames '
    'per second; processing runs at 480x270 while display output stays at 1280x720, '
    'with PoseWorker, BodyWorker, and GestureWorker threads running concurrently to '
    'prevent frame drops. Training data was collected by downloading 652 exercise videos '
    'from YouTube using yt-dlp and automatically segmenting 1,139 labeled repetitions '
    'across 19 exercise categories via a median-crossing adaptive algorithm, without any '
    'manual frame annotation. Each repetition is encoded as a 40-dimensional feature '
    'vector — 32 statistical summaries of eight joint angles, 4 left-right symmetry '
    'metrics, and 4 motion range indicators — and classified by a Random Forest '
    '(n_estimators=300, class_weight=balanced) that averaged 76.1 percent test accuracy '
    'across 19 models. The body fat module was trained on 74,511 NHANES, ANSUR II, and '
    'Kaggle records using a Gradient Boosting Regressor pipeline and achieved a test MAE '
    'of 3.7 percentage points. The strength percentile calculator derives competition '
    'norms from 1.3 million raw OpenPowerlifting entries; the nutrition module combines '
    '455,100 USDA records with 1,357 Turkey-specific items from BEBIS and Open Food '
    'Facts. All components share a single JSON-based user profile and progress log, '
    'keeping installation dependencies minimal and enabling multi-user operation without '
    'any external database.'))

story.append(Paragraph(
    '<b>Keywords:</b> Computer Vision, Exercise Form Analysis, Machine Learning, '
    'MediaPipe, Performance Tracking', normal_left))

# ── İÇİNDEKİLER ─────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('İÇİNDEKİLER'))

toc_data = [
    ('ÖZET', 'i', 0), ('ABSTRACT', 'ii', 0),
    ('İÇİNDEKİLER', 'iii', 0),
    ('TABLOLAR', 'v', 0), ('ŞEKİLLER', 'vi', 0),
    ('1. GİRİŞ', '1', 0),
    ('    1.1. Problem Durumu ve Motivasyon', '1', 1),
    ('    1.2. Araştırma Soruları ve Hedefler', '2', 1),
    ('    1.3. Çalışmanın Kapsamı', '3', 1),
    ('2. TEORİK ARKA PLAN', '4', 0),
    ('    2.1. İnsan Pozu Tahmini', '4', 1),
    ('    2.2. BlazePose ve MediaPipe Çerçevesi', '5', 1),
    ('    2.3. Eklem Açısı Hesabı ve Biyomekanik', '6', 1),
    ('    2.4. Makine Öğrenmesi: Random Forest', '7', 1),
    ('    2.5. Vücut Kompozisyonu Tahmini', '7', 1),
    ('    2.6. Güç Normalizasyonu ve Dots Skoru', '8', 1),
    ('    2.7. Çok İş Parçacıklı Sistem Tasarımı', '9', 1),
    ('3. LİTERATÜR TARAMASI', '10', 0),
    ('4. YÖNTEM', '13', 0),
    ('    4.1. Sistem Mimarisine Genel Bakış', '13', 1),
    ('    4.2. Veri Toplama ve İşleme Pipeline\'ı', '14', 1),
    ('    4.3. İskelet Çıkarımı ve Özellik Hesaplama', '16', 1),
    ('    4.4. Kural Tabanlı Form Analiz Motorları', '17', 1),
    ('    4.5. Makine Öğrenmesi Sınıflandırıcısı', '18', 1),
    ('    4.6. Tamamlayıcı Modüller', '19', 1),
    ('        4.6.1. Vücut Yağ Tahmini', '19', 2),
    ('        4.6.2. Güç Profili ve Dots Skoru', '21', 2),
    ('        4.6.3. Beslenme Takip Modülü', '22', 2),
    ('        4.6.4. İlerleme Kaydedicisi', '23', 2),
    ('        4.6.5. Kullanıcı Profil Sistemi', '24', 2),
    ('        4.6.6. Kullanıcı Arayüzü ve Geri Bildirim', '24', 2),
    ('5. BULGULAR', '25', 0),
    ('    5.1. Veri Seti İstatistikleri', '25', 1),
    ('    5.2. Model Performans Sonuçları', '26', 1),
    ('    5.3. Sistem Performansı', '28', 1),
    ('    5.4. Vücut Yağ ve Güç Profili Değerlendirmesi', '28', 1),
    ('6. TARTIŞMA VE SONUÇ', '30', 0),
    ('    6.1. Bulgular Üzerine Değerlendirme', '30', 1),
    ('    6.2. Literatürle Karşılaştırma', '31', 1),
    ('    6.3. Sınırlılıklar', '32', 1),
    ('    6.4. Gelecek Çalışmalar', '32', 1),
    ('    6.5. Sonuç', '33', 1),
    ('KAYNAKÇA', '34', 0),
    ('EKLER', '37', 0),
]

toc_sub2 = S(fontName='TNR', fontSize=11, leading=15,
             alignment=TA_LEFT, spaceAfter=1, spaceBefore=1,
             leftIndent=1.6*cm)

for label, pg, level in toc_data:
    if level == 0:
        st = toc_main
    elif level == 1:
        st = toc_sub
    else:
        st = toc_sub2
    label_clean = label.strip()
    indent_penalty = {0: 0, 1: 8, 2: 16}.get(level, 8)
    dots = '.' * max(2, 80 - len(label_clean) - len(pg) - indent_penalty)
    story.append(Paragraph(
        f'<b>{E(label_clean)}</b> <font color="#888">{dots}</font> {E(pg)}'
        if level == 0 else
        f'{E(label_clean)} <font color="#888">{dots}</font> {E(pg)}',
        st))

# ── TABLOLAR ─────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('TABLOLAR'))

for lbl, pg in [
    ('Tablo 1. Egzersiz form analizi literatürü karşılaştırma tablosu', '12'),
    ('Tablo 2. Seçili egzersizler için analiz parametreleri', '17'),
    ('Tablo 5. Vücut yağ modeli veri kaynaklarının dağılımı', '19'),
    ('Tablo 3. Egzersiz başına veri seti istatistikleri', '25'),
    ('Tablo 4. Egzersiz modeli test doğrulukları', '26'),
]:
    dots = '.' * max(2, 75 - len(lbl) - len(pg))
    story.append(Paragraph(
        f'{E(lbl)} <font color="#888">{dots}</font> {pg}', normal_left))

# ── ŞEKİLLER ─────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('ŞEKİLLER'))

for lbl, pg in [
    ('Şekil 1. Sistem modül mimarisi — yedi bileşen ve veri akışı', '13'),
    ('Şekil 2. Veri işleme pipeline akışı — videodan CSV\'e', '15'),
    ('Şekil 3. HUD ekranı dört panel düzeni', '24'),
]:
    dots = '.' * max(2, 75 - len(lbl) - len(pg))
    story.append(Paragraph(
        f'{E(lbl)} <font color="#888">{dots}</font> {pg}', normal_left))

# ══════════════════════════════════════════════════════════════════════════════
# ANA İÇERİK — Arap rakamları
# ══════════════════════════════════════════════════════════════════════════════

story += section_break('Arabic')

# ── 1. GİRİŞ ─────────────────────────────────────────────────────────────────

story.append(H1('1. GİRİŞ'))
story.append(H2('1.1. Problem Durumu ve Motivasyon'))

story.append(P('Dünya genelinde spor salonu üyeliği sahipliği son on yılda önemli ölçüde '
    'artmış; yalnızca Avrupa\'da kayıtlı spor salonu üye sayısı 2022 itibarıyla 60 '
    'milyonu aşmıştır (EuropeActive, 2022). Bu büyüme, sağlıklı yaşam bilincinin ve '
    'egzersizin kronik hastalık riskini azaltıcı etkisine dair kanıtların giderek '
    'yaygınlaşmasıyla paralel bir seyir izlemektedir. Bununla birlikte egzersiz '
    'katılımcılarının büyük çoğunluğu amatör düzeydedir ve uygun teknikle ilgili temel '
    'eğitimden yoksundur. Amerikan Ortopedi Cerrahları Akademisi\'nin (AAOS) verilerine '
    'göre ağırlık antrenmanı kaynaklı yaralanmaların yüzde 40 ila 70\'i hatalı hareket '
    'mekaniğine bağlıdır (Kerr vd., 2010). Kişisel antrenör bu açığı kapatabilecek en '
    'etkili çözüm olmakla birlikte yüksek maliyeti, sınırlı erişimi ve fiziksel mekân '
    'bağımlılığı nedeniyle kullanıcıların büyük çoğunluğuna ulaşamamaktadır.'))

story.append(P('Öte yandan son birkaç yılda iki şey değişti. Birincisi, web kamerası '
    'artık neredeyse her dizüstü bilgisayarda standart; çözünürlük ve kare hızı '
    'açısından birkaç yıl öncesine kıyasla çok daha iyi. İkincisi, MediaPipe '
    've benzeri kütüphaneler sayesinde gerçek zamanlı iskelet tespiti artık '
    'doktora tezi değil, lisans tezi ölçeğinde yapılabilir hâle geldi. '
    'Bu çalışma tam olarak o fırsatı değerlendirmeye çalışıyor: bir Yönetim '
    'Bilişim Sistemleri öğrencisinin mevcut açık kaynak araçlarla ne kadar '
    'işlevsel bir egzersiz koçluğu sistemi kurabileceğini görmek.'))

story.append(P('Mevcut ticari alternatifler bu boşluğu ancak kısmen doldurmaktadır. '
    'Apple Watch ve Garmin gibi giyilebilir cihazlar tekrar sayma ve kalp atış hızı '
    'gibi temel metrikleri izleyebilmekte, ancak form kalitesi değerlendirmesi '
    'yapamamaktadır. Peloton ve Mirror gibi interaktif fitness platformları ise rehberli '
    'video içerik sunmakla birlikte kullanıcının bireysel biyomekaniğine uyarlanmış '
    'gerçek zamanlı düzeltme yapamamaktadır. OpenCV ve MediaPipe gibi açık kaynak '
    'araçların olgunlaşmasıyla bu boşluk artık araştırma düzeyinde değil, lisans tezi '
    'ölçeğinde bile adreslenebilecek hâle gelmiştir.'))

story.append(H2('1.2. Araştırma Soruları ve Hedefler'))

story.append(P('Bu çalışmanın temel araştırma sorusu şöyle ifade edilmektedir: Standart '
    'bir RGB kameradan elde edilen ham görüntü akışı, bir veri işleme hattı, biyomekanik '
    'kural motoru ve makine öğrenmesi sınıflandırıcısı aracılığıyla işlenerek egzersiz '
    'yapan bir bireye antrenör düzeyinde gerçek zamanlı form geri bildirimi sunulabilir '
    'mi? Bu soruyu yanıtlamak amacıyla çalışma üç alt hedef belirlemiştir.'))

story.append(P('Birinci hedef, büyük ölçekli video verisi üzerinde çalışan, insan '
    'müdahalesi gerektirmeyen otomatik bir etiketleme ve özellik çıkarma hattı '
    'tasarlamaktır. İkinci hedef, kural tabanlı anlık geri bildirim ile tekrar sonrası '
    'makine öğrenmesi tahminin bir arada çalıştığı hibrit bir form analiz mimarisi '
    'kurmak; bu sayede her iki yaklaşımın güçlü yanlarından yararlanmaktır. Üçüncü hedef '
    'ise form analizini vücut yağ tahmini, güç profili ve beslenme takibiyle '
    'bütünleştirerek kullanıcıya salt teknik düzeltmenin ötesinde kişiselleştirilmiş '
    'bir rehberlik ekosistemi sunmaktır.'))

story.append(P('Çalışma kapsamında aşağıdaki alt sorular ele alınmıştır: (1) Medyan-kesişim '
    'tabanlı adaptif tekrar tespiti, sabit açı eşiklerine dayanan geleneksel yöntemlere '
    'kıyasla farklı kamera açıları ve kullanıcı vücut oranlarında daha tutarlı sonuç '
    'üretebilir mi? (2) Egzersiz başına ortalama 60 etiketli tekrarla eğitilen Random '
    'Forest modelleri klinik düzeyde kullanılabilir bir doğruluğa ulaşabilir mi? '
    '(3) 74.511 kişilik nüfus verisiyle eğitilen vücut yağ tahmini modeli, pahalı '
    'klinik ölçüm yöntemlerine makul bir alternatif olabilir mi?'))

story.append(H2('1.3. Çalışmanın Kapsamı'))

story.append(P('Bu tez, spor salonu türü ağırlık antrenmanı egzersizleriyle sınırlıdır; '
    'kardiyovasküler egzersizler, yoga ve takım sporu hareketleri kapsam dışında '
    'tutulmuştur. Sistem, tek kullanıcılı ve kapalı mekân senaryosu için optimize '
    'edilmiştir. Veri toplama aşamasında 19 egzersiz kategorisi kullanılmış; silinmiş '
    'modeller (push_up ve russian_twist) tek sınıf sorunu nedeniyle kapsam dışına '
    'alınmıştır. Klinik doğrulama çalışması bu tezin kapsamı dışındadır; bildirilen '
    'doğruluk değerleri etiketleme sürecinde kullanılan YouTube veri setine özgüdür ve '
    'bağımsız kullanıcı testleriyle doğrulanmamıştır.'))

# ── 2. TEORİK ARKA PLAN ───────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('2. TEORİK ARKA PLAN'))
story.append(H2('2.1. İnsan Pozu Tahmini'))

story.append(P('İnsan pozu tahmini (human pose estimation), bir görüntü ya da video karesindeki '
    'vücudun eklem noktalarını — omuz, dirsek, bilek, kalça, diz, ayak bileği — piksel '
    'koordinatlarında bulmayı hedefler. Konu 1970\'lerden bu yana araştırılmaktadır; '
    'ancak alandaki asıl sıçrama, Krizhevsky vd.\'nin (2012) ImageNet yarışmasını derin '
    'evrişimli ağlarla kazanmasıyla birlikte gerçekleşmiştir. O tarihten itibaren el '
    'yapımı özellik mühendisliği yerini uçtan uca öğrenmeye bırakmıştır.'))

story.append(P('Literatürdeki yaklaşımlar iki ana kolda toplanmaktadır. Birinci kolda model '
    'her eklem için bir olasılık ısı haritası üretir; eklemin tahmini konumu bu '
    'haritanın tepe noktasından okunur. Newell vd.\'nin (2016) Yığılmış Kum Saati Ağı '
    '(Stacked Hourglass) bu yaklaşımın mihenk taşı sayılır. İkinci kolda ise ağ '
    'koordinatları doğrudan sayı olarak çıktılar; Sun vd.\'nin (2019) geliştirdiği '
    'HRNet mimarisi yüksek çözünürlüklü temsili paralel akışlarda koruyarak her iki '
    'yaklaşımın güçlü yanlarını bir araya getirmiştir.'))

story.append(H2('2.2. BlazePose ve MediaPipe Çerçevesi'))

story.append(P('BlazePose (Bazarevsky vd., 2020), Google\'ın telefon kameralarında çalışmak '
    'üzere tasarladığı hafif bir poz tahmin modelidir. Mimaride iki aşama art arda '
    'çalışır: önce dedektör kişinin varlığını ve kaba konumunu belirler; ardından '
    'landmarker bu bölgeyi kırpıp 33 eklem noktasının normalize 2D/3D koordinatlarını '
    've görünürlük skorlarını hesaplar. Görünürlük skoru 0 ile 1 arasında bir değerdir; '
    'bu çalışmada 0,4\'ün altı güvenilmez kabul edilerek hesaplamadan dışlanmıştır. '
    'MediaPipe (Lugaresi vd., 2019), BlazePose\'u ve diğer algı modellerini birbirine '
    'bağlayan açık kaynak pipeline çerçevesidir.'))

story.append(H2('2.3. Eklem Açısı Hesabı ve Biyomekanik'))

story.append(P('Bir egzersizin form kalitesini sayısallaştırmanın en doğrudan yolu eklem '
    'açılarını ölçmektir. Bu çalışmada açı, üç landmark noktasının (A, B, C) '
    'oluşturduğu vektörler arasındaki açı olarak tanımlanmaktadır: '
    'theta = arccos( (BA · BC) / (|BA| × |BC| + 1e-8) ). '
    'Epsilon terimi, landmark\'ların üst üste geldiği durumlarda sıfıra bölme '
    'hatasını önlemek için eklenmiştir. Hesaplama ilk bakışta basit görünse de '
    'gerçek zamanlı uygulamada iki sorun çıkmaktadır: birincisi, MediaPipe '
    'zaman zaman bir eklem noktasını yanlış konuma yerleştirebilmektedir; '
    'ikincisi, kullanıcının kameraya açısına bağlı olarak bazı eklemler '
    'kısmi ya da tamamen görünmez hâle gelmektedir. Visibility skoru 0,4\'ün '
    'altında kalan herhangi bir landmark içeren açı hesaba katılmamakta; '
    'bu eşiğin 0,5\'e çıkarılması test sırasında lateral_raise gibi '
    'omuz ağırlıklı egzersizlerde veri kaybına yol açtığından 0,4\'te '
    'bırakılmıştır. Hareket aralığı (ROM) ise tekrar boyunca kaydedilen '
    'maksimum ve minimum açı farkı olarak hesaplanmaktadır.'))

story.append(H2('2.4. Makine Öğrenmesi: Random Forest'))

story.append(P('Breiman (2001), karar ağaçlarının tek başına yüksek varyanslı çıktılar '
    'ürettiğini gözlemleyerek bootstrap örneklemesiyle büyütülen yüzlerce ağacın '
    'oylamayla birleştirildiği Random Forest\'i önermiştir. Bu çalışmada algoritmayı '
    'tercih eden üç pratik neden vardır. Birincisi, class_weight=\'balanced\' seçeneği '
    'sınıf dengesizliğini (örneğin shoulder_press\'te 5 doğru / 56 yanlış) '
    'otomatik ağırlıklandırmayla gidermektedir. İkincisi, predict_proba() ile '
    'her tahmine güven skoru eşlik etmekte; düşük güvenli (< 0,55) tahminler '
    'HUD\'da ayrıca işaretlenmektedir. Üçüncüsü, n_jobs=-1 ile tüm CPU '
    'çekirdeklerini kullanarak eğitim süresi kısalmaktadır. '
    'Nihai yapılandırma: n_estimators=300, min_samples_leaf=3.'))

story.append(H2('2.5. Vücut Kompozisyonu Tahmini'))

story.append(P('Vücut yağ oranını doğru ölçmenin iki altın standardı DEXA taraması ve su '
    'altı tartımıdır; her ikisi de özel klinik donanım gerektirir ve sıradan '
    'kullanıcıya erişilebilir değildir. Daha ucuz alternatifler — BKİ, deri '
    'kıvrımı, biyoelektrik impedans — tek bir ölçüme dayandığından hataya '
    'açıktır. Bu çalışmada benimsenen yaklaşım, boy-kilo-yaş-cinsiyet '
    'temelini kamera silüetiyle zenginleştiren bir özellik vektörü '
    'üzerinde Gradient Boosting Regressor çalıştırmaktır. GBR\'nin '
    'artıksal öğrenme mekanizması, birbiriyle korelasyonlu antropometrik '
    'ölçümler arasındaki doğrusal olmayan ilişkileri yakalamada basit '
    'regresyon modellerinden belirgin biçimde daha başarılıdır. Ayrıca '
    'SimpleImputer ile eksik ölçümler medyanla tamamlandığından kullanıcının '
    'yalnızca boy-kilo-yaş girmesi bile çalışan bir tahmin üretmektedir.'))

story.append(H2('2.6. Güç Normalizasyonu ve Dots Skoru'))

story.append(P('70 kg\'lık bir sporcunun 150 kg squat yapması mı daha etkileyici, yoksa '
    '100 kg\'lık birinin 180 kg yapması mı? Bu soruyu yanıtlamak için vücut '
    'ağırlığından bağımsız bir normalizasyon katsayısı gerekir. Wilks katsayısı '
    'uzun yıllar bu amaçla kullanılmıştır; ancak OpenPowerlifting topluluğu 2019\'da '
    'yüksek vücut ağırlığı kategorilerindeki adaletsiz eğriyi düzelten Dots '
    'formülünü önermiştir. Dots = 500 / f(bw) × toplam_kg formülünde payda f(bw), '
    'erkekler için dördüncü dereceli bir polinomdur. Sisteme bu formülü entegre '
    'ederken ilk hesaplamada hata yapıldı: polinomun katsayıları OpenPowerlifting '
    'wiki sayfasından elle girildiğinden bir negatif işaret kaçırılmıştı ve '
    '80 kg altı için Dots değerleri hatalı çıkıyordu. Kaynaktaki katsayılar '
    'tek tek doğrulandıktan sonra düzeltildi; bu nedenle tezdeki '
    'Dots değerleri nihai doğrulanmış formüle aittir.'))

story.append(H2('2.7. Çok İş Parçacıklı Sistem Tasarımı'))

story.append(P('Ana kamera döngüsü her kareyi hem ekranda göstermek hem de MediaPipe\'a '
    'işletmek hem de el jestlerini okumak zorundadır. Bunları tek thread\'de '
    'sırayla yapmak denemeye değer ama çalıştırmaya değmez; test sırasında '
    'tüm işlemi tek döngüde yaptığımızda kare hızı 8-10 fps\'ye düşüyordu. '
    'Çözüm klasik üretici-tüketici deseni oldu: PoseWorker, BodyWorker ve '
    'GestureWorker adlı üç daemon thread Python queue\'larıyla kamera döngüsünden '
    'bağımsız çalışmakta; threading.Lock ile paylaşılan değişkenlere erişim '
    'güvence altına alınmaktadır. Her thread 480×270 girdi alır; işlenmiş '
    'sonuçlar bir sonraki kare çizilmeden önce ana döngüye aktarılır. '
    'Bu yapı standart donanımda 30 fps\'nin korunmasını sağlamaktadır.'))

# ── 3. LİTERATÜR TARAMASI ────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('3. LİTERATÜR TARAMASI'))

story.append(P('Egzersiz form analizi ve hareket kalitesi değerlendirmesi akademik literatürde '
    'üç ana koldan ele alınmaktadır: (1) özel donanım (Kinect, IMU) tabanlı yaklaşımlar, '
    '(2) RGB kamera ve poz tahmin modeli tabanlı yaklaşımlar, (3) giyilebilir sensör '
    'tabanlı yaklaşımlar. Bu bölüm, her koldan öne çıkan çalışmaları değerlendirmekte '
    've mevcut çalışmanın konumunu belirlemeyi amaçlamaktadır.'))

story.append(P('Özel donanım tabanlı çalışmalar arasında en kapsamlı veri setini sunan KIMORE '
    '(Capecci vd., 2018) dikkat çekmektedir. Microsoft Kinect RGB-D sensörüyle kayıt '
    'altına alınan 78 katılımcının beş fizik tedavi egzersizini gerçekleştirmesinden '
    'oluşan bu veri seti, klinik hareket puanlamasıyla eşleştirilmektedir. Mevcut '
    'çalışma bu kısıtı standart RGB kameraya yönelerek aşmaktadır.'))

story.append(P('Shotton vd. (2011), Microsoft\'un Kinect\'i için temel algoritmik katkıyı '
    'sunmuştur. Rastgele karar ağacı tabanlı bu yaklaşım, derinlik görüntülerinden '
    'milisaniyeler içinde insan vücut parçalarını sınıflandırabilmektedir. RGB kamera '
    'tabanlı hareket kalitesi değerlendirmesinde Pirsiavash ve Ramanan (2014), '
    'profesyonel hakem puanlamasını hedef alarak çeşitli sporlarda otomatik hareket '
    'kalitesi derecelendirmesi yapmıştır. Liao vd. (2020), squat egzersizinde açı '
    'sapmasını ölçmek için OpenPose tabanlı bir sistem geliştirmiş; 8 katılımcı '
    'üzerinde yaptıkları test çalışmasında yüzde 85 uyum bildirmiştir.'))

story.append(P('Dang vd. (2022), 2012-2022 döneminde yayımlanan 2B insan pozu tahmin '
    'yöntemlerini kapsamlı biçimde inceleyen bir derleme çalışması sunmuş; yöntemleri '
    'ısı haritası tabanlı ve regresyon tabanlı olarak sınıflandırarak her kategorinin '
    'güçlü ve zayıf yanlarını karşılaştırmalı olarak ortaya koymuştur. Kok vd. (2022), '
    'MediaPipe Pose kullanarak ev ortamında squat ve lunge analizini gerçekleştirmiş; '
    '10 katılımcılı ön çalışmalarında uzman değerlendirmesiyle ortalama yüzde 79 uyum '
    'bildirmiştir.'))

story.append(P('Türkiye\'de YBS ve bilgisayar mühendisliği perspektifinden yürütülmüş kamera '
    'tabanlı egzersiz form analizi çalışmalarının sayısı oldukça sınırlıdır. YÖK Ulusal '
    'Tez Merkezi veritabanında gerçekleştirilen taramada bu konuyu doğrudan ele alan bir '
    'tez kaydına ulaşılamamıştır. Bu durum, mevcut çalışmanın yerel literatürdeki '
    'boşluğu doldurma ve gelecek araştırmalara referans oluşturma potansiyelini '
    'güçlendirmektedir.'))

story += make_tbl(
    'Tablo 1. Egzersiz form analizi literatürü karşılaştırma tablosu',
    ['Çalışma', 'Donanım', 'Kapsam', 'Gerçek Zamanlı', 'ML Modeli'],
    [
        ['Pirsiavash & Ramanan (2014)', 'RGB Kamera', 'Genel spor', 'Hayır', 'SVM'],
        ['Shotton vd. (2011)', 'Kinect RGB-D', 'Genel poz', 'Evet', 'Karar Ağacı'],
        ['Capecci vd. (2018)', 'Kinect RGB-D', 'Rehabilitasyon', 'Hayır', 'Yok'],
        ['Liao vd. (2020)', 'RGB Kamera', 'Squat', 'Evet', 'Yok (kural)'],
        ['Dang vd. (2022)', '—', 'Derleme', 'Hayır', 'Çeşitli'],
        ['Kok vd. (2022)', 'RGB Kamera', 'Squat/Lunge', 'Evet', 'Yok (kural)'],
        ['Bu Çalışma', 'RGB Kamera', '19 Egzersiz', 'Evet', 'Random Forest'],
    ],
    col_widths=[4.2*cm, 2.8*cm, 2.8*cm, 2.8*cm, 2.8*cm]
)

story.append(P('Tablo 1\'den görüldüğü üzere, tek kamera kullanarak 19 farklı egzersizi '
    'gerçek zamanlı hem kural tabanlı hem de makine öğrenmesi sınıflandırmasıyla '
    'değerlendiren bir çalışma literatürde yer almamaktadır.'))

# ── 4. YÖNTEM ────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('4. YÖNTEM'))
story.append(H2('4.1. Sistem Mimarisine Genel Bakış'))

story.append(P('Sistem, birbirine gevşek bağlı yedi işlevsel modülden oluşmaktadır. '
    'Her modül kendi alt dizininde bağımsız Python paketleri olarak yapılandırılmış; '
    'modüller arası bağımlılık yalnızca config.py sabitleri ve kullanici_verisi/ '
    'klasöründeki JSON dosyaları üzerinden kurulmaktadır. Ana uygulama döngüsü '
    'main.py\'de tanımlıdır; bu dosya kamera akışını PoseWorker thread\'ine yönlendirerek '
    'tüm modülleri tek bir ekran döngüsünde orchestrate etmektedir. '
    'Kamera çözünürlüğü 1280×720 olarak tutulurken pose işleme 480×270\'de '
    'gerçekleştirilmekte; bu ayrım sayesinde standart donanımda 30 fps akıcılık '
    'korunmaktadır. Şekil 1\'de sistemin genel modül mimarisi ve bileşenler arası '
    'veri akışı gösterilmektedir.'))

story.extend(make_fig(1, 'Sistem modül mimarisi — yedi bileşen ve veri akışı', [
    box_row(['main.py — Ana Uygulama Döngüsü (Kamera + Tuş + Ekran)'],
            [FW], bg='#D0E8FF'),
    SP(4),
    box_row([
        'PoseWorker\n(iskelet)',
        'BodyWorker\n(segmentasyon)',
        'GestureWorker\n(el jesti)',
    ], [FW/3, FW/3, FW/3], bg='#E8F4E8'),
    SP(4),
    box_row([
        'exercises/\n19 form motoru',
        'ml/\nRF sınıflandırıcı',
        'bodyfat/\nyağ tahmini',
        'strength/\nguç profili',
        'nutrition/\nbeslenme',
        'progress/\nilerleme',
        'feedback/\nHUD + ses',
    ], [FW/7]*7, bg='#FFF8E8'),
]))

story.append(H2('4.2. Veri Toplama ve İşleme Pipeline\'ı'))

story.append(P('Etiketli egzersiz verisi üretmek için tamamen otomatik, uçtan uca bir veri '
    'işleme hattı tasarlanmıştır. Veri derleme sürecinde her egzersiz için İngilizce '
    'arama terimleri oluşturulmuş; "proper form", "correct technique", "common mistakes" '
    'anahtar sözcükleri birleştirilerek hem doğru hem de hatalı form örneklerini '
    'barındıran kanallar hedeflenmiştir. Bu strateji, aynı video kaynağından hem '
    '"correct" hem "wrong" etiketli tekrar çıkarmayı mümkün kılmıştır. Toplam 652 '
    'video 21 egzersiz kategorisinde derlenmiştir; push_up ve russian_twist kategorileri '
    'etiketleme sonrasında tek sınıf (yalnızca "correct") içerdiğinden kapsam dışına '
    'alınmış, 19 egzersiz kalıcı olarak benimsenmiştir.'))

story.append(P('Video indirme altyapısı olarak yt-dlp kullanılmıştır. Bazı büyük fitness '
    'kanalları bot trafiğini engellemek amacıyla HTTP 429 hataları döndürdüğünden '
    '--sleep-requests 1.0 ve --sleep-interval 2 parametreleri eklenerek istek hızı '
    'düşürülmüştür. İndirilen videolar 1080p veya mevcut en yüksek çözünürlükte '
    'kaydedilmiş; video başına ortalama dosya boyutu 180 MB civarında seyretmiştir. '
    '652 videonun tamamı yaklaşık 14 saatlik toplu işlemle ml/video_miner.py '
    'modülü aracılığıyla işlenmiştir. Tekrar tespitinde geliştirilen medyan-kesişim '
    'tabanlı adaptif algoritma, son 60 karenin medyanını dinamik eşik olarak '
    'güncelleme; birincil açı bu eşiği iki kez (aşağıdan yukarıya ve yukarıdan '
    'aşağıya) geçtiğinde bir tekrarı tamamlanmış saymaktadır. Bu yaklaşım, sabit açı '
    'eşiği kullanan yöntemlerin farklı kamera açıları ve boy oranlarında yaşadığı '
    'hassasiyet sorununu belirgin ölçüde azaltmıştır.'))

story.append(P('Video işleme hattının adım adım akışı şöyledir: ham video OpenCV '
    'VideoCapture nesnesiyle açılır; gereksiz hesaplamadan kaçınmak amacıyla her '
    'üçüncü kare alınır ve BGR\'den RGB\'ye dönüştürülerek MediaPipe Pose API\'ye '
    'iletilir. Başarılı iskelet tespitinde landmarks_to_angles() işlevi çağrılarak '
    'sekiz eklem açısı hesaplanır ve anlık açı sözlüğüne eklenir. Egzersiz motorunun '
    'analyze() metodu bu sözlüğü oylayarak faz bilgisini (up/down) günceller; medyan '
    'eşik kontrolü iki kesişim sayıldığında _flush_rep() devreye girer ve o tekrara '
    'ait tüm frame açıları veri setine CSV satırları olarak yazılır. Veri kalitesi '
    'güvencesi için hatta dört katmanlı filtreleme uygulanmıştır: (1) visibility '
    'skoru 0,40\'ın altındaki kareler işlenmez; (2) 10 kareden kısa tekrarlar '
    'atılır; (3) oyların yüzde 60\'ından azı "correct" ise tekrar otomatik olarak '
    '"wrong" olarak etiketlenir; (4) sınıf başına beşten az örnek içeren egzersizler '
    'model eğitiminden çıkarılır. Bu filtreler sonucunda hammadde 1.139 kullanılabilir '
    'tekrara indirilmiştir.'))

story.extend(make_fig(2, 'Veri işleme pipeline akışı — videodan etiketli CSV\'ye', [
    box_row(['Ham Video (652 dosya, ~180 MB/video, toplam ~117 GB)'],
            [FW], bg='#D0E8FF'),
    SP(3),
    box_row([
        '1. VideoCapture\n(her 3. kare)',
        '2. BGR→RGB\ndönüşüm',
        '3. MediaPipe\nPose API',
        '4. landmarks\n→ angles()',
    ], [FW/4]*4, bg='#E8F4E8'),
    SP(3),
    box_row([
        '5. Faz tespiti\n(up/down)',
        '6. Medyan eşik\nkontrolü',
        '7. Tekrar\nsayacı',
        '8. _flush_rep()\n→ CSV satırı',
    ], [FW/4]*4, bg='#E8F4E8'),
    SP(3),
    box_row([
        'Filtre 1:\nvisibility < 0.40 → at',
        'Filtre 2:\n< 10 kare → at',
        'Filtre 3:\noy < %60 → wrong',
        'Filtre 4:\n< 5 örnek → çıkar',
    ], [FW/4]*4, bg='#FFF0E8'),
    SP(3),
    box_row(['1.139 kullanılabilir tekrar (655 correct / 484 wrong)'],
            [FW], bg='#E8FFE8'),
]))

story.append(H2('4.3. İskelet Çıkarımı ve Özellik Hesaplama'))

story.append(P('MediaPipe Pose API şu üç parametreyle yapılandırılmıştır: model_complexity=0 '
    '(hız-doğruluk dengesini standart donanım koşullarında optimize eden hafif model), '
    'min_detection_confidence=0.6, min_tracking_confidence=0.5. Özellik vektörü 40 '
    'boyuttan oluşmaktadır. Birinci grup: sekiz temel açının tekrar boyunca minimum, '
    'maksimum, ortalama ve standart sapması (32 özellik). İkinci grup: simetri ölçütleri '
    '(4 özellik). Üçüncü grup: ROM, maksimum hız, faz oranı ve normalize süre (4 özellik). '
    'Minimum açı tam kontraksiyonu; maksimum açı tam uzanmayı; standart sapma hareket '
    'tutarlılığını kodlar. Simetri ölçütleri sol-sağ asimetriyi ölçmekte; 15°\'nin '
    'üzerindeki asimetri yaralanma riskini artırmaktadır.'))

story.append(H2('4.4. Kural Tabanlı Form Analiz Motorları'))

story.append(P('Sistemdeki 19 egzersiz için bağımsız analiz motorları oluşturulmuştur. '
    'Tüm motorlar exercises/base_exercise.py\'daki BaseExercise soyut sınıfından türemekte '
    've analyze(landmarks, width, height) → FormResult arayüzünü uygulamaktadır. Hata '
    'yaralanma riskiyle doğrudan ilişkili sapmalara, uyarı ise etkinliği düşüren ancak '
    'acil tehlike oluşturmayan sapmalara karşılık gelir.'))

story += make_tbl(
    'Tablo 2. Seçili egzersizler için analiz parametreleri',
    ['Egzersiz', 'Birincil Açı', 'Zirve (°)', 'Dip (°)', 'Ek Kural'],
    [
        ['Biceps Curl', 'Sol dirsek', '55', '150', 'Gövde eğilimi < 0.09'],
        ['Triceps Ext.', 'Sol dirsek', '150', '60', 'Dirsek sabit'],
        ['Shoulder Press', 'Sol dirsek', '160', '80', 'Bilek hizası'],
        ['Lateral Raise', 'Sol omuz', '65', '30', 'Dirsek bükülmesi'],
        ['Pec Fly', 'Sol dirsek', '100', '175', 'Simetri < 15°'],
        ['Bench Press', 'Sol dirsek', '80', '155', 'Flare açısı < 75°'],
        ['Squat', 'Sol diz', '85', '160', 'Diz-parmak hizası'],
        ['Deadlift', 'Sol diz', '90', '160', 'Sırt duruluğu'],
        ['Lat Pulldown', 'Sol dirsek', '65', '155', 'Gövde sallanımı'],
        ['Hip Thrust', 'Sol kalça', '165', '100', 'Kalça uzanması'],
        ['Leg Extension', 'Sol diz', '165', '85', 'Tam uzanma'],
    ],
    col_widths=[3.5*cm, 3.0*cm, 2.2*cm, 2.2*cm, 4.5*cm]
)

story.append(H2('4.5. Makine Öğrenmesi Sınıflandırıcısı'))

story.append(P('ml/trainer.py modülü şu adımları izler: (1) CSV yükleme ve etiket dönüşümü, '
    '(2) sınıf başına minimum 5 örnek kontrolü, (3) stratifiye 80/20 bölünme, '
    '(4) StandardScaler fit (sadece eğitim kümesine), '
    '(5) RandomForestClassifier(n_estimators=300, class_weight=\'balanced\', '
    'min_samples_leaf=3) eğitimi, (6) test doğruluğu hesaplama, '
    '(7) ml/models/{egzersiz}_form.joblib\'e kaydetme. Güven skoru 0,55 eşiğinin '
    'altında kaldığında "düşük güven" uyarısı gösterilmektedir.'))

story.append(H2('4.6. Tamamlayıcı Modüller'))

story.append(P('Temel form analizi altyapısının yanı sıra sistem; vücut kompozisyonu tahmini, '
    'güç persentili hesaplama, beslenme takibi, antrenman günlüğü ve kişisel profil '
    'yönetimini tek çatı altında birleştiren beş tamamlayıcı modül içermektedir. '
    'Bu modüller birbirinden bağımsız Python paketleri olarak tasarlanmış; ortak '
    'bağımlılık yalnızca kullanici_verisi/ dizinindeki JSON dosyaları üzerinden '
    'kurulmuştur. Böylece herhangi bir modül devre dışı bırakıldığında ana '
    'form analizi döngüsü kesintisiz çalışmaya devam etmektedir.'))

story.append(H3('4.6.1. Vücut Yağ Tahmini'))

story.append(P('bodyfat/estimator.py modülü iki ayrı bilgi kaynağını birleştirerek '
    'vücut yağ oranı tahmini yapmaktadır: kamera görüntüsünden MediaPipe '
    'SegmentationMask aracılığıyla ölçülen silüet genişlikleri ve kullanıcının '
    'profilinden alınan antropometrik veriler. Silüet ölçümü için yöntem şu şekilde '
    'işler: maske ikili eşiklendikten sonra (> 0,45) her yatay satırdaki en soldaki '
    've en sağdaki piksel koordinatları belirlenir; bel bölgesi için omuz-kalça '
    'mesafesinin yüzde 60\'ı noktasından üç piksel yukarı-aşağı taranarak medyan '
    'genişlik alınır. Ham piksel genişliğini santimetreye çevirmek için '
    'kullanıcı boyuna oransal bir ölçek katsayısı uygulanır. Ölçülen piksel '
    'genişliği gerçek çevre ölçümüne doğrudan eşit olmadığından NHANES popülasyon '
    'verisiyle kalibre edilmiş BMI-bağımlı dönüşüm katsayıları kullanılmaktadır: '
    'kalça için hip_factor = 1,856 + 0,0255 × BKİ, bel için '
    'waist_factor = 1,580 + 0,0350 × BKİ. Bu katsayılar 68.011 NHANES ölçümünün '
    'anlık kamera açısına uyarlanmasıyla türetilmiştir.'))

story.append(P('Model eğitimi için vücut yağ ölçümüne sahip üç kaynaktan toplamda 74.511 '
    'kayıt bir araya getirilmiştir. Bu kaynakların dağılımı Tablo 5\'te özetlenmiştir. '
    'Eğitim pipeline\'ı SimpleImputer(strategy=median) → StandardScaler → '
    'GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, '
    'subsample=0.8) adımlarından oluşmaktadır. Eksik ölçümlerin medyanla doldurulması, '
    'farklı veri kalitesi senaryolarında (yalnızca boy/kilo biliniyorsa veya tüm '
    'çevre ölçüleri mevcutsa) aynı modelin sorunsuz çalışmasını sağlamaktadır. '
    'Test kümesinde elde edilen MAE değeri 3,7 yüzde puandır. Gerçek zamanlı '
    'kararlılık için tahminler 25 karelik bir halka tamponda toplanmakta ve '
    'kullanıcıya medyan değer gösterilmektedir; bu yöntem anlık görüntü gürültüsünden '
    'kaynaklanan ±0,5 puanlık salınımları bastırmaktadır.'))

story += make_tbl(
    'Tablo 5. Vücut yağ modeli veri kaynaklarının dağılımı',
    ['Kaynak', 'Kayıt Sayısı', 'Ölçüm Türü', 'Popülasyon'],
    [
        ['NHANES (2003-2018)', '68.011', 'DXA (altın standart)', 'ABD genel popülasyon'],
        ['ANSUR II (2012)', '6.068', 'Antropometri + BKİ tahmini', 'ABD Ordusu personeli'],
        ['Kaggle – Extended BF', '432', 'Su altı tartımı', 'Karma (spor salonu)'],
        ['TOPLAM', '74.511', '—', '—'],
    ],
    col_widths=[4.0*cm, 3.0*cm, 4.0*cm, 4.3*cm]
)

story.append(P('Kamera mesafesi yetersiz olduğunda veya maske kalitesi düştüğünde sistem '
    'otomatik olarak Deurenberg (1991) fallback formülüne geçmektedir: '
    'yağ_oranı = 1,20 × BKİ + 0,23 × yaş - 16,2 (erkek) veya - 5,4 (kadın). '
    'Segmentasyon maskesi geçerli olduğu durumlarda hesaplanan değerler; BKİ, bel '
    've kalça persentilleri NHANES+ANSUR2 norm tablosuna karşı anlık olarak '
    'hesaplanmaktadır. Vücut tipi sınıflandırması erkekler için altı aralığa '
    'ayrılmıştır: < yüzde 6 Estetik Sporcu, yüzde 6-14 Atletik, yüzde 14-18 Fit, '
    'yüzde 18-25 Ortalama, yüzde 25 üstü Yüksek Yağ. Bu eşikler American Council '
    'on Exercise (ACE) kategorileriyle örtüşmekte; kadın için aralıklar yaklaşık '
    'sekiz puan yukarı kaydırılmaktadır.'))

story.append(H3('4.6.2. Güç Profili ve Dots Skoru'))

story.append(P('strength/estimator.py modülü kullanıcının squat, bench press ve deadlift '
    'kaldırışlarını OpenPowerlifting veri tabanından türetilen norm tablolarıyla '
    'karşılaştırarak güç persentilini hesaplamaktadır. OpenPowerlifting, uluslararası '
    'powerlifting federasyonlarına ait yarışma kayıtlarını açık kaynak olarak '
    'yayımlamaktadır. Ham veride 1,3 milyonun üzerinde tekrar kaydı bulunmaktadır; '
    'bu kayıtlar veri seti içinde hem doğal (ekipmansız) hem de technikli '
    '(Squat suit, Bench shirt) sporcuları kapsamaktadır. veri/kondisyon/build_strength_norms.py '
    'betiği bu veriyi filtreler: ekipman="Raw" veya "Wraps" olmayan kayıtlar, '
    'geçersiz kaldırış değerleri (sıfır veya negatif) ve doping ihlali bulunan '
    'sporcular elenmiştir. Kalan kayıtlar cinsiyete ve 5 kg\'lık vücut ağırlığı '
    'dilimlerine (40-45 kg\'dan 155-160 kg\'ya kadar) ayrılarak p10, p25, p50, p75, '
    'p90 persentil değerleri hesaplanmış ve 202 satırlık strength_norms.csv dosyasına '
    'özetlenmiştir.'))

story.append(P('Persentil hesabında ham kaldırış kilogramı değil Dots skoru kullanılmaktadır. '
    'Dots skoru, kaldırış ağırlığını vücut ağırlığından bağımsız kılan bir '
    'normalizasyon katsayısıdır: Dots = 500 / f(bw) × toplam_kg. Payda f(bw), '
    'erkekler için -0.00000109 × bw^4 + 0.000739 × bw^3 - 0.1919 × bw^2 + '
    '24.09 × bw - 307.75 şeklinde tanımlanan dördüncü dereceli bir polinomdur. '
    'Bu formül 2019\'da OpenPowerlifting topluluğu tarafından Wilks katsayısının '
    'yerine önerilmiştir; özellikle yüksek vücut ağırlığı kategorilerinde daha '
    'adil bir karşılaştırma sağladığı gösterilmiştir. Kullanıcının belirlenen '
    'vücut ağırlığı dilimine düşen norm satırında Dots skoru interpolasyonla '
    'yerleştirilmekte ve kaçıncı persentilde olduğu kullanıcı arayüzüne yansıtılmaktadır.'))

story.append(H3('4.6.3. Beslenme Takip Modülü'))

story.append(P('nutrition/ alt sistemi iki katmandan oluşmaktadır: gıda veritabanı '
    '(food_db.py) ve günlük kalori/makro kaydedicisi (tracker.py). Gıda veritabanı, '
    'USDA FoodData Central\'ın Nisan 2026 sürümünden derlenen 455.100 kayıtlık '
    'compact CSV üzerine inşa edilmiştir. Bu kayıtların büyük çoğunluğu (440.450 '
    'adet) markalı ürünler olmakla birlikte Türkiye\'ye özgü iki ek kaynak da '
    'entegre edilmiştir. Birinci ek kaynak, Hacettepe Üniversitesi\'nin Besin '
    'Bilgi Sistemi\'ni (BEBIS) ve TURKKOMP verilerini temel alan 275 adet el yapımı '
    'Türk ev yemeği kaydıdır; mercimek çorbası, imam bayıldı, köfte gibi yaygın '
    'yemekleri 100 gram başına makro değerleriyle içermektedir. İkinci ek kaynak, '
    'Open Food Facts\'tan Türkiye etiketiyle çekilen 1.082 adet paketli ürün '
    'kaydıdır. Bu iki kaynak birleştirildiğinde veritabanında 1.357 Türk gıdası '
    'yer almakta; standart USDA aramaları yetersiz kaldığında öncelikli olarak '
    'bu kayıtlar döndürülmektedir.'))

story.append(P('Günlük kalori hedefi Harris-Benedict denklemine PAL (Fiziksel Aktivite '
    'Düzeyi) çarpanı uygulanarak belirlenmektedir: Bazal Metabolizma Hızı (BMH) '
    'erkekler için 88,36 + 13,40 × kg + 4,80 × cm - 5,68 × yaş; bu değer '
    'hareketsiz yaşam tarzı için 1,2, orta düzey aktif için 1,55 ve çok aktif '
    'için 1,9 ile çarpılmaktadır. nutrition/tracker.py, kullanıcının profiline '
    'bağlı hedef kaloriyi JSON tabanlı günlük log sistemiyle karşılaştırarak '
    'anlık tüketim, kalan kalori ve makro (protein/karbonhidrat/yağ) dağılımını '
    'ekranda göstermektedir. Log dosyası kullanici_verisi/nutrition_logs.json '
    'adresinde profil adı ve tarih anahtarıyla sözlük yapısında saklanmaktadır; '
    'bu yapı farklı kullanıcıların verilerinin karışmamasını garantilemektedir.'))

story.append(H3('4.6.4. İlerleme Kaydedicisi'))

story.append(P('progress/tracker.py modülü kullanıcının antrenman geçmişini, vücut '
    'ölçümlerini ve güç değerlerini seans bazında kaydeden hafif bir JSON veri '
    'tabanı işlevi görmektedir. Kullanici_verisi/progress_log.json dosyasının yapısı '
    'üç alt kategoriden oluşmaktadır: "exercise" girdileri egzersiz kimliği, tekrar '
    'sayısı ve seans süresi; "body" girdileri vücut yağ oranı, kilo ve BKİ; '
    '"strength" girdileri squat, bench ve deadlift kilogramları ile hesaplanan '
    'Dots skoru. Her girdiye otomatik olarak ISO 8601 formatında tarih damgası '
    'eklenmektedir. Bu yapı sayesinde kullanıcı uygulama üzerinden haftalık ve '
    'aylık trendleri görselleştirilebilmektedir.'))

story.append(P('İlerleme ekranı (progress/screen.py), son 30 günün egzersiz geçmişini '
    'tablo biçiminde listelemekte; güç seyrini grafik yerine satır bazında '
    'kıyaslama olarak sunmaktadır. Veri depolama için harici bir veritabanı '
    'seçilmemesinin temel nedeni kurulum bağımlılığını sıfırda tutmaktır; SQLite\'ın '
    'hafif yapısına karşın standart Python kurulumunda hazır bulunan json modülü '
    'tercih edilmiştir. Bellek kullanımı açısından ortalama 10 farklı kullanıcı '
    'için bir yıllık log yaklaşık 120 KB yer kaplamaktadır.'))

story.append(H3('4.6.5. Kullanıcı Profil Sistemi'))

story.append(P('Tüm kişiselleştirilmiş hesaplamalar — vücut yağ tahmini, Dots persentili, '
    'kalori hedefi — kullanici_verisi/profiles.json dosyasına kaydedilen profil '
    'üzerine otururmaktadır. Her profil girişi şu alanları içermektedir: ad, '
    'boy_cm, kilo_kg, yaş, cinsiyet, bel_cm, kalça_cm, göğüs_cm, kol_cm, boyun_cm. '
    'Bel ve kalça gibi çevre ölçümleri opsiyoneldir; girilmediğinde model '
    'SimpleImputer aracılığıyla bu alanları popülasyon medyanıyla tamamlar. '
    'Sistem çok kullanıcılı çalışmayı desteklemektedir; farklı profiller '
    'birbirinin verisine erişemez ve kendi günlüklerine ayrı ayrı yazar. '
    'Uygulama açılışında profiles.json okunarak profil listesi gösterilmekte; '
    'seçim 2 saniyelik klavye veya el jesti (GestureWorker) ile yapılabilmektedir.'))

story.append(H3('4.6.6. Kullanıcı Arayüzü ve Geri Bildirim Katmanı'))

story.append(P('Kullanıcı arayüzü 1280×720 kamera görüntüsü üzerine bindirilen dört panelden '
    'oluşmaktadır. feedback/visual_feedback.py içindeki draw_hud() işlevi her kare '
    'işlendikten sonra çağrılarak iskelet üzerine bu dört bilgi katmanını çizer. '
    'Sesli geri bildirim modülü (audio_feedback.py) winsound.Beep() üzerine inşa '
    'edilmiş olup üç farklı frekans kullanmaktadır: 800 Hz hata bildirimi, '
    '1.200 Hz uyarı ve 1.600 Hz başarılı tekrar onayı için ayrılmıştır. '
    'Birden fazla hatanın aynı anda üst üste gelmesini engellemek amacıyla '
    '1,5 saniyelik cooldown mekanizması uygulanmıştır; bu süre içinde gelen '
    'ikinci uyarı sessize alınmakta ve yalnızca görsel panel güncellenmektedir. '
    'HUD düzeni Şekil 3\'te gösterilmektedir.'))

story.extend(make_fig(3, 'HUD ekranı dört panel düzeni (1280×720 üzerine OpenCV katmanı)', [
    box_row([
        'SOL ÜST\nAçı Göstergesi\n(8 eklem açısı,\nfaz: UP/DOWN)',
        'SAG ÜST\nOturum İstatistikleri\n(rep sayısı, süre,\nson ML skoru)',
    ], [FW/2, FW/2], bg='#D0E8FF'),
    SP(3),
    box_row([
        '← KAMERA GÖRÜNTÜSÜ (1280×720) — MediaPipe iskelet üst katman →',
    ], [FW], bg='#F0F0F0'),
    SP(3),
    box_row([
        'SOL ALT\nHata/Uyarı Listesi\n(kırmızı=hata,\nturuncu=uyarı)',
        'SAG ALT\nML Tahmini\n(confidence %,\ncorrect/wrong)',
    ], [FW/2, FW/2], bg='#FFE8D0'),
]))

# ── 5. BULGULAR ──────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('5. BULGULAR'))
story.append(H2('5.1. Veri Seti İstatistikleri'))

story.append(P('652 egzersiz videosunun işlenmesi sonucunda 19 egzersiz kategorisinde '
    'toplam 1.139 etiketli tekrar elde edilmiştir. Video başına ortalama 1,75 tekrar, '
    'seanslardaki video süreleri ve kamera açısı çeşitliliğiyle açıklanabilmektedir. '
    'Standart dizüstü bilgisayarda 652 videonun tümü yaklaşık 14 saatte '
    'tamamlanmıştır.'))

story += make_tbl(
    'Tablo 3. Egzersiz başına veri seti istatistikleri',
    ['Egzersiz', 'Doğru', 'Yanlış', 'Toplam', 'Oran (D/Y)'],
    [
        ['bench_press', '22', '10', '32', '2,2'],
        ['biceps_curl', '32', '10', '42', '3,2'],
        ['deadlift', '27', '19', '46', '1,4'],
        ['decline_bench_press', '15', '40', '55', '0,4'],
        ['fly', '42', '8', '50', '5,3'],
        ['hammer_curl', '28', '33', '61', '0,8'],
        ['hip_thrust', '52', '8', '60', '6,5'],
        ['incline_bench_press', '14', '53', '67', '0,3'],
        ['lat_pulldown', '13', '21', '34', '0,6'],
        ['lateral_raise', '59', '29', '88', '2,0'],
        ['leg_extension', '33', '26', '59', '1,3'],
        ['leg_raises', '34', '21', '55', '1,6'],
        ['pull_up', '46', '24', '70', '1,9'],
        ['romanian_deadlift', '28', '23', '51', '1,2'],
        ['shoulder_press', '5', '56', '61', '0,1'],
        ['squat', '83', '7', '90', '11,9'],
        ['t_bar_row', '82', '5', '87', '16,4'],
        ['tricep_dips', '29', '65', '94', '0,4'],
        ['triceps', '11', '26', '37', '0,4'],
        ['TOPLAM', '655', '484', '1.139', '1,4'],
    ],
    col_widths=[4.8*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3.0*cm]
)

story.append(H2('5.2. Model Performans Sonuçları'))

story.append(P('Her egzersiz için eğitilen 19 Random Forest modeli, stratifiye yüzde 80/20 '
    'bölünmesiyle elde edilen test kümelerinde değerlendirilmiştir.'))

story += make_tbl(
    'Tablo 4. Egzersiz modeli test doğrulukları',
    ['Egzersiz', 'Test Doğruluğu (%)', 'Test Örneği'],
    [
        ['bench_press', '100,0', '6'],
        ['biceps_curl', '88,9', '9'],
        ['deadlift', '50,0', '9'],
        ['decline_bench_press', '90,9', '11'],
        ['fly', '70,0', '10'],
        ['hammer_curl', '38,5', '13'],
        ['hip_thrust', '91,7', '12'],
        ['incline_bench_press', '78,6', '14'],
        ['lat_pulldown', '71,4', '7'],
        ['lateral_raise', '72,2', '18'],
        ['leg_extension', '83,3', '12'],
        ['leg_raises', '90,9', '11'],
        ['pull_up', '57,1', '14'],
        ['romanian_deadlift', '45,5', '11'],
        ['shoulder_press', '92,3', '13'],
        ['squat', '100,0', '18'],
        ['t_bar_row', '88,9', '18'],
        ['tricep_dips', '73,7', '19'],
        ['triceps', '62,5', '8'],
        ['Ortalama', '76,1', '—'],
    ],
    col_widths=[5.5*cm, 5.0*cm, 3.8*cm]
)

story.append(P('Sonuçlar üç grupta incelenebilir. Yüksek doğruluk grubu (≥%85): bench_press, '
    'biceps_curl, decline_bench_press, hip_thrust, leg_raises, shoulder_press, squat, '
    't_bar_row. Orta doğruluk grubu (%60-84): fly, incline_bench_press, lat_pulldown, '
    'lateral_raise, leg_extension, pull_up, tricep_dips, triceps. Düşük doğruluk grubu '
    '(<%60): deadlift, hammer_curl, romanian_deadlift.'))

story.append(P('Özellik önem sıralamaları incelendiğinde tüm egzersiz modellerinde ortaklaşan '
    'örüntüler dikkat çekmektedir. Birincil açının standart sapması ve ROM özelliklerinin '
    'önem skorları büyük çoğunlukta ilk üçe girmektedir; "hangi açıda olduğundan çok ne '
    'kadar tutarlı ve tam hareket edildiği" form kalitesini daha iyi tahmin etmektedir. '
    'Başlangıçta en yüksek doğruluğun bilateral egzersizlerden geleceği öngörülmüştü; '
    'ancak bench_press ve squat\'ın %100 elde ederken fly\'ın yalnızca %70 alması bu '
    'beklentiyi kısmen tersine çevirdi. Fly egzersizinin görece düşük performansı, iki '
    'bilek arası açıyı ölçen özellik vektörünün gövde öne eğimi kaynaklı artıfaktlara '
    'beklenenden daha kırılgan olduğuna işaret etmektedir.'))

story.append(P('Çapraz doğrulama (5-kat stratifiye CV) ortalama skoru yüzde 72,4 olarak '
    'ölçülmüştür; bu değer test kümesi sonucundan 3,7 puan düşüktür ve aralarındaki '
    'fark, veri setinin sınırlı büyüklüğünden kaynaklanan değerlendirme varyansını '
    'yansıtmaktadır.'))

story.append(H2('5.3. Sistem Performansı'))

story.append(P('Intel Core i5-1135G7 (entegre Iris Xe grafik) işlemcili 16 GB RAM\'li '
    'dizüstü bilgisayarda test edilmiştir. MediaPipe model_complexity=0 ile 480×270 '
    'çözünürlükte ortalama 28-32 fps elde edilmiştir. Aynı donanımda 1280×720 '
    'çözünürlükte doğrudan pose işleme yapıldığında kare hızı 10-14 fps\'ye '
    'gerilemiştir; bu nedenle düşük çözünürlük-yüksek ekran ayrımı zorunlu '
    'kılınmıştır. Bellek kullanımı: başlangıçta yaklaşık 380 MB, '
    '19 model yüklenince yaklaşık 450 MB.'))

story.append(H2('5.4. Vücut Yağ ve Güç Profili Değerlendirmesi'))

story.append(P('Vücut yağ tahmini modülü dört farklı kullanıcıyla (Furkan, İslam, Mustafa, '
    'Yusuf) toplam 12 ölçüm seansında değerlendirilmiştir. Kamera mesafesi 1,5-2,5 m '
    'aralığında tutulmuş; her kullanıcı için üç tekrar ölçüm gerçekleştirilmiştir. '
    'Sonuçlar incelendiğinde aynı kullanıcı için yağ tahmini değerleri ±2,1 yüzde '
    'puan standart sapma göstermiştir. Bu değer, deri kıvrımı ölçüm yöntemiyle '
    'elde edilen günler arası tekrarlanabilirliğe (±3,5) ve BKİ tabanlı tahminlere '
    '(±4,8) kıyasla belirgin biçimde daha kararlı bir seyir izlemiştir. Ancak bu '
    'karşılaştırmanın sınırlılığı vurgulanmalıdır: klinik doğrulama için DXA veya '
    'su altı tartımı referans alınmamış; sistematik sapma (bias) hesaplanmamıştır. '
    'Modelin eğitildiği veri setinde ağırlıklı ABD popülasyonu yer aldığından '
    'Türk kullanıcılar için kalibrasyon hatası beklenenden yüksek olabilir.'))

story.append(P('Güç profili değerlendirmesinde dört kullanıcının squat, bench press ve '
    'deadlift değerleri sisteme girilmiştir. Örnek olarak Furkan profili (70 kg, '
    '178 cm, 23 yaş) için sisteme girilen 150/150/200 kg kaldırışlar Dots skoru '
    '375,6 olarak hesaplanmış; bu değer OpenPowerlifting norm tablosunda yüzde 95 '
    'persentile karşılık gelmektedir. Yusuf profili (85 kg) için 130/110/160 kg '
    'girişinden Dots skoru 266,5 elde edilmiş ve bu değer yaklaşık yüzde 72 '
    'persentile düşmüştür. Norm tablosunun gerçek yarışma verilerine dayandığı '
    'düşünüldüğünde bu çıktıların yorumlanmasında dikkatli olunmalıdır; '
    'antrenman şartlarında ölçülen kaldırışlar genellikle yarışma kaldırışlarından '
    'düşük çıkmakta, dolayısıyla kullanıcı persentili gerçek rekabetçi düzeyinden '
    'hafif yukarıda görünebilmektedir. Bu durum kullanıcıya ilerleme bağlamında '
    'motivasyon sağlayıcı bir referans sunarken kıyaslamanın yarışma performansıyla '
    'doğrudan örtüşmediği not edilmelidir.'))

# ── 6. TARTIŞMA VE SONUÇ ─────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('6. TARTIŞMA VE SONUÇ'))
story.append(H2('6.1. Bulgular Üzerine Değerlendirme'))

story.append(P('Ortalama yüzde 76,1 test doğruluğu, ne mükemmel bir başarı ne de açık bir '
    'başarısızlık olarak nitelendirilebilir; bu sayının anlamını veri hacmi ve '
    'metodolojik kısıtlamalar çerçevesinde yorumlamak gerekmektedir. Egzersiz başına '
    'ortalama 60 etiketli tekrar, akademik makine öğrenmesi çalışmalarında "az veri" '
    'kategorisine girmektedir. Bununla birlikte mevcut sistem, bu sınırla birlikte bile '
    'egzersizlerin üçte ikisinde yüzde 70\'in üzerinde doğruluk elde etmekte; bu oran, '
    'teknik fizibilite hedefi için yeterli kabul edilebilmektedir.'))

story.append(P('Shoulder_press\'in yüzde 92,3 doğruluğuyla yüksek performanslı görünmesi '
    'ancak 5 doğru/56 yanlış oranına sahip olması, sınıf önyargısı sorununu açıkça '
    'ortaya koymaktadır. Model neredeyse her durumda "yanlış" tahmin ederek yüksek '
    'doğruluk elde etmektedir. Hammer_curl (yüzde 38,5), romanian_deadlift '
    '(yüzde 45,5) ve deadlift (yüzde 50,0) için zayıf sonuçlar ise kural motoru '
    'ile gerçek form kalitesi arasındaki uyum düşüklüğünü yansıtmaktadır.'))

story.append(H2('6.2. Literatürle Karşılaştırma'))

story.append(P('Liao vd. (2020) ile doğrudan karşılaştırma yapılabilmektedir: onlar '
    'yalnızca squat egzersizini ve 8 katılımcıyı kullanarak yüzde 85 uyum '
    'bildirmiştir. Bu çalışma 19 egzersiz ve 1.139 tekrarla yüzde 76,1 ortalama '
    'elde etmiştir. Sayısal açıdan bakıldığında bu bir gerileme gibi görünse de '
    'kapsam on dokuz kat daha geniştir ve veri tamamen otomatik etiketlenmiştir; '
    'insan doğrulaması yapılmamıştır. KIMORE tabanlı çalışmalar '
    'yüzde 80-90 aralığında raporlamaktadır ama koşullar çok daha kontrollüdür: '
    'Kinect derinlik sensörü, sabit ışıklı laboratuvar ortamı, beş egzersiz ve '
    'klinik fizyoterapist denetimi. Ev ortamı tek kamera senaryosunda bu rakamları '
    'doğrudan kıyaslamamak gerekir.'))

story.append(H2('6.3. Sınırlılıklar'))

story.append(P('En büyük sorun veri hacmidir. Egzersiz başına ortalama 60 tekrar makine '
    'öğrenmesi literatüründe "az veri" sayılır; pek çok modelin yüzde 70\'in '
    'altında kalması, daha fazla verinin toplanmasını gerektirdiğini göstermektedir. '
    'İkinci sorun etiketleme döngüsüdür: etiketler kural motorlarına dayanıyor, '
    'kural motorları ise araştırmacı kararlarına. Bu durum hatanın veri setine '
    'taşınması anlamına gelir ve en iyi makine öğrenmesi modelinin dahi performansını '
    'tavan düzeyinde kısıtlar. Üçüncü sorun klinik doğrulama yapılamamış olmasıdır; '
    'bildirilen doğruluklar kendi veri setimiz üzerinde hesaplanmış, bağımsız '
    'katılımcı testleriyle teyit edilmemiştir. Son olarak tek kamera kısıtı bazı '
    'üç boyutlu hataları — örneğin diz içe çökmesini — sagital düzlemden '
    'görülemeyen açılar nedeniyle kaçırabilmektedir.'))

story.append(H2('6.4. Gelecek Çalışmalar'))

story.append(P('Kısa vadede öncelikli iyileştirme hedefi etiketleme kalitesini artırmaktır. '
    'İnsan etiketlemesi ve Cohen\'s Kappa uyum ölçümü eklenebilir. Orta vadede LSTM ya '
    'da Temporal Convolutional Network (TCN) tabanlı zaman serisi modelleri tekrar '
    'içindeki zamansal bağımlılıkları daha iyi yakalayabilir. Uzun vadede üç boyutlu '
    'landmark koordinatları açı hesabına dahil edilebilir, mobil platformlara '
    'taşınabilir ve rehabilitasyon alanına genişlenebilir.'))

story.append(H2('6.5. Sonuç'))

story.append(P('Bu çalışmada, kullanıcılara kişisel antrenöre başvurmadan gerçek zamanlı '
    'egzersiz form geri bildirimi sağlayan, veri odaklı ve çok modüllü bir bilgisayarlı '
    'görü platformu tasarlanmış ve Python ekosistemi üzerinde çalışır hâle getirilmiştir. '
    'Sistemin teknik omurgası: BlazePose tabanlı 33 noktalı iskelet çıkarımı, sekiz '
    'temel eklem açısının gerçek zamanlı hesabı, 19 egzersiz için biyomekanik kural '
    'motorları, 40 boyutlu özellik vektörü üzerinde Random Forest sınıflandırıcıları '
    've çok iş parçacıklı mimari. 652 YouTube videosunu işleyerek 1.139 etiketli tekrar '
    'üreten otomatik pipeline, vücut yağ tahmini, güç persentili ve Türkiye\'ye özgü '
    'beslenme takibiyle bütüncül bir performans rehberliği sunmaktadır. Ortalama yüzde '
    '76,1 test doğruluğuyla teknik fizibilite düzeyini karşılamakta; gelecekte insan '
    'etiketlemesi ve zamansal modellerin entegrasyonuyla geliştirilmeye açık, '
    'ölçeklenebilir bir temel oluşturmaktadır.'))

# ── KAYNAKÇA ─────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('KAYNAKÇA'))

refs = [
    'Bazarevsky, V., Grishchenko, I., Raveendran, K., Zhu, T., Zhang, F. ve Grundmann, M. (2020). BlazePose: On-device real-time body pose tracking. Retrieved from https://arxiv.org/abs/2006.10204',
    'Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.',
    'Cao, Z., Hidalgo, G., Simon, T., Wei, S. E. ve Sheikh, Y. (2021). OpenPose: Realtime multi-person 2D pose estimation using part affinity fields. IEEE Transactions on Pattern Analysis and Machine Intelligence, 43(1), 172–186.',
    'Capecci, M., Ceravolo, M. G., Ferracuti, F., Iarlori, S., Monteriu, A., Romeo, L. ve Verdini, F. (2018). The KIMORE dataset. IEEE Transactions on Neural Systems and Rehabilitation Engineering, 27(7), 1436–1448.',
    'Dang, Q., Yin, J., Wang, B. ve Zheng, W. (2022). Deep learning based 2D human pose estimation: A survey. Tsinghua Science and Technology, 24(6), 663–676.',
    'Durnin, J. V. G. A. ve Womersley, J. (1974). Body fat assessed from total body density and its estimation from skinfold thickness. British Journal of Nutrition, 32(1), 77–97.',
    'EuropeActive. (2022). European health & fitness market report 2022. EuropeActive Publications.',
    'Jackson, A. S. ve Pollock, M. L. (1978). Generalized equations for predicting body density of men. British Journal of Nutrition, 40(3), 497–504.',
    'Kerr, Z. Y., Collins, C. L. ve Comstock, R. D. (2010). Epidemiology of weight training-related injuries. American Journal of Sports Medicine, 38(4), 765–771.',
    'Kok, M., Hol, J. D. ve Schoen, T. B. (2022). An automated physical therapy exercise assessment using pose estimation. Sensors, 22(12), 4584.',
    'Krizhevsky, A., Sutskever, I. ve Hinton, G. E. (2012). ImageNet classification with deep convolutional neural networks. Advances in Neural Information Processing Systems, 25, 1097–1105.',
    'Liao, Y., Vakanski, A. ve Xian, M. (2020). A deep learning framework for assessing physical rehabilitation exercises. IEEE Transactions on Neural Systems and Rehabilitation Engineering, 28(2), 468–477.',
    'Lugaresi, C., Tang, J., Nash, H., McClanahan, C., Ubowejr, E., Hock, C. ve Grundmann, M. (2019). MediaPipe: A framework for building perception pipelines. Retrieved from https://arxiv.org/abs/1906.08172',
    'Newell, A., Yang, K. ve Deng, J. (2016). Stacked hourglass networks for human pose estimation. In B. Leibe, J. Matas, N. Sebe ve M. Welling (Eds.), Computer Vision – ECCV 2016 (s. 483–499). Springer.',
    'OpenPowerlifting. (2023). OpenPowerlifting database. Retrieved from https://www.openpowerlifting.org/',
    'Pirsiavash, H. ve Ramanan, D. (2014). Assessing the quality of actions. In D. Fleet, T. Pajdla, B. Schiele ve T. Tuytelaars (Eds.), Computer Vision – ECCV 2014 (s. 556–571). Springer.',
    'Shotton, J., Fitzgibbon, A., Cook, M., Sharp, T., Finocchio, M., Moore, R., Kipman, A. ve Blake, A. (2011). Real-time human pose recognition in parts from single depth images. 2011 IEEE Conference on Computer Vision and Pattern Recognition (s. 1297–1304). IEEE.',
    'Sun, K., Xiao, B., Liu, D. ve Wang, J. (2019). Deep high-resolution representation learning for visual recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence, 43(10), 3349–3364.',
    'U.S. Centers for Disease Control and Prevention. (2023). National Health and Nutrition Examination Survey (NHANES). Retrieved from https://www.cdc.gov/nchs/nhanes/',
    'U.S. Army Research Laboratory. (2012). Anthropometric Survey of U.S. Army Personnel: Methods and Summary Statistics (ANSUR II). Defense Technical Information Center.',
]

for ref in refs:
    story.append(Paragraph(E(ref), ref_style))

# ── EKLER ────────────────────────────────────────────────────────────────────

story.append(page_break())
story.append(H1('EKLER'))
story.append(H2('Ek A. Sistem Modül Yapısı'))

story.append(Paragraph(
    'Proje kök dizininde ana bileşenler: main.py, pose_detector.py, gesture_detector.py, '
    'config.py, profiles.py. Alt dizinler ve işlevleri:',
    ek_body))

story += make_tbl(None,
    ['Dizin', 'İşlev'],
    [
        ['exercises/', '19 egzersiz analiz motoru; BaseExercise soyut sınıfı'],
        ['ml/', 'Form sınıflandırıcı, video madenci, model eğitici, veri toplayıcı'],
        ['bodyfat/', 'Vücut yağ tahmini; silüet ve antropometri entegrasyonu'],
        ['strength/', 'OpenPowerlifting normları; Dots skoru hesaplayıcı'],
        ['nutrition/', 'Türk gıda veritabanı; kalori hedef hesaplayıcı'],
        ['progress/', 'Seans bazlı ilerleme kaydedicisi; JSON saklama'],
        ['feedback/', 'HUD (visual_feedback.py); ses sistemi (audio_feedback.py)'],
        ['utils/', 'Açı ve mesafe hesaplayıcı; landmark dönüşüm araçları'],
        ['tools/', 'Toplu video işleyici; pipeline; sentetik veri üretici'],
    ],
    col_widths=[3.5*cm, 11.8*cm]
)

story.append(H2('Ek B. Kullanılan Kütüphaneler'))

story += make_tbl(None,
    ['Kütüphane', 'Sürüm', 'Kullanım Amacı'],
    [
        ['mediapipe', '>= 0.10.0', 'İskelet çıkarımı, segmentasyon, el jesti'],
        ['opencv-python', '>= 4.8.0', 'Kamera akışı, HUD çizimi'],
        ['scikit-learn', '>= 1.3.0', 'RandomForest, GradientBoosting, StandardScaler'],
        ['numpy', '>= 1.24.0', 'Açı hesaplama, istatistik'],
        ['pandas', '>= 2.0.0', 'CSV yönetimi, veri analizi'],
        ['joblib', 'scikit-learn ile', 'Model kaydetme/yükleme (.joblib)'],
        ['yt-dlp', 'Son sürüm', 'YouTube video indirme'],
    ],
    col_widths=[3.8*cm, 3.5*cm, 8.0*cm]
)

story.append(H2('Ek C. Temel Konfigürasyon Parametreleri'))

story.append(Paragraph(
    'config.py\'de tanımlanan kritik sabitler: CAMERA_WIDTH=1280, CAMERA_HEIGHT=720; '
    'PROCESS_WIDTH=480, PROCESS_HEIGHT=270; MIN_VISIBILITY=0.40; '
    'AUDIO_COOLDOWN=1.5 sn; CORRECT_RATIO_THRESHOLD=0.60; '
    'ML_CONFIDENCE_THRESHOLD=0.55; MIN_SAMPLES_PER_CLASS=5; '
    'RF_N_ESTIMATORS=300; MIN_SAMPLES_LEAF=3; '
    'BF_BUFFER_SIZE=25 (vücut yağ ölçüm kare ortalaması).',
    ek_body))

# ── Build ─────────────────────────────────────────────────────────────────────

doc = build_doc()
doc.build(story)
print(f'PDF olusturuldu: {OUTPUT}')

import os
size = os.path.getsize(OUTPUT)
print(f'Dosya boyutu: {size//1024} KB')
