import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas
from config import Config

def number_to_words(n):
    """Simple number to Indian currency words converter"""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
            "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    n = int(round(float(n)))
    if n == 0:
        return "Zero Rupees Only"
    
    def convert_below_thousand(num):
        res = ""
        if num >= 100:
            res += ones[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            res += tens[num // 10] + " "
            num %= 10
        if num > 0:
            res += ones[num] + " "
        return res.strip()
    
    result = ""
    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    
    if crore > 0:
        result += convert_below_thousand(crore) + " Crore "
    if lakh > 0:
        result += convert_below_thousand(lakh) + " Lakh "
    if thousand > 0:
        result += convert_below_thousand(thousand) + " Thousand "
    if n > 0:
        result += convert_below_thousand(n)
        
    return f"{result.strip()} Rupees Only"

class NumberedCanvas(canvas.Canvas):
    """Canvas for background decorative borders and watermarks"""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations()
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self):
        self.saveState()
        # Outer decorative double border
        self.setStrokeColor(colors.HexColor("#8B0000")) # Crimson sacred border
        self.setLineWidth(3)
        self.rect(20, 20, 555, 802) # A4 size approx
        self.setStrokeColor(colors.HexColor("#D97706")) # Gold inner border
        self.setLineWidth(1)
        self.rect(24, 24, 547, 794)
        
        # Subtle watermark
        self.setFont("Helvetica-Bold", 45)
        self.setFillColor(colors.HexColor("#FEF3C7"), alpha=0.35)
        self.drawCentredString(297, 420, "BUDHI KALI MANDIR")
        self.setFont("Helvetica", 18)
        self.drawCentredString(297, 390, "KISHANGANJ (BIHAR)")
        
        self.restoreState()

def generate_pdf_receipt(donation_dict, output_path=None):
    """
    Generates a beautifully formatted PDF receipt using ReportLab.
    Returns bytes buffer or saves to output_path.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MandirTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1, # Center
        textColor=colors.HexColor("#8B0000")
    )
    
    subtitle_style = ParagraphStyle(
        'MandirSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#92400E")
    )
    
    meta_style = ParagraphStyle(
        'MandirMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#4B5563")
    )
    
    receipt_badge_style = ParagraphStyle(
        'ReceiptBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#8B0000")
    )
    
    cell_label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151")
    )
    
    cell_value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827")
    )

    blessing_style = ParagraphStyle(
        'BlessingStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#9A3412")
    )

    elements = []
    
    # Sanskrit Invocations
    elements.append(Paragraph("॥ OM KRIM KALIKAYE NAMAH ॥", ParagraphStyle(
        'Invocation', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.HexColor("#B45309")
    )))
    elements.append(Spacer(1, 4))
    
    # Header
    elements.append(Paragraph("SHREE SHREE 108 BUDHI KALI MANDIR (BURHI KALI MANDIR)", title_style))
    elements.append(Paragraph("Line Para, Kishanganj, Bihar - 855107", subtitle_style))
    elements.append(Paragraph("Historical Siddh Peeth Estd. 1902 | Reg. No: BR-KSG-BKM/1902-TRUST", meta_style))
    elements.append(Paragraph("Helpline: +91 6456 222108 / +91 94312 85510 | Email: sevadar@burhikalimandir.org", meta_style))
    elements.append(Spacer(1, 10))
    
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#D97706"), spaceBefore=2, spaceAfter=8))
    
    # Receipt Banner
    receipt_banner_data = [[
        Paragraph("OFFICIAL DONATION RECEIPT / दान सहयोग पावती", receipt_badge_style),
    ]]
    receipt_banner = Table(receipt_banner_data, colWidths=[520])
    receipt_banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(receipt_banner)
    elements.append(Spacer(1, 12))
    
    # Receipt Meta Row
    dt_str = str(donation_dict.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    meta_table_data = [
        [
            Paragraph(f"<b>Receipt No:</b> <font color='#8B0000'>{donation_dict.get('receipt_no', 'BKM-REC')}</font>", cell_label_style),
            Paragraph(f"<b>Date & Time:</b> {dt_str}", cell_label_style)
        ],
        [
            Paragraph(f"<b>Payment Mode:</b> {donation_dict.get('gateway', 'ONLINE')}", cell_label_style),
            Paragraph(f"<b>Payment Ref / ID:</b> {donation_dict.get('payment_id') or donation_dict.get('order_id') or 'N/A'}", cell_label_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 12))
    
    # Donor Information Table
    donor_info_data = [
        [Paragraph("Donor Name (दानदाता):", cell_label_style), Paragraph(str(donation_dict.get('donor_name', '-')), cell_value_style)],
        [Paragraph("Contact Number:", cell_label_style), Paragraph(str(donation_dict.get('phone', '-')), cell_value_style)],
        [Paragraph("Email Address:", cell_label_style), Paragraph(str(donation_dict.get('email') or 'N/A'), cell_value_style)],
        [Paragraph("Gotra (गोत्र):", cell_label_style), Paragraph(str(donation_dict.get('gotra') or 'Kashyap / General'), cell_value_style)],
        [Paragraph("Address / City:", cell_label_style), Paragraph(str(donation_dict.get('address') or 'Kishanganj, Bihar'), cell_value_style)],
        [Paragraph("PAN No. (For 80G):", cell_label_style), Paragraph(str(donation_dict.get('pan') or 'Not Provided'), cell_value_style)],
        [Paragraph("Seva / Purpose (दान संकल्प):", cell_label_style), Paragraph(f"<b>{str(donation_dict.get('purpose', 'General Mandir Seva'))}</b>", cell_value_style)],
    ]
    donor_table = Table(donor_info_data, colWidths=[150, 370])
    donor_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#F3F4F6")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F9FAFB")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(donor_table)
    elements.append(Spacer(1, 12))
    
    # Amount Box
    amt = float(donation_dict.get('amount', 0))
    amt_words = number_to_words(amt)
    amount_box_data = [
        [
            Paragraph("Total Contribution (दान राशि):", ParagraphStyle('AmtLbl', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1F2937"))),
            Paragraph(f"INR ₹{amt:,.2f}", ParagraphStyle('AmtVal', fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor("#8B0000"), alignment=2))
        ],
        [
            Paragraph(f"<b>In Words:</b> {amt_words}", ParagraphStyle('AmtWrd', fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#4B5563"))),
            Paragraph("<font color='#047857'><b>Status: COMPLETED</b></font>", ParagraphStyle('StLbl', fontName='Helvetica-Bold', fontSize=9, alignment=2))
        ]
    ]
    amount_table = Table(amount_box_data, colWidths=[340, 180])
    amount_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#10B981")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(amount_table)
    elements.append(Spacer(1, 16))
    
    # Divine Blessing & Notes
    elements.append(Paragraph(
        "\"May Shree Shree 108 Budhi Kali Mata (Burhi Kali) fulfill all your righteous wishes, protect your home, and bless you and your family with peace, health, and everlasting prosperity.\"",
        blessing_style
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "मां बूढ़ी काली आपके परिवार पर सदा अपनी असीम अनुकंपा बनाए रखें। आपका सहयोग मंदिर जीर्णोद्धार एवं नित्य भोग सेवा हेतु सादर स्वीकृत है।",
        ParagraphStyle('BlessingHi', fontName='Helvetica', fontSize=8, alignment=1, textColor=colors.HexColor("#6B7280"))
    ))
    elements.append(Spacer(1, 20))
    
    # Signatures & Seals
    sig_data = [
        [
            Paragraph("<b>Verified By:</b><br/>Mandir Accounts Section<br/>Line Para, Kishanganj", ParagraphStyle('Sig1', fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#6B7280"))),
            Paragraph("<b>[ DIGITALLY GENERATED SEAL ]</b><br/>SHREE SHREE 108 BUDHI KALI MANDIR<br/>MANAGEMENT TRUST, KISHANGANJ", ParagraphStyle('Seal', fontName='Helvetica-Bold', fontSize=8, alignment=1, textColor=colors.HexColor("#8B0000"))),
            Paragraph("<b>Authorized Signatory</b><br/>Secretary / Head Priest<br/>Budhi Kali Mandir Trust", ParagraphStyle('Sig2', fontName='Helvetica', fontSize=8, alignment=2, textColor=colors.HexColor("#6B7280")))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[170, 180, 170])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("This is a computer-generated digital receipt. No physical signature is required.", ParagraphStyle(
        'Disclaimer', fontName='Helvetica', fontSize=7, alignment=1, textColor=colors.HexColor("#9CA3AF")
    )))

    # Build Document
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    if output_path:
        return output_path
    
    buffer.seek(0)
    return buffer.getvalue()
