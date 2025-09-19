# app/pdf_generator.py
import os
import shutil
import tempfile
import traceback
from dataclasses import dataclass
from num2words import num2words

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import (
    LOGO_PATH, SIGNATURE_PATH, QR_CODE_PATH, FONT_PATH, FONT_BOLD_PATH,
    UI_PRIMARY_COLOR, UI_PRIMARY_COLOR_DARK, UI_NEUTRAL_WHITE, UI_NEUTRAL_BLACK,
    UI_GREY_LIGHTEST, UI_GREY_LIGHT, UI_GREY_MEDIUM, UI_GREY_DARK, UI_GREY_DARKER,
    UI_SUCCESS_GREEN, UI_ERROR_RED, UI_WARNING_ORANGE, UI_TEXT_ON_PRIMARY
)

@dataclass
class ReceiptData:
    receipt_no: str
    date: str
    name: str
    amount: float
    address: str
    pan: str
    org_pan: str = "AAATH7141M"
    purpose: str = "Education"

try:
    pdfmetrics.registerFont(TTFont('Poppins', FONT_PATH))
    pdfmetrics.registerFont(TTFont('Poppins-Bold', FONT_BOLD_PATH))
    FONT_REGULAR, FONT_BOLD = 'Poppins', 'Poppins-Bold'
    print("✅ Poppins font registered successfully.")
except Exception as e:
    print(f"⚠️ Poppins font not found. Using default Helvetica. Error: {e}")
    FONT_REGULAR, FONT_BOLD = 'Helvetica', 'Helvetica-Bold'

COLOR_PRIMARY_GREEN = UI_PRIMARY_COLOR
COLOR_ACCENT_CORAL = UI_ERROR_RED
COLOR_TEXT_DARK = UI_GREY_DARKER
COLOR_TEXT_GRAY = UI_GREY_DARK
COLOR_BG_LIGHT_GRAY = UI_GREY_LIGHTEST
COLOR_BG_DARKER_GRAY = "#B0B0B0"
COLOR_BORDER_LIGHT = UI_GREY_LIGHT
COLOR_WHITE = UI_NEUTRAL_WHITE

PAGE_WIDTH, PAGE_HEIGHT = landscape((108 * mm, 140 * mm))

