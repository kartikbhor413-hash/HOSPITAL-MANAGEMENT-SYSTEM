"""
Smart Hospital Management System — PDF Presentation Generator
Generates: SHMS_Presentation.pdf (10 slides, A4 landscape, professional layout)
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line
from reportlab.graphics import renderPDF

# ─── Color Palette ───────────────────────────────────────────────────────────
C_DARK     = colors.HexColor('#0f172a')
C_NAVY     = colors.HexColor('#1e3a5f')
C_BLUE     = colors.HexColor('#1e40af')
C_SKY      = colors.HexColor('#0ea5e9')
C_TEAL     = colors.HexColor('#0d9488')
C_GREEN    = colors.HexColor('#16a34a')
C_RED      = colors.HexColor('#dc2626')
C_ORANGE   = colors.HexColor('#ea580c')
C_AMBER    = colors.HexColor('#d97706')
C_WHITE    = colors.white
C_LIGHT    = colors.HexColor('#f1f5f9')
C_MUTED    = colors.HexColor('#64748b')
C_BORDER   = colors.HexColor('#cbd5e1')
C_ACCENT   = colors.HexColor('#7c3aed')

PAGE_W, PAGE_H = landscape(A4)

# ─── Asset Paths ─────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
LOGO_PATH     = os.path.join(BASE, 'static', 'images', 'hospital_logo.png')
ICON_PATH     = os.path.join(BASE, 'static', 'images', 'hospital_icon.png')
BUILDING_PATH = os.path.join(BASE, 'static', 'images', 'hospital_building.jpg')
OUTPUT_PATH   = os.path.join(BASE, 'SHMS_Presentation.pdf')

# ─── Helper: slide canvas painter ────────────────────────────────────────────
class SlideCanvas:
    """Wraps reportlab canvas to paint each page as a slide."""

    def __init__(self, c: canvas.Canvas):
        self.c = c
        self.w = PAGE_W
        self.h = PAGE_H

    # --- Backgrounds ---
    def bg_gradient(self, top_color=C_DARK, bottom_color=C_NAVY):
        """Simple two-band gradient approximation via stacked thin rects."""
        steps = 80
        for i in range(steps):
            frac = i / steps
            r = top_color.red   + frac * (bottom_color.red   - top_color.red)
            g = top_color.green + frac * (bottom_color.green - top_color.green)
            b = top_color.blue  + frac * (bottom_color.blue  - top_color.blue)
            band_h = self.h / steps
            self.c.setFillColorRGB(r, g, b)
            self.c.rect(0, self.h - (i + 1) * band_h, self.w, band_h, stroke=0, fill=1)

    def bg_light(self):
        self.c.setFillColor(C_LIGHT)
        self.c.rect(0, 0, self.w, self.h, stroke=0, fill=1)

    def accent_bar(self, y, height=3, color=C_SKY):
        self.c.setFillColor(color)
        self.c.rect(0, y, self.w, height, stroke=0, fill=1)

    def side_panel(self, width=6*cm, color=C_BLUE):
        self.c.setFillColor(color)
        self.c.rect(0, 0, width, self.h, stroke=0, fill=1)

    # --- Text helpers ---
    def title(self, text, y, size=34, color=C_WHITE, bold=True):
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawCentredString(self.w / 2, y, text)

    def sub(self, text, y, size=14, color=C_SKY, align='center'):
        self.c.setFont('Helvetica', size)
        self.c.setFillColor(color)
        if align == 'center':
            self.c.drawCentredString(self.w / 2, y, text)
        elif align == 'left':
            self.c.drawString(1.5*cm, y, text)
        else:
            self.c.drawRightString(self.w - 1.5*cm, y, text)

    def body(self, text, y, x=2*cm, size=11, color=C_DARK):
        self.c.setFont('Helvetica', size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, text)

    def badge(self, text, x, y, bg=C_RED, fg=C_WHITE, w=3.5*cm, h=0.7*cm, radius=4):
        self.c.setFillColor(bg)
        self.c.roundRect(x, y, w, h, radius, stroke=0, fill=1)
        self.c.setFont('Helvetica-Bold', 9)
        self.c.setFillColor(fg)
        self.c.drawCentredString(x + w/2, y + h/4, text)

    def icon_bullet(self, symbol, text, x, y, size=11, icon_color=C_SKY):
        self.c.setFont('Helvetica-Bold', size)
        self.c.setFillColor(icon_color)
        self.c.drawString(x, y, symbol)
        self.c.setFont('Helvetica', size)
        self.c.setFillColor(C_DARK)
        self.c.drawString(x + 0.55*cm, y, text)

    def draw_logo(self, x, y, width=4*cm):
        if os.path.exists(LOGO_PATH):
            try:
                img = ImageReader(LOGO_PATH)
                iw, ih = img.getSize()
                ratio = width / iw
                self.c.drawImage(LOGO_PATH, x, y, width=width, height=ih*ratio, mask='auto')
                return ih * ratio
            except Exception:
                pass
        return 0

    def draw_icon(self, x, y, size=1.5*cm):
        if os.path.exists(ICON_PATH):
            try:
                img = ImageReader(ICON_PATH)
                self.c.drawImage(ICON_PATH, x, y, width=size, height=size, mask='auto')
            except Exception:
                pass

    def footer(self, slide_num, total=10):
        # Footer bar
        self.c.setFillColor(C_NAVY)
        self.c.rect(0, 0, self.w, 1.1*cm, stroke=0, fill=1)
        self.c.setFont('Helvetica', 8)
        self.c.setFillColor(C_SKY)
        self.c.drawString(1*cm, 0.35*cm, 'Smart Hospital Management System  |  Final Year Project')
        self.c.setFillColor(C_WHITE)
        self.c.drawRightString(self.w - 1*cm, 0.35*cm, f'Slide {slide_num} / {total}')
        # Accent line above footer
        self.c.setFillColor(C_SKY)
        self.c.rect(0, 1.1*cm, self.w, 0.12*cm, stroke=0, fill=1)

    def heading_bar(self, title, y=None, bg=C_BLUE, fg=C_WHITE, size=18):
        if y is None:
            y = self.h - 2.8*cm
        self.c.setFillColor(bg)
        self.c.rect(0, y, self.w, 1.6*cm, stroke=0, fill=1)
        self.c.setFont('Helvetica-Bold', size)
        self.c.setFillColor(fg)
        self.c.drawString(1.5*cm, y + 0.45*cm, title)
        # Accent stripe
        self.c.setFillColor(C_SKY)
        self.c.rect(0, y, 0.35*cm, 1.6*cm, stroke=0, fill=1)

    def divider(self, y, color=C_BORDER, width=None, x=1.5*cm):
        w = width or (self.w - 2*x)
        self.c.setStrokeColor(color)
        self.c.setLineWidth(0.5)
        self.c.line(x, y, x + w, y)

    def card(self, x, y, w, h, bg=C_WHITE, border=C_BORDER, radius=6):
        # Shadow
        self.c.setFillColor(colors.HexColor('#00000015'))
        self.c.roundRect(x+2, y-2, w, h, radius, stroke=0, fill=1)
        # Card body
        self.c.setFillColor(bg)
        self.c.setStrokeColor(border)
        self.c.setLineWidth(0.5)
        self.c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

    def colored_rect(self, x, y, w, h, color, radius=0):
        self.c.setFillColor(color)
        if radius:
            self.c.roundRect(x, y, w, h, radius, stroke=0, fill=1)
        else:
            self.c.rect(x, y, w, h, stroke=0, fill=1)


# ─── Individual Slide Painters ────────────────────────────────────────────────

def slide_01_title(c: canvas.Canvas):
    """Slide 1: Title / Cover Slide"""
    sc = SlideCanvas(c)
    # Full dark gradient bg
    sc.bg_gradient(C_DARK, C_NAVY)

    # Hospital building photo as semi-transparent overlay strip
    if os.path.exists(BUILDING_PATH):
        try:
            sc.c.saveState()
            sc.c.setFillAlpha(0.18)
            sc.c.drawImage(BUILDING_PATH, 0, 0, width=PAGE_W, height=PAGE_H, mask='auto', preserveAspectRatio=False)
            sc.c.restoreState()
        except Exception:
            pass

    # Left blue accent stripe
    sc.colored_rect(0, 0, 0.6*cm, PAGE_H, C_SKY)

    # Top-right corner decoration
    sc.colored_rect(PAGE_W - 8*cm, PAGE_H - 0.5*cm, 8*cm, 0.5*cm, C_SKY)
    sc.colored_rect(PAGE_W - 4*cm, PAGE_H - 3.5*cm, 4*cm, 3*cm, colors.HexColor('#0ea5e920'))

    # Logo top-left
    sc.draw_logo(1.2*cm, PAGE_H - 4*cm, width=5*cm)

    # Cross decoration circle (top right)
    sc.c.setFillColor(colors.HexColor('#0ea5e912'))
    sc.c.circle(PAGE_W - 3*cm, PAGE_H - 2*cm, 3*cm, stroke=0, fill=1)
    sc.c.setFillColor(colors.HexColor('#0ea5e918'))
    sc.c.circle(PAGE_W - 1*cm, PAGE_H*0.5, 5*cm, stroke=0, fill=1)

    # Tag line
    sc.c.setFont('Helvetica', 10)
    sc.c.setFillColor(C_SKY)
    sc.c.drawCentredString(PAGE_W/2, PAGE_H - 3.5*cm, '● FINAL YEAR PROJECT PRESENTATION ●')

    # Main title
    sc.c.setFont('Helvetica-Bold', 38)
    sc.c.setFillColor(C_WHITE)
    sc.c.drawCentredString(PAGE_W/2, PAGE_H/2 + 2.8*cm, 'Smart Hospital')
    sc.c.drawCentredString(PAGE_W/2, PAGE_H/2 + 1.4*cm, 'Management System')

    # Blue underline
    sc.c.setFillColor(C_SKY)
    sc.c.rect(PAGE_W/2 - 6*cm, PAGE_H/2 + 1.0*cm, 12*cm, 0.18*cm, stroke=0, fill=1)

    # Subtitle
    sc.c.setFont('Helvetica', 14)
    sc.c.setFillColor(colors.HexColor('#94a3b8'))
    sc.c.drawCentredString(PAGE_W/2, PAGE_H/2 + 0.2*cm,
        'A Full-Stack Python Flask · JSON Storage · Role-Based ERP for Healthcare')

    # Info chips
    chips = [('Python Flask', C_BLUE), ('JSON Storage', C_TEAL), ('7 RBAC Roles', C_ACCENT),
             ('REST API', C_GREEN), ('Responsive UI', C_ORANGE)]
    chip_w = 3.2*cm
    gap = 0.5*cm
    total_chips_w = len(chips) * chip_w + (len(chips)-1) * gap
    start_x = PAGE_W/2 - total_chips_w/2
    for i, (label, bg) in enumerate(chips):
        cx = start_x + i * (chip_w + gap)
        sc.colored_rect(cx, PAGE_H/2 - 1.8*cm, chip_w, 0.7*cm, bg, radius=4)
        sc.c.setFont('Helvetica-Bold', 8)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(cx + chip_w/2, PAGE_H/2 - 1.5*cm, label)

    # Bottom info
    sc.c.setFont('Helvetica', 10)
    sc.c.setFillColor(colors.HexColor('#94a3b8'))
    sc.c.drawCentredString(PAGE_W/2, PAGE_H/2 - 3*cm, f'Hospital Center Health  |  {datetime.now().strftime("%B %Y")}')

    sc.footer(1)


def slide_02_problem(c: canvas.Canvas):
    """Slide 2: Problem Statement & Motivation"""
    sc = SlideCanvas(c)
    sc.bg_light()
    sc.heading_bar('Problem Statement & Motivation')

    # Two-column layout
    col1_x = 1.5*cm
    col2_x = PAGE_W/2 + 0.5*cm
    col_w = PAGE_W/2 - 2.5*cm
    top_y = PAGE_H - 4.2*cm

    # Column 1 — Problems
    sc.card(col1_x, 1.5*cm, col_w, top_y - 1.8*cm, bg=colors.HexColor('#fff1f2'), border=C_RED)
    sc.c.setFont('Helvetica-Bold', 13)
    sc.c.setFillColor(C_RED)
    sc.c.drawString(col1_x + 0.4*cm, top_y - 0.5*cm, '⚠  Current Hospital Challenges')
    problems = [
        ('Manual paper records slow down patient care',),
        ('No real-time bed availability visibility',),
        ('Prescription errors due to illegible handwriting',),
        ('Billing errors & revenue leakage from manual calc',),
        ('No triage priority system for emergencies',),
        ('Pharmacy stock-outs & expired medicine risks',),
        ('No audit trail for staff actions',),
    ]
    for i, (p,) in enumerate(problems):
        y = top_y - 1.4*cm - i * 0.75*cm
        sc.c.setFillColor(C_RED)
        sc.c.circle(col1_x + 0.6*cm, y + 0.2*cm, 0.12*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica', 10)
        sc.c.setFillColor(C_DARK)
        sc.c.drawString(col1_x + 0.95*cm, y, p)

    # Column 2 — Solutions
    sc.card(col2_x, 1.5*cm, col_w, top_y - 1.8*cm, bg=colors.HexColor('#f0fdf4'), border=C_GREEN)
    sc.c.setFont('Helvetica-Bold', 13)
    sc.c.setFillColor(C_GREEN)
    sc.c.drawString(col2_x + 0.4*cm, top_y - 0.5*cm, '✔  SHMS Solution')
    solutions = [
        'Centralized electronic patient records (EHR)',
        'Real-time bed census dashboard',
        'Digital e-prescription module',
        'Automated multi-factor billing engine',
        'Rule-based emergency priority classifier',
        'Inventory expiry & stock alert watcher',
        'Activity logger middleware for all actions',
    ]
    for i, s in enumerate(solutions):
        y = top_y - 1.4*cm - i * 0.75*cm
        sc.c.setFillColor(C_GREEN)
        sc.c.circle(col2_x + 0.6*cm, y + 0.2*cm, 0.12*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica', 10)
        sc.c.setFillColor(C_DARK)
        sc.c.drawString(col2_x + 0.95*cm, y, s)

    sc.divider(PAGE_H - 3.0*cm, color=C_BORDER)
    sc.footer(2)


def slide_03_architecture(c: canvas.Canvas):
    """Slide 3: System Architecture"""
    sc = SlideCanvas(c)
    sc.bg_gradient(colors.HexColor('#0f172a'), colors.HexColor('#1e293b'))
    sc.heading_bar('System Architecture', bg=colors.HexColor('#1e40af'))

    # Layer boxes
    layers = [
        ('PRESENTATION LAYER', 'HTML5 · CSS3 · Vanilla JS (Fetch API ES6+)',
         C_TEAL,    PAGE_H - 4.2*cm, '7 Role Dashboards · Responsive Grid'),
        ('APPLICATION LAYER', 'Python 3.x · Flask · Flask-Session · Werkzeug',
         C_BLUE,    PAGE_H - 6.2*cm, 'REST API · RBAC Decorators · Session Auth'),
        ('BUSINESS LOGIC',    'helpers/ — json_db.py · auth.py · emergency_logic.py',
         C_ACCENT,  PAGE_H - 8.2*cm, 'Billing Engine · Triage · Inventory Watcher'),
        ('PERSISTENCE LAYER', 'data/ — 15 JSON files with FileLock + Atomic Writes',
         C_GREEN,   PAGE_H - 10.2*cm, 'Thread-Safe · Process-Safe · Auto-ID Generation'),
    ]

    box_x = 2*cm
    box_w = PAGE_W - 4*cm
    box_h = 1.7*cm

    for label, sublabel, color, y, detail in layers:
        # Color strip
        sc.colored_rect(box_x, y, 0.5*cm, box_h, color, radius=0)
        # Box
        sc.c.setFillColor(colors.HexColor('#1e293b'))
        sc.c.setStrokeColor(color)
        sc.c.setLineWidth(1)
        sc.c.roundRect(box_x, y, box_w, box_h, 4, stroke=1, fill=1)
        # Label
        sc.c.setFont('Helvetica-Bold', 11)
        sc.c.setFillColor(color)
        sc.c.drawString(box_x + 0.8*cm, y + box_h - 0.55*cm, label)
        # Sub
        sc.c.setFont('Helvetica', 9)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawString(box_x + 0.8*cm, y + 0.55*cm, sublabel)
        # Detail badge right
        sc.c.setFont('Helvetica', 8)
        sc.c.setFillColor(colors.HexColor('#94a3b8'))
        sc.c.drawRightString(box_x + box_w - 0.4*cm, y + box_h/2 - 0.1*cm, detail)
        # Arrow below (except last)
        if y != layers[-1][3]:
            ax = PAGE_W / 2
            ay = y
            sc.c.setStrokeColor(C_SKY)
            sc.c.setLineWidth(1.5)
            sc.c.line(ax, ay, ax, ay - 0.4*cm)
            # Arrowhead
            sc.c.setFillColor(C_SKY)
            sc.c.setFillColor(C_SKY)
            p = sc.c.beginPath()
            p.moveTo(ax - 0.2*cm, ay - 0.35*cm)
            p.lineTo(ax + 0.2*cm, ay - 0.35*cm)
            p.lineTo(ax, ay - 0.6*cm)
            p.close()
            sc.c.drawPath(p, stroke=0, fill=1)

    # DB files panel
    db_y = PAGE_H - 12.2*cm
    sc.colored_rect(2*cm, db_y, box_w, 1.4*cm, colors.HexColor('#134e4a'), radius=4)
    sc.c.setFont('Helvetica-Bold', 9)
    sc.c.setFillColor(C_TEAL)
    sc.c.drawString(2.5*cm, db_y + 0.9*cm, '15 JSON Collections:')
    files = 'users · patients · doctors · nurses · appointments · medical_records · prescriptions'
    files2 = 'medicines · laboratory_tests · lab_reports · beds · bills · emergency · activity_logs · staff'
    sc.c.setFont('Helvetica', 8)
    sc.c.setFillColor(C_WHITE)
    sc.c.drawString(2.5*cm, db_y + 0.5*cm, files)
    sc.c.drawString(2.5*cm, db_y + 0.15*cm, files2)

    sc.footer(3)


def slide_04_roles(c: canvas.Canvas):
    """Slide 4: 7 RBAC Roles"""
    sc = SlideCanvas(c)
    sc.bg_light()
    sc.heading_bar('7 Role-Based Access Control (RBAC) Roles')

    roles = [
        ('👨‍💼', 'Admin',         C_BLUE,   'Full system control, user management, reports, system config'),
        ('👨‍⚕️', 'Doctor',        C_TEAL,   'OPD consultations, e-prescriptions, lab order requests'),
        ('👩‍⚕️', 'Nurse',         C_GREEN,  'Bed allocation, patient vitals, discharge management'),
        ('🏥', 'Receptionist',  C_ACCENT, 'Patient registration, appointment booking, billing generation'),
        ('🔬', 'Laboratory',    C_ORANGE, 'Test catalog, diagnostic orders, lab report upload'),
        ('💊', 'Pharmacy',      C_RED,    'Medicine inventory, expiry alerts, prescription dispensing'),
        ('🧑‍🤝‍🧑', 'Patient',       C_MUTED,  'View own appointments, prescriptions, reports, pay bills'),
    ]

    card_w = (PAGE_W - 3*cm) / 4
    card_h = 3.2*cm
    gap = 0.3*cm
    # Row 1: 4 roles
    for i, (icon, name, color, desc) in enumerate(roles[:4]):
        cx = 1.5*cm + i * (card_w + gap)
        cy = PAGE_H - 5.5*cm
        sc.card(cx, cy, card_w, card_h, bg=C_WHITE)
        sc.colored_rect(cx, cy + card_h - 0.35*cm, card_w, 0.35*cm, color, radius=0)
        sc.c.setFont('Helvetica', 20)
        sc.c.setFillColor(color)
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 1.2*cm, icon)
        sc.c.setFont('Helvetica-Bold', 11)
        sc.c.setFillColor(color)
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 1.8*cm, name)
        sc.c.setFont('Helvetica', 7.5)
        sc.c.setFillColor(C_MUTED)
        # wrap description
        words = desc.split(', ')
        line1 = ', '.join(words[:2])
        line2 = ', '.join(words[2:]) if len(words) > 2 else ''
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 2.4*cm, line1)
        if line2:
            sc.c.drawCentredString(cx + card_w/2, cy + card_h - 2.9*cm, line2)

    # Row 2: 3 roles (centered)
    offset = (PAGE_W - 3 * (card_w + gap)) / 2
    for i, (icon, name, color, desc) in enumerate(roles[4:]):
        cx = offset + i * (card_w + gap)
        cy = PAGE_H - 5.5*cm - card_h - 0.5*cm
        sc.card(cx, cy, card_w, card_h, bg=C_WHITE)
        sc.colored_rect(cx, cy + card_h - 0.35*cm, card_w, 0.35*cm, color, radius=0)
        sc.c.setFont('Helvetica', 20)
        sc.c.setFillColor(color)
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 1.2*cm, icon)
        sc.c.setFont('Helvetica-Bold', 11)
        sc.c.setFillColor(color)
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 1.8*cm, name)
        sc.c.setFont('Helvetica', 7.5)
        sc.c.setFillColor(C_MUTED)
        words = desc.split(', ')
        line1 = ', '.join(words[:2])
        line2 = ', '.join(words[2:]) if len(words) > 2 else ''
        sc.c.drawCentredString(cx + card_w/2, cy + card_h - 2.4*cm, line1)
        if line2:
            sc.c.drawCentredString(cx + card_w/2, cy + card_h - 2.9*cm, line2)

    # RBAC note
    note_y = PAGE_H - 12.5*cm
    sc.colored_rect(1.5*cm, note_y, PAGE_W - 3*cm, 0.85*cm, colors.HexColor('#eff6ff'), radius=4)
    sc.c.setFont('Helvetica-Bold', 9)
    sc.c.setFillColor(C_BLUE)
    sc.c.drawString(2*cm, note_y + 0.3*cm,
        'RBAC Enforcement: @login_required + @role_required([...]) Flask decorators on every sensitive API endpoint.')

    sc.divider(PAGE_H - 3*cm)
    sc.footer(4)


def slide_05_emergency(c: canvas.Canvas):
    """Slide 5: Smart Emergency Priority Engine"""
    sc = SlideCanvas(c)
    sc.bg_gradient(colors.HexColor('#1a0a0a'), colors.HexColor('#1f1f2e'))
    sc.heading_bar('Smart Emergency Priority Engine', bg=C_RED)

    levels = [
        ('CRITICAL', C_RED,    '#3b0000', [
            'SpO2 < 85%',
            'Systolic BP > 180 or < 80 mmHg',
            'Unconscious / Unresponsive',
            'Severe Trauma / Hemorrhage',
        ]),
        ('HIGH',     C_ORANGE, '#2a1500', [
            'SpO2 85–92%',
            'Severe Abdominal Pain',
            'High Fever > 103°F',
            'Deep Lacerations',
        ]),
        ('MEDIUM',   C_AMBER,  '#1a1400', [
            'SpO2 93–95%',
            'Moderate Fractures',
            'Persistent Vomiting',
            'Moderate Chest Pain',
        ]),
        ('LOW',      C_GREEN,  '#001a00', [
            'Stable Vitals',
            'Minor Injuries',
            'Mild Fever < 99°F',
            'Routine Consultation',
        ]),
    ]

    card_w = (PAGE_W - 3*cm) / 4 - 0.2*cm
    card_h = 6.5*cm
    gap = 0.35*cm
    base_x = 1.5*cm
    base_y = PAGE_H - 12.5*cm

    for i, (level, color, bg_hex, criteria) in enumerate(levels):
        cx = base_x + i * (card_w + gap)
        sc.c.setFillColor(colors.HexColor(bg_hex))
        sc.c.setStrokeColor(color)
        sc.c.setLineWidth(1.5)
        sc.c.roundRect(cx, base_y, card_w, card_h, 6, stroke=1, fill=1)

        # Header
        sc.colored_rect(cx, base_y + card_h - 1*cm, card_w, 1*cm, color, radius=0)
        sc.c.setFont('Helvetica-Bold', 12)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(cx + card_w/2, base_y + card_h - 0.65*cm, level)

        for j, criterion in enumerate(criteria):
            cy = base_y + card_h - 1.7*cm - j * 0.95*cm
            sc.c.setFillColor(color)
            sc.c.circle(cx + 0.5*cm, cy + 0.2*cm, 0.1*cm, stroke=0, fill=1)
            sc.c.setFont('Helvetica', 8.5)
            sc.c.setFillColor(C_WHITE)
            sc.c.drawString(cx + 0.75*cm, cy, criterion)

    # Bed alert note
    note_y = base_y - 1.0*cm
    sc.colored_rect(1.5*cm, note_y, PAGE_W - 3*cm, 0.65*cm, colors.HexColor('#7f1d1d'), radius=4)
    sc.c.setFont('Helvetica-Bold', 9)
    sc.c.setFillColor(C_WHITE)
    sc.c.drawString(2*cm, note_y + 0.2*cm,
        '⚠  Auto-Alert: If CRITICAL patient arrives and ICU/Emergency beds = 0, dashboard alert triggers immediately.')

    sc.footer(5)


def slide_06_billing(c: canvas.Canvas):
    """Slide 6: Automated Billing Engine"""
    sc = SlideCanvas(c)
    sc.bg_light()
    sc.heading_bar('Automated Multi-Factor Billing Engine')

    # Formula box
    formula_y = PAGE_H - 5.5*cm
    sc.colored_rect(1.5*cm, formula_y, PAGE_W - 3*cm, 1.8*cm, colors.HexColor('#eff6ff'), radius=6)
    sc.c.setFont('Helvetica-Bold', 10)
    sc.c.setFillColor(C_BLUE)
    sc.c.drawString(2*cm, formula_y + 1.3*cm, 'Billing Formula:')
    sc.c.setFont('Helvetica', 11)
    sc.c.setFillColor(C_DARK)
    sc.c.drawCentredString(PAGE_W/2, formula_y + 0.65*cm,
        'Total Bill  =  Consultation Fee  +  (Bed Rate × Days)  +  Σ Lab Test Prices  +  Σ (Medicine Price × Qty)')

    # Component cards
    components = [
        ('Consultation\nFee', C_BLUE,   'Fixed fee per doctor\nOPD / specialist visit',    'e.g.  Rs. 500'),
        ('Bed Charges',       C_TEAL,   'Daily rate × total days\nadmitted in ward/ICU',    'e.g.  Rs. 1,200/day'),
        ('Lab Tests',         C_ACCENT, 'Sum of all ordered\ndiagnostic test prices',        'e.g.  CBC Rs.350, X-Ray Rs.700'),
        ('Medicine Cost',     C_GREEN,  'Price × quantity for\nevery prescription item',    'e.g.  2×Rs.45 + 1×Rs.120'),
    ]

    card_w = (PAGE_W - 3.5*cm) / 4 - 0.15*cm
    card_h = 4.2*cm
    gap = 0.35*cm
    base_x = 1.5*cm
    base_y = PAGE_H - 11*cm

    for i, (name, color, detail, example) in enumerate(components):
        cx = base_x + i * (card_w + gap)
        sc.card(cx, base_y, card_w, card_h)
        sc.colored_rect(cx, base_y + card_h - 0.4*cm, card_w, 0.4*cm, color, radius=0)
        sc.c.setFont('Helvetica-Bold', 10)
        sc.c.setFillColor(color)
        for j, ln in enumerate(name.split('\n')):
            sc.c.drawCentredString(cx + card_w/2, base_y + card_h - 1.0*cm - j*0.4*cm, ln)
        sc.c.setFont('Helvetica', 8)
        sc.c.setFillColor(C_MUTED)
        for j, ln in enumerate(detail.split('\n')):
            sc.c.drawCentredString(cx + card_w/2, base_y + card_h - 2.1*cm - j*0.4*cm, ln)
        # Example
        sc.colored_rect(cx + 0.3*cm, base_y + 0.4*cm, card_w - 0.6*cm, 0.65*cm, color, radius=3)
        sc.c.setFont('Helvetica', 7.5)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(cx + card_w/2, base_y + 0.62*cm, example)

    # Plus signs between cards
    for i in range(3):
        px = base_x + (i+1) * (card_w + gap) - gap/2 - 0.1*cm
        sc.c.setFont('Helvetica-Bold', 18)
        sc.c.setFillColor(C_MUTED)
        sc.c.drawCentredString(px, base_y + card_h/2 - 0.2*cm, '+')

    # Auto-generate note
    note_y = base_y - 1.0*cm
    sc.colored_rect(1.5*cm, note_y, PAGE_W - 3*cm, 0.7*cm, colors.HexColor('#f0fdf4'), radius=4)
    sc.c.setFont('Helvetica-Bold', 9)
    sc.c.setFillColor(C_GREEN)
    sc.c.drawString(2*cm, note_y + 0.25*cm,
        '✔  Bill auto-generated on patient discharge  |  Unique BILL-ID  |  Status: Pending → Paid  |  Stored in bills.json')

    sc.divider(PAGE_H - 3*cm)
    sc.footer(6)


def slide_07_json_storage(c: canvas.Canvas):
    """Slide 7: Thread-Safe Atomic JSON Storage"""
    sc = SlideCanvas(c)
    sc.bg_gradient(colors.HexColor('#0f172a'), colors.HexColor('#1e2744'))
    sc.heading_bar('Thread-Safe Atomic JSON Storage Engine', bg=C_TEAL)

    # Flow diagram
    steps = [
        ('Request In',       C_SKY,    'API write call\narrives'),
        ('Acquire\nFileLock', C_BLUE,   'filelock.FileLock\n(cached instance)'),
        ('Acquire\nRLock',    C_ACCENT, 'threading.RLock\n(thread safety)'),
        ('Read & Modify',    C_TEAL,   '_read_unlocked()\napply changes'),
        ('Atomic Write',     C_GREEN,  'tempfile + os.replace()\nno partial writes'),
        ('Release Locks',    C_ORANGE, 'RLock → FileLock\nreleased in order'),
    ]

    step_w = (PAGE_W - 3*cm) / len(steps) - 0.3*cm
    step_h = 3.5*cm
    gap = 0.5*cm
    base_x = 1.5*cm
    base_y = PAGE_H - 10*cm

    for i, (name, color, detail) in enumerate(steps):
        cx = base_x + i * (step_w + gap)
        # Box
        sc.c.setFillColor(colors.HexColor('#1e293b'))
        sc.c.setStrokeColor(color)
        sc.c.setLineWidth(1.5)
        sc.c.roundRect(cx, base_y, step_w, step_h, 5, stroke=1, fill=1)
        # Step number circle
        sc.c.setFillColor(color)
        sc.c.circle(cx + step_w/2, base_y + step_h - 0.6*cm, 0.45*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica-Bold', 10)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(cx + step_w/2, base_y + step_h - 0.72*cm, str(i+1))
        # Name
        sc.c.setFont('Helvetica-Bold', 8.5)
        sc.c.setFillColor(color)
        for j, ln in enumerate(name.split('\n')):
            sc.c.drawCentredString(cx + step_w/2, base_y + step_h - 1.4*cm - j*0.38*cm, ln)
        # Detail
        sc.c.setFont('Helvetica', 7.5)
        sc.c.setFillColor(colors.HexColor('#94a3b8'))
        for j, ln in enumerate(detail.split('\n')):
            sc.c.drawCentredString(cx + step_w/2, base_y + 0.95*cm - j*0.4*cm, ln)
        # Arrow (except last)
        if i < len(steps) - 1:
            ax = cx + step_w + 0.05*cm
            ay = base_y + step_h/2
            sc.c.setStrokeColor(C_SKY)
            sc.c.setLineWidth(1)
            sc.c.line(ax, ay, ax + gap - 0.1*cm, ay)
            sc.c.setFillColor(C_SKY)
            sc.c.polygon([ax+gap-0.1*cm, ay-0.15*cm,
                          ax+gap-0.1*cm, ay+0.15*cm,
                          ax+gap+0.2*cm, ay], stroke=0, fill=1)

    # Key features
    features = [
        ('No Race Conditions', 'FileLock blocks all processes from writing simultaneously'),
        ('No Partial Writes',  'Atomic os.replace() ensures complete file swap only'),
        ('No Deadlocks',       '_read_unlocked / _write_unlocked avoid re-entrant locking'),
        ('Auto ID Generation', 'PREFIX + zero-padded counter: PAT001, DOC001, BILL001'),
    ]
    feat_y = base_y - 0.7*cm
    feat_w = (PAGE_W - 3*cm) / 2 - 0.3*cm
    for i, (title, desc) in enumerate(features):
        fx = 1.5*cm + (i % 2) * (feat_w + 0.6*cm)
        fy = feat_y - (i // 2) * 0.75*cm
        sc.c.setFillColor(C_TEAL)
        sc.c.circle(fx + 0.2*cm, fy + 0.25*cm, 0.12*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica-Bold', 9)
        sc.c.setFillColor(C_TEAL)
        sc.c.drawString(fx + 0.45*cm, fy, title + ':')
        sc.c.setFont('Helvetica', 9)
        sc.c.setFillColor(colors.HexColor('#94a3b8'))
        sc.c.drawString(fx + 0.45*cm + (len(title)+1)*0.12*cm + 0.5*cm, fy, desc)

    sc.footer(7)


def slide_08_pharmacy(c: canvas.Canvas):
    """Slide 8: Pharmacy & Inventory Management"""
    sc = SlideCanvas(c)
    sc.bg_light()
    sc.heading_bar('Pharmacy & Inventory Management System')

    # Two columns
    col1_x = 1.5*cm
    col2_x = PAGE_W/2 + 0.5*cm
    col_w = PAGE_W/2 - 2.5*cm
    top_y = PAGE_H - 4.2*cm

    # --- Left: Inventory Logic ---
    sc.card(col1_x, 1.5*cm, col_w, top_y - 2*cm, bg=C_WHITE)
    sc.c.setFont('Helvetica-Bold', 12)
    sc.c.setFillColor(C_BLUE)
    sc.c.drawString(col1_x + 0.5*cm, top_y - 0.7*cm, 'Dynamic Status Evaluation')

    status_rows = [
        ('LOW_STOCK',      C_RED,    'stock_quantity <= min_threshold',            'Order immediately'),
        ('EXPIRING_SOON',  C_ORANGE, 'expiry_date - today <= 30 days',             'Return / dispose'),
        ('OK',             C_GREEN,  'quantity > threshold & expiry > 30 days',    'Normal operations'),
    ]
    for i, (status, color, condition, action) in enumerate(status_rows):
        row_y = top_y - 1.8*cm - i * 1.4*cm
        sc.colored_rect(col1_x + 0.3*cm, row_y, col_w - 0.6*cm, 1.1*cm, color, radius=4)
        sc.c.setFont('Helvetica-Bold', 9)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawString(col1_x + 0.6*cm, row_y + 0.7*cm, status)
        sc.c.setFont('Helvetica', 8)
        sc.c.drawString(col1_x + 0.6*cm, row_y + 0.3*cm, f'When: {condition}')
        sc.c.drawRightString(col1_x + col_w - 0.4*cm, row_y + 0.3*cm, f'Action: {action}')

    # Python logic
    code_y = top_y - 6*cm
    sc.colored_rect(col1_x + 0.3*cm, code_y, col_w - 0.6*cm, 1.8*cm, colors.HexColor('#0f172a'), radius=4)
    sc.c.setFont('Helvetica', 7.5)
    sc.c.setFillColor(C_SKY)
    code_lines = [
        "if stock_quantity <= min_threshold:",
        "    med['status'] = 'LOW_STOCK'",
        "if (expiry - today).days <= 30:",
        "    med['status'] = 'EXPIRING_SOON'",
    ]
    for i, ln in enumerate(code_lines):
        color = C_SKY if not ln.startswith(' ') else C_GREEN
        sc.c.setFillColor(color)
        sc.c.drawString(col1_x + 0.6*cm, code_y + 1.5*cm - i * 0.38*cm, ln)

    # --- Right: Features ---
    sc.card(col2_x, 1.5*cm, col_w, top_y - 2*cm, bg=C_WHITE)
    sc.c.setFont('Helvetica-Bold', 12)
    sc.c.setFillColor(C_ACCENT)
    sc.c.drawString(col2_x + 0.5*cm, top_y - 0.7*cm, 'Pharmacy Module Features')

    feats = [
        ('Prescription Dispensing', 'Doctor e-prescriptions → Pharmacy queue; dispense & deduct stock'),
        ('Supplier Management',     'Track supplier info, purchase dates, batch numbers'),
        ('Expiry Dashboard',        'Visual alert list of all medicines expiring within 30 days'),
        ('Stock Report',            'Admin can export current stock level report at any time'),
        ('Auto-Deduction',          'Stock quantity auto-decremented when prescription dispensed'),
        ('Threshold Alerts',        'Email/dashboard notify when stock hits minimum threshold'),
    ]
    for i, (title, desc) in enumerate(feats):
        fy = top_y - 1.4*cm - i * 1.1*cm
        sc.c.setFillColor(C_ACCENT)
        sc.c.circle(col2_x + 0.5*cm, fy + 0.3*cm, 0.12*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica-Bold', 9)
        sc.c.setFillColor(C_DARK)
        sc.c.drawString(col2_x + 0.8*cm, fy + 0.15*cm, title)
        sc.c.setFont('Helvetica', 8)
        sc.c.setFillColor(C_MUTED)
        sc.c.drawString(col2_x + 0.8*cm, fy - 0.25*cm, desc)

    sc.divider(PAGE_H - 3*cm)
    sc.footer(8)


def slide_09_api(c: canvas.Canvas):
    """Slide 9: REST API & System Demo Highlights"""
    sc = SlideCanvas(c)
    sc.bg_gradient(colors.HexColor('#0f172a'), colors.HexColor('#1e293b'))
    sc.heading_bar('REST API Endpoints & System Highlights', bg=C_ACCENT)

    # API table
    endpoints = [
        ('POST', '/api/login',              'Session-based auth with role mapping',   C_GREEN),
        ('GET',  '/api/patients',           'List all patients (Admin/Doctor)',        C_SKY),
        ('POST', '/api/patients',           'Register new patient (PAT-ID auto)',      C_SKY),
        ('GET',  '/api/appointments',       'Fetch appointments by role/doctor',       C_TEAL),
        ('POST', '/api/emergency',          'Auto-classify emergency priority',        C_RED),
        ('GET',  '/api/beds',               'Real-time bed census by ward',            C_TEAL),
        ('POST', '/api/beds',               'Allocate/discharge bed (Nurse)',          C_TEAL),
        ('POST', '/api/billing',            'Auto-calculate & generate bill',          C_ORANGE),
        ('GET',  '/api/medicines',          'List medicines + LOW_STOCK flags',        C_ACCENT),
        ('GET',  '/api/dashboard/stats',    'KPI aggregates for admin dashboard',      C_BLUE),
    ]

    row_h = 0.62*cm
    table_x = 1.5*cm
    table_w = PAGE_W - 3*cm
    col_widths = [1.4*cm, 5.5*cm, 9*cm, 1*cm]
    headers = ['Method', 'Endpoint', 'Description', '']

    header_y = PAGE_H - 4.3*cm
    sc.colored_rect(table_x, header_y, table_w, row_h, C_ACCENT, radius=0)
    xpos = table_x
    for i, h in enumerate(headers[:3]):
        sc.c.setFont('Helvetica-Bold', 9)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawString(xpos + 0.2*cm, header_y + 0.18*cm, h)
        xpos += col_widths[i]

    method_colors = {'GET': C_TEAL, 'POST': C_GREEN, 'PUT': C_ORANGE, 'DELETE': C_RED}
    for i, (method, path, desc, _) in enumerate(endpoints):
        row_y = header_y - (i+1) * row_h
        bg = colors.HexColor('#1e293b') if i % 2 == 0 else colors.HexColor('#162032')
        sc.colored_rect(table_x, row_y, table_w, row_h, bg)
        # Method badge
        mc = method_colors.get(method, C_MUTED)
        sc.colored_rect(table_x + 0.1*cm, row_y + 0.1*cm, 1.2*cm, row_h - 0.2*cm, mc, radius=3)
        sc.c.setFont('Helvetica-Bold', 7.5)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(table_x + 0.7*cm, row_y + 0.2*cm, method)
        # Path
        sc.c.setFont('Helvetica', 8.5)
        sc.c.setFillColor(C_SKY)
        sc.c.drawString(table_x + col_widths[0] + 0.2*cm, row_y + 0.18*cm, path)
        # Desc
        sc.c.setFont('Helvetica', 8.5)
        sc.c.setFillColor(colors.HexColor('#94a3b8'))
        sc.c.drawString(table_x + col_widths[0] + col_widths[1] + 0.2*cm, row_y + 0.18*cm, desc)

    # Highlights
    high_y = header_y - (len(endpoints)+1) * row_h - 0.4*cm
    highlights = [
        ('30+ REST Endpoints', C_SKY),
        ('9-Module Test Suite', C_GREEN),
        ('15 JSON Collections', C_TEAL),
        ('100% Tests Passed', C_GREEN),
        ('Seed Data Pre-loaded', C_ACCENT),
    ]
    hx = table_x
    hw = (PAGE_W - 3*cm) / len(highlights) - 0.2*cm
    for i, (hl, color) in enumerate(highlights):
        sc.colored_rect(hx + i*(hw+0.2*cm), high_y, hw, 0.7*cm, color, radius=4)
        sc.c.setFont('Helvetica-Bold', 8)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawCentredString(hx + i*(hw+0.2*cm) + hw/2, high_y + 0.25*cm, hl)

    sc.footer(9)


def slide_10_conclusion(c: canvas.Canvas):
    """Slide 10: Conclusion & Future Scope"""
    sc = SlideCanvas(c)
    sc.bg_gradient(C_DARK, C_NAVY)

    if os.path.exists(BUILDING_PATH):
        try:
            sc.c.saveState()
            sc.c.setFillAlpha(0.10)
            sc.c.drawImage(BUILDING_PATH, 0, 0, width=PAGE_W, height=PAGE_H,
                           mask='auto', preserveAspectRatio=False)
            sc.c.restoreState()
        except Exception:
            pass

    sc.colored_rect(0, 0, 0.6*cm, PAGE_H, C_GREEN)
    sc.heading_bar('Conclusion & Future Scope', bg=C_GREEN)

    # Achievements
    ach_y = PAGE_H - 4.5*cm
    sc.c.setFont('Helvetica-Bold', 13)
    sc.c.setFillColor(C_GREEN)
    sc.c.drawString(1.5*cm, ach_y, 'Key Achievements')
    sc.divider(ach_y - 0.2*cm, color=C_GREEN, width=5*cm, x=1.5*cm)

    achievements = [
        'Full-stack RBAC ERP with 7 distinct role dashboards',
        'Rule-based Smart Emergency Triage (CRITICAL/HIGH/MEDIUM/LOW)',
        'Thread-safe atomic JSON storage (FileLock + RLock + os.replace)',
        'Auto-billing engine with multi-factor formula calculation',
        'Dynamic pharmacy watcher: expiry & low-stock real-time alerts',
        'Activity logger middleware for complete audit trail',
        'Production-grade login UI: no auto-fill, caps lock, IT support modal',
    ]
    for i, ach in enumerate(achievements):
        ay = ach_y - 0.7*cm - i * 0.65*cm
        sc.c.setFillColor(C_GREEN)
        sc.c.circle(1.9*cm, ay + 0.25*cm, 0.1*cm, stroke=0, fill=1)
        sc.c.setFont('Helvetica', 10)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawString(2.2*cm, ay, ach)

    # Future scope
    fut_x = PAGE_W/2 + 0.5*cm
    fut_y = PAGE_H - 4.5*cm
    sc.c.setFont('Helvetica-Bold', 13)
    sc.c.setFillColor(C_SKY)
    sc.c.drawString(fut_x, fut_y, 'Future Scope')
    sc.divider(fut_y - 0.2*cm, color=C_SKY, width=5*cm, x=fut_x)

    future = [
        ('PostgreSQL / MongoDB migration',     C_BLUE),
        ('WebSocket real-time bed dashboard',  C_TEAL),
        ('ML-based disease prediction',        C_ACCENT),
        ('Mobile app (Flutter / React Native)',C_ORANGE),
        ('HL7 / FHIR EHR standard compliance', C_GREEN),
        ('SMS & Email notification gateway',   C_SKY),
        ('Telemedicine video consultation',    C_BLUE),
    ]
    for i, (item, color) in enumerate(future):
        iy = fut_y - 0.7*cm - i * 0.65*cm
        sc.badge(f'v{i+2}.0', fut_x, iy - 0.05*cm, bg=color, w=1.2*cm, h=0.45*cm)
        sc.c.setFont('Helvetica', 10)
        sc.c.setFillColor(C_WHITE)
        sc.c.drawString(fut_x + 1.4*cm, iy, item)

    # Thank you box
    ty_y = 1.3*cm
    sc.colored_rect(PAGE_W/4, ty_y, PAGE_W/2, 0.9*cm, C_SKY, radius=6)
    sc.c.setFont('Helvetica-Bold', 14)
    sc.c.setFillColor(C_WHITE)
    sc.c.drawCentredString(PAGE_W/2, ty_y + 0.28*cm, 'Thank You  —  Smart Hospital Management System')

    sc.footer(10)


# ─── Main PDF Assembly ────────────────────────────────────────────────────────

def build_pdf():
    print(f'Building PDF: {OUTPUT_PATH}')
    c = canvas.Canvas(OUTPUT_PATH, pagesize=landscape(A4))
    c.setTitle('Smart Hospital Management System — Final Year Project Presentation')
    c.setAuthor('Hospital Center Health — Development Team')
    c.setSubject('SHMS — Full-Stack Flask · JSON · RBAC Medical ERP')
    c.setCreator('ReportLab 5.0.1 — Python 3.x')

    slides = [
        ('Slide 1: Title',             slide_01_title),
        ('Slide 2: Problem Statement', slide_02_problem),
        ('Slide 3: Architecture',      slide_03_architecture),
        ('Slide 4: RBAC Roles',        slide_04_roles),
        ('Slide 5: Emergency Engine',  slide_05_emergency),
        ('Slide 6: Billing Engine',    slide_06_billing),
        ('Slide 7: JSON Storage',      slide_07_json_storage),
        ('Slide 8: Pharmacy',          slide_08_pharmacy),
        ('Slide 9: REST API',          slide_09_api),
        ('Slide 10: Conclusion',       slide_10_conclusion),
    ]

    for i, (name, fn) in enumerate(slides):
        print(f'  Generating {name}...')
        fn(c)
        if i < len(slides) - 1:
            c.showPage()

    c.save()
    print(f'\nPDF saved successfully: {OUTPUT_PATH}')
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f'File size: {size_kb:.1f} KB')

    # Copy to static/ for Flask serving
    static_out = os.path.join(BASE, 'static', 'SHMS_Presentation.pdf')
    import shutil
    shutil.copy2(OUTPUT_PATH, static_out)
    print(f'Also saved to: {static_out}')


if __name__ == '__main__':
    build_pdf()