def create_receipt_pdf(data: ReceiptData, session_output_dir: str):
    """
    Generates a PDF receipt from a ReceiptData object.
    PDFs are saved into a session-specific directory.

    Args:
        data (ReceiptData): An object containing all necessary info for the receipt.
        session_output_dir (str): The path to the current session's output directory.

    Returns:
        str: The final path to the generated PDF on success.
        None: On failure or if the PDF already exists.
    """
    os.makedirs(session_output_dir, exist_ok=True)
    final_pdf_path = os.path.join(session_output_dir, f"{data.receipt_no}.pdf")
    if os.path.exists(final_pdf_path):
        print(f"⚠️ PDF already exists for {data.receipt_no}. Skipping generation.")
        return final_pdf_path

    temp_dir = tempfile.gettempdir()
    temp_pdf_path = os.path.join(temp_dir, f"temp_{data.receipt_no}_{os.getpid()}.pdf")

    try:
        c = canvas.Canvas(temp_pdf_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

        # Set default values for empty fields
        name = data.name if data.name else "Donor"
        address = data.address if data.address else "Tamil Nadu"
        pan = data.pan if data.pan else "xxxxx1234x"

        # --- Section Boundaries & Margins ---
        X_MARGIN = 8 * mm
        CONTENT_WIDTH = PAGE_WIDTH - (2 * X_MARGIN)
        header_h = PAGE_HEIGHT * 0.20
        footer_h = PAGE_HEIGHT * 0.20
        header_top_y = PAGE_HEIGHT
        details_top_y = header_top_y - header_h
        footer_top_y = header_h

        # --- Draw Backgrounds ---
        c.setFillColor(COLOR_WHITE)
        c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
        c.setFillColor(COLOR_BG_DARKER_GRAY)
        c.rect(0, details_top_y, PAGE_WIDTH, header_h, fill=1, stroke=0)
        c.setFillColor(COLOR_BG_DARKER_GRAY)
        c.rect(0, 0, PAGE_WIDTH, footer_h, fill=1, stroke=0)

        # === HEADER ===
        header_content_width = PAGE_WIDTH - (2 * X_MARGIN)
        sec1_width = header_content_width * 0.20
        sec2_width = header_content_width * 0.60
        sec3_width = header_content_width * 0.20
        sec1_center_x = X_MARGIN + (sec1_width / 2)
        sec2_center_x = X_MARGIN + sec1_width + (sec2_width / 2)
        sec3_center_x = X_MARGIN + sec1_width + sec2_width + (sec3_width / 2)
        header_content_area_height = 20 * mm
        header_center_y = details_top_y + header_h - (header_content_area_height / 2) - (2*mm)

        logo_size = 16 * mm
        logo_x = sec1_center_x - (logo_size / 2)
        logo_y = header_center_y - (logo_size / 2)
        c.drawImage(LOGO_PATH, logo_x, logo_y, height=logo_size, width=logo_size, preserveAspectRatio=True, mask='auto')

        c.setFont(FONT_BOLD, 28)
        c.setFillColor(COLOR_TEXT_DARK)
        c.drawCentredString(sec2_center_x, header_center_y + 0.5*mm, "HOPE TRUST")
        c.setFont(FONT_REGULAR, 5)
        c.setFillColor(COLOR_TEXT_GRAY)
        c.drawCentredString(sec2_center_x, header_center_y - 4.5*mm, "RECOGNIZED BY GOVT. OF TAMIL NADU")
        c.setFont(FONT_BOLD, 6)
        c.setFillColor(COLOR_TEXT_DARK)
        c.drawCentredString(sec2_center_x, header_center_y - 7.5*mm, "REG. NO: 174/2017 | PH. NO: 7397271881")

        c.setFont(FONT_REGULAR, 8)
        c.setFillColor(COLOR_TEXT_GRAY)
        c.drawCentredString(sec3_center_x, header_center_y + 2*mm, "RECEIPT NO:")
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(COLOR_ACCENT_CORAL)
        c.drawCentredString(sec3_center_x, header_center_y - 3*mm, data.receipt_no.upper())

        y_cursor = details_top_y
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.setLineWidth(0.5)
        c.line(X_MARGIN, y_cursor, PAGE_WIDTH - X_MARGIN, y_cursor)

        # === MAIN CONTENT ===
        y_cursor -= 7 * mm
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(COLOR_PRIMARY_GREEN)
        c.drawCentredString(PAGE_WIDTH / 2, y_cursor, "DONATION RECEIPT")

        y_cursor -= 8 * mm
        message_style = ParagraphStyle(name='ThankYouMessage', fontName=FONT_BOLD, fontSize=12, textColor=COLOR_ACCENT_CORAL)
        thank_you_message = f"DEAR, <font size=12><b>{name.upper()}!</b></font>"
        p_message = Paragraph(thank_you_message, message_style)
        p_message.wrapOn(c, CONTENT_WIDTH, 20*mm)
        p_message.drawOn(c, X_MARGIN, y_cursor)

        y_cursor -= 6 * mm
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(X_MARGIN, y_cursor, "WE SINCERELY APPRECIATE YOUR CONTRIBUTION FOR OUR MISSION.")

        y_cursor -= 10 * mm
        col1_x = X_MARGIN
        col2_x = X_MARGIN + (CONTENT_WIDTH / 2)
        line_height = 6 * mm

        c.setFont(FONT_BOLD, 9)
        c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col2_x, y_cursor, "RECEIPT DETAILS")
        c.drawString(col1_x, y_cursor, "DONOR DETAILS")
        y_cursor -= line_height

        c.setFont(FONT_REGULAR, 9); c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(col2_x, y_cursor, "RECEIPT NO"); c.drawString(col1_x, y_cursor, "ADDRESS")
        c.setFont(FONT_BOLD, 9); c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col2_x + 25*mm, y_cursor, f":  {data.receipt_no.upper()}"); c.drawString(col1_x + 25*mm, y_cursor, f":  {address.upper()}")
        y_cursor -= line_height

        c.setFont(FONT_REGULAR, 9); c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(col2_x, y_cursor, "PAYMENT DATE"); c.drawString(col1_x, y_cursor, "PAN")
        c.setFont(FONT_BOLD, 9); c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col2_x + 25*mm, y_cursor, f":  {data.date.upper()}"); c.drawString(col1_x + 25*mm, y_cursor, f":  {pan.upper()}")
        y_cursor -= line_height

        c.setFont(FONT_REGULAR, 9); c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(col1_x, y_cursor, "PURPOSE")
        c.setFont(FONT_BOLD, 9); c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col1_x + 25*mm, y_cursor, f":  {data.purpose.upper()}")
        y_cursor -= line_height

        c.setFont(FONT_REGULAR, 9); c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(col1_x, y_cursor, "AMOUNT")
        c.setFont(FONT_BOLD, 9); c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col1_x + 25*mm, y_cursor, f": ₹ {str(data.amount).upper()}")
        y_cursor -= line_height

        c.setFont(FONT_REGULAR, 9); c.setFillColor(COLOR_TEXT_GRAY)
        c.drawString(col1_x, y_cursor, "IN WORDS")
        amount_words = f"{num2words(int(data.amount), lang='en_IN').title()} RUPEES ONLY."
        c.setFont(FONT_BOLD, 9); c.setFillColor(COLOR_TEXT_DARK)
        c.drawString(col1_x + 25*mm, y_cursor, f":  {amount_words.upper()}")

        y_cursor -= line_height
        c.line(X_MARGIN, y_cursor, PAGE_WIDTH - X_MARGIN, y_cursor)

        # === FOOTER ===
        sig_width, sig_height = 30*mm, footer_h - 4*mm
        qr_size = footer_h
        sig_x = X_MARGIN
        qr_x = PAGE_WIDTH - X_MARGIN - qr_size

        sig_y = (footer_h - sig_height) / 2 + 2*mm
        c.drawImage(SIGNATURE_PATH, sig_x, sig_y, width=sig_width, height=sig_height, preserveAspectRatio=True, mask='auto')
        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(COLOR_TEXT_GRAY)
        c.drawCentredString(sig_x + sig_width/2, sig_y - 0.5*mm, "AUTHORISED SIGNATORY")

        qr_y = (footer_h - qr_size) / 2 + 6*mm
        c.drawImage(QR_CODE_PATH, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True, mask='auto')
        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(COLOR_TEXT_GRAY)
        c.drawCentredString(qr_x + qr_size/2, qr_y - 3*mm, "SCAN ME")

        text_x = sig_x + sig_width + 4*mm
        text_width = qr_x - text_x - 4*mm

        # --- Updated Footer ---
        footer_lines = [
            "THIS IS A COMPUTER-GENERATED RECEIPT.",
            f"<font color='{COLOR_TEXT_DARK}'><b>ORG PAN: {data.org_pan.upper()}</b></font>",
            "ALL DONATIONS ARE ELIGIBLE FOR TAX EXEMPTION UNDER SECTION 80G."
        ]
        footer_text = "<br/>".join(footer_lines)
        footer_style = ParagraphStyle(
            'footer',
            fontName=FONT_REGULAR,
            fontSize=7,
            textColor=COLOR_TEXT_GRAY,
            alignment=TA_CENTER,
            leading=9
        )
        p = Paragraph(footer_text, footer_style)
        w, h = p.wrapOn(c, text_width, footer_h)
        p.drawOn(c, text_x, (footer_h - h)/2)

        c.save()
        shutil.move(temp_pdf_path, final_pdf_path)
        print(f"✅ Successfully generated and saved receipt: {final_pdf_path}")
        return final_pdf_path

    except Exception as e:
        print(f"❌ PDF Generation Failed for {data.receipt_no}: {e}")
        traceback.print_exc()
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return None

