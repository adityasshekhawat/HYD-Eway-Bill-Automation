#!/usr/bin/env python3
"""
DC PDF Generator - Creates print-ready PDF versions of DC templates
Exactly matches Excel template layout with landscape orientation and scale-to-fit
"""

import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import decimal
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import re

try:
    from num2words import num2words
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'num2words'])
    from num2words import num2words

# ✅ CITY-AGNOSTIC: Import dynamic configuration from dc_template_generator
# This replaces hardcoded Bangalore-specific values
try:
    # Try relative import first (when imported as module)
    from ..core.dc_template_generator import HUB_CONSTANTS, FACILITY_ADDRESS_MAPPING
    from ..core.dynamic_hub_constants import get_dynamic_hub_constants
except (ImportError, ValueError):
    try:
        # Try absolute import from src (Streamlit context)
        from src.core.dc_template_generator import HUB_CONSTANTS, FACILITY_ADDRESS_MAPPING
        from src.core.dynamic_hub_constants import get_dynamic_hub_constants
    except ImportError:
        # Fallback for standalone execution
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.dc_template_generator import HUB_CONSTANTS, FACILITY_ADDRESS_MAPPING
        from core.dynamic_hub_constants import get_dynamic_hub_constants

def get_hub_pincode_from_address(hub_address):
    """Extract pincode from hub address"""
    if not hub_address:
        return '000000'  # ✅ CITY-AGNOSTIC: Changed from hardcoded 562123
    
    pincode_match = re.search(r'(\d{6})', hub_address)
    return pincode_match.group(1) if pincode_match else '000000'  # ✅ CITY-AGNOSTIC: Changed from hardcoded 562123

class DCPDFGenerator:
    """
    Generates print-ready PDF versions of DC templates
    Portrait A4, flat tables, consistent borders, compact font.
    """

    def __init__(self):
        # Page setup - Portrait A4 (more rows per page than landscape)
        self.page_size = A4
        self.page_width = self.page_size[0]
        self.page_height = self.page_size[1]

        # Margins - tight for maximum content area
        self.margin_left = 10
        self.margin_right = 10
        self.margin_top = 10
        self.margin_bottom = 10

        # Available content area
        self.content_width = self.page_width - self.margin_left - self.margin_right
        self.content_height = self.page_height - self.margin_top - self.margin_bottom

        # Style definitions
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Logo path - FIXED: Use relative path from project root
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "image.png")
        print(f"🖼️ PDF Generator: Looking for logo at: {self.logo_path}")
        if os.path.exists(self.logo_path):
            print(f"✅ Logo found successfully")
        else:
            print(f"⚠️ Logo not found at path")
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles - portrait compact layout"""
        self.styles.add(ParagraphStyle(
            name='DCTitle',
            parent=self.styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold',
            textColor=colors.black, leading=11,
        ))
        self.styles.add(ParagraphStyle(
            name='DCHeader',
            parent=self.styles['Normal'],
            fontSize=5, fontName='Helvetica-Bold',
            textColor=colors.black, leading=6.5,
        ))
        self.styles.add(ParagraphStyle(
            name='DCData',
            parent=self.styles['Normal'],
            fontSize=5, fontName='Helvetica',
            textColor=colors.black, leading=6.5,
        ))
        self.styles.add(ParagraphStyle(
            name='DCSmall',
            parent=self.styles['Normal'],
            fontSize=4.5, fontName='Helvetica',
            textColor=colors.black, leading=5.5,
        ))
        self.styles.add(ParagraphStyle(
            name='DCProductRow',
            parent=self.styles['Normal'],
            fontSize=5, fontName='Helvetica',
            textColor=colors.black, leading=6.5,
        ))
        self.styles.add(ParagraphStyle(
            name='DCProductHeader',
            parent=self.styles['Normal'],
            fontSize=5, fontName='Helvetica-Bold',
            textColor=colors.black, leading=6.5,
        ))
    
    def create_dc_pdf(self, dc_data, output_path):
        """
        Create a PDF version of the DC template matching Excel structure exactly
        """
        try:
            # Create document with landscape orientation
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                leftMargin=self.margin_left,
                rightMargin=self.margin_right,
                topMargin=self.margin_top,
                bottomMargin=self.margin_bottom,
                title=f"DC_{dc_data.get('serial_number', '')}"
            )
            
            # Build content following Excel structure exactly
            story = []
            
            # Row 1: Title and Logo (A1:G1 merged for title, H1:I1 for logo)
            story.extend(self._create_title_row(dc_data))
            
            # Rows 3-6: Header information
            story.extend(self._create_header_rows(dc_data))
            
            # Rows 7-12: Party details (exactly matching Excel layout)
            story.extend(self._create_party_details_rows(dc_data))
            
            # Row 13: Product table header
            # Rows 14+: Product data and totals
            story.extend(self._create_product_table(dc_data))
            
            # Footer section (matching Excel footer layout)
            story.extend(self._create_footer_section(dc_data))
            
            # Build PDF
            doc.build(story)
            
            print(f"✅ Created PDF DC: {dc_data.get('serial_number', '')} at {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating PDF DC: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_title_row(self, dc_data):
        """Create title row with optional logo."""
        story = []
        cw = self.content_width

        logo_cell = ""
        if os.path.exists(self.logo_path):
            try:
                logo_cell = Image(self.logo_path, width=50, height=16)
            except Exception as e:
                print(f"⚠️ Could not load logo: {e}")

        title_table = Table(
            [[Paragraph("<b>Delivery Challan</b>", self.styles['DCTitle']), logo_cell]],
            colWidths=[cw * 0.80, cw * 0.20],
        )
        title_table.setStyle(TableStyle([
            ('ALIGN',           (0, 0), (0, 0), 'LEFT'),
            ('ALIGN',           (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN',          (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',             (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING',      (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',   (0, 0), (-1, -1), 3),
        ]))
        story.append(title_table)
        return story
    
    def _create_header_rows(self, dc_data):
        """Header info: flat 4-column table (label_L | value_L | label_R | value_R)."""
        story = []
        cw = self.content_width

        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')
        hub_details = HUB_CONSTANTS.get(hub_key, {})
        place_of_supply = dc_data.get('place_of_supply', hub_details.get('place_of_supply', ''))
        hub_state = dc_data.get('hub_state', hub_details.get('state', ''))

        print(f"🏢 PDF Generator using dynamic data:")
        print(f"   Place of Supply: {place_of_supply}")
        print(f"   Hub State: {hub_state}")

        lbl = lambda t: Paragraph(f"<b>{t}</b>", self.styles['DCHeader'])
        dat = lambda t: Paragraph(str(t), self.styles['DCData'])

        date_str = dc_data.get('date', datetime.now())
        if hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%d-%b-%Y')

        col_widths = [cw * 0.15, cw * 0.35, cw * 0.18, cw * 0.32]
        header_table = Table([
            [lbl("Serial no. of Challan:"), dat(dc_data.get('serial_number', '')),
             lbl("Transport Mode:"),         dat("By Road")],
            [lbl("Date of Challan:"),        dat(date_str),
             lbl("Vehicle number:"),         dat(dc_data.get('vehicle_number', ''))],
            [lbl("Place of Supply:"),        dat(place_of_supply),   dat(""), dat("")],
            [lbl("State:"),                  dat(hub_state),         dat(""), dat("")],
        ], colWidths=col_widths, rowHeights=[10] * 4)

        header_table.setStyle(TableStyle([
            ('ALIGN',           (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN',          (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',             (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID',       (0, 0), (-1, -1), 0.3, colors.black),
            ('TOPPADDING',      (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING',   (0, 0), (-1, -1), 1),
            # Merge blank right cells in rows 2-3 (no stray divider)
            ('SPAN', (2, 2), (3, 2)),
            ('SPAN', (2, 3), (3, 3)),
        ]))

        story.append(header_table)
        return story
    
    def _create_party_details_rows(self, dc_data):
        """Party section: flat 4-column table (label_L | value_L | label_R | value_R)."""
        story = []
        cw = self.content_width

        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')

        # CRITICAL FIX: Use FACILITY STATE for GSTIN lookup
        facility_state = dc_data.get('facility_state', '')
        facility_name = dc_data.get('facility_name', '')

        print(f"🔍 PDF: Starting GSTIN lookup for {hub_key}")
        print(f"   facility_state: {facility_state}")
        print(f"   facility_name: {facility_name}")

        if not facility_state:
            facility_state = dc_data.get('hub_state', '')
            print(f"⚠️  PDF: Facility state not found, using hub state: {facility_state}")

        if facility_state:
            try:
                dhc = get_dynamic_hub_constants()
                hub_details = dhc.get_hub_constants(hub_key, state=facility_state, fc_name=facility_name)
                print(f"✅ PDF: Using DYNAMIC hub constants for {hub_key} in {facility_state}")
                print(f"   GSTIN: {hub_details.get('sender_gstin', 'N/A')}")
            except Exception as e:
                print(f"❌ PDF: Error getting dynamic hub constants: {e}")
                hub_details = HUB_CONSTANTS.get(hub_key, {})
        else:
            hub_details = HUB_CONSTANTS.get(hub_key, {})
            print(f"⚠️  PDF: Using STATIC hub constants for {hub_key} (state not available)")

        hub_state = dc_data.get('hub_state', hub_details.get('state', ''))
        hub_state_code = dc_data.get('hub_state_code', hub_details.get('state_code', ''))

        # CRITICAL FIX: Use dynamic facility address
        facility_name = dc_data.get('facility_name', 'Unknown')
        if dc_data.get('facility_address'):
            sender_address = dc_data['facility_address']
            print(f"🏢 PDF Generator: Using facility-specific address for {facility_name}")
        else:
            facility_address_info = FACILITY_ADDRESS_MAPPING.get(facility_name)
            if facility_address_info:
                sender_address = facility_address_info['address']
                print(f"🏢 PDF Generator: Using mapped address for {facility_name}")
            else:
                sender_address = hub_details.get('sender_address', '')
                print(f"⚠️ PDF Generator: Using fallback address")

        lbl = lambda t: Paragraph(f"<b>{t}</b>", self.styles['DCHeader'])
        dat = lambda t: Paragraph(str(t), self.styles['DCData'])
        adr = lambda t: Paragraph(str(t), self.styles['DCSmall'])

        state_val = f"{hub_state}  Code: {hub_state_code}"

        # 4 columns: lbl_L | val_L | lbl_R | val_R
        col_widths = [cw * 0.11, cw * 0.39, cw * 0.11, cw * 0.39]
        party_table = Table([
            [lbl("Details from Dispatch"), "",
             lbl("Details of Receiver"),   ""],
            [lbl("Name:"),      dat(dc_data.get('sender_name', '')),
             lbl("Name:"),      dat(dc_data.get('receiver_name', ''))],
            [lbl("Address:"),   adr(sender_address),
             lbl("Address:"),   adr(dc_data.get('hub_address', ''))],
            [lbl("GSTIN/UIN:"), dat(hub_details.get('sender_gstin', '')),
             lbl("GSTIN/UIN:"), dat(hub_details.get('sender_gstin', ''))],
            [lbl("State:"),     dat(state_val),
             lbl("State:"),     dat(state_val)],
        ], colWidths=col_widths)

        party_table.setStyle(TableStyle([
            ('ALIGN',           (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN',          (0, 0), (-1, -1), 'TOP'),
            ('BOX',             (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID',       (0, 0), (-1, -1), 0.3, colors.black),
            ('TOPPADDING',      (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING',   (0, 0), (-1, -1), 1),
            # Section title spans and styling
            ('SPAN',            (0, 0), (1, 0)),
            ('SPAN',            (2, 0), (3, 0)),
            ('BACKGROUND',      (0, 0), (1, 0), colors.HexColor('#DEDEDE')),
            ('BACKGROUND',      (2, 0), (3, 0), colors.HexColor('#DEDEDE')),
            ('VALIGN',          (0, 0), (3, 0), 'MIDDLE'),
            ('TOPPADDING',      (0, 0), (3, 0), 2),
            ('BOTTOMPADDING',   (0, 0), (3, 0), 2),
        ]))

        story.append(party_table)
        return story
    
    def _create_product_table(self, dc_data):
        """Product table: portrait column widths, auto row heights, consistent grid."""
        story = []
        cw = self.content_width

        prh = lambda t: Paragraph(f"<b>{t}</b>", self.styles['DCProductHeader'])
        prd = lambda t: Paragraph(str(t),         self.styles['DCProductRow'])

        heads = ["S.\nNo.", "Product Description", "HSN\nCode", "Qty",
                 "Taxable\nValue", "GST\nRate", "CGST\nAmt", "SGST\nAmt", "Cess"]
        product_data = [[prh(h) for h in heads]]

        total_qty = Decimal('0')
        total_taxable_value = Decimal('0')
        total_cgst = Decimal('0')
        total_sgst = Decimal('0')
        total_cess = Decimal('0')
        TWO_PLACES = Decimal('0.01')

        for idx, product in enumerate(dc_data.get('products', []), 1):
            value = product.get('Value', 0)
            if isinstance(value, str):
                value = Decimal(value.replace(',', ''))
            else:
                value = Decimal(str(value))

            gst_rate = Decimal(str(product.get('GST Rate', 0)))
            cgst_amount = (value * gst_rate * Decimal('0.5') / Decimal('100')).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            sgst_amount = cgst_amount

            cess_rate = product.get('Cess', 0)
            if isinstance(cess_rate, str):
                cess_rate = Decimal(cess_rate.replace(',', '').replace('%', ''))
            else:
                cess_rate = Decimal(str(cess_rate))
            cess_amount = (cess_rate * value / Decimal('100')).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            quantity = Decimal(str(product.get('Quantity', 0)))
            total_qty          += quantity
            total_taxable_value += value
            total_cgst          += cgst_amount
            total_sgst          += sgst_amount
            total_cess          += cess_amount

            product_data.append([
                prd(str(idx)),
                prd(str(product.get('Description', ''))),
                prd(str(product.get('HSN', ''))),
                prd(f"{float(quantity):,.0f}"),
                prd(f"{float(value):,.2f}"),
                prd(f"{float(gst_rate):.1f}%"),
                prd(f"{float(cgst_amount):,.2f}"),
                prd(f"{float(sgst_amount):,.2f}"),
                prd(f"{float(cess_amount):,.2f}"),
            ])

        product_data.append([
            prh("Total"), "", "",
            prh(f"{float(total_qty):,.0f}"),
            prh(f"{float(total_taxable_value):,.2f}"),
            "",
            prh(f"{float(total_cgst):,.2f}"),
            prh(f"{float(total_sgst):,.2f}"),
            prh(f"{float(total_cess):,.2f}"),
        ])

        # Portrait column widths — sum = 1.00
        col_widths = [cw * x for x in [0.04, 0.36, 0.09, 0.06, 0.12, 0.06, 0.09, 0.09, 0.09]]

        product_table = Table(product_data, colWidths=col_widths)  # no fixed rowHeights → auto
        product_table.setStyle(TableStyle([
            ('ALIGN',           (0, 0), (0, -1),  'CENTER'),
            ('ALIGN',           (1, 0), (2, -1),  'LEFT'),
            ('ALIGN',           (3, 0), (-1, -1), 'RIGHT'),
            ('VALIGN',          (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',             (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID',       (0, 0), (-1, -1), 0.3, colors.black),
            ('BACKGROUND',      (0, 0), (-1, 0),  colors.HexColor('#DEDEDE')),
            ('BACKGROUND',      (0, -1),(-1, -1), colors.HexColor('#DEDEDE')),
            ('TOPPADDING',      (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING',   (0, 0), (-1, -1), 1),
            ('SPAN',            (0, -1),(2, -1)),
        ]))

        story.append(product_table)

        dc_data['_pdf_totals'] = {
            'total_taxable_value': total_taxable_value,
            'total_cgst':          total_cgst,
            'total_sgst':          total_sgst,
            'total_cess':          total_cess,
            'grand_total':         total_taxable_value + total_cgst + total_sgst + total_cess,
        }
        return story
    
    def _create_footer_section(self, dc_data):
        """Footer: total-in-words, certification, reasons, terms, signatures."""
        story = []
        cw = self.content_width

        totals = dc_data.get('_pdf_totals', {})
        grand_total = totals.get('grand_total', Decimal('0'))

        try:
            amount_in_words = num2words(float(grand_total), to='currency', lang='en_IN', currency='INR').title()
        except Exception as e:
            print(f"Warning: Could not convert amount to words: {e}")
            amount_in_words = "Amount conversion error"

        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')
        hub_details = HUB_CONSTANTS.get(hub_key, {})

        lbl = lambda t: Paragraph(f"<b>{t}</b>", self.styles['DCHeader'])
        sml = lambda t: Paragraph(str(t),         self.styles['DCSmall'])
        dat = lambda t: Paragraph(str(t),         self.styles['DCData'])

        col_widths = [cw * x for x in [0.15, 0.05, 0.15, 0.15, 0.10, 0.10, 0.10, 0.05, 0.15]]
        footer_table = Table([
            [lbl(f"Total in Words: {amount_in_words} Only"),
             "", "", "", "", "", "", "",
             lbl(f"{float(grand_total):,.2f}")],
            [sml("Certified that the particulars given above are true and correct"),
             "", "", "", "", "", "", "", ""],
            [sml("Reasons for transportation: Intrastate Stock transfer between units of same entity"),
             "", "", "",
             lbl(hub_details.get('company_name', '')), "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            [lbl("Terms & Conditions"), "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            [dat("Signature of Receiver"), "", "", "",
             lbl("Authorised signatory"),  "", "", "", ""],
        ], colWidths=col_widths)

        footer_table.setStyle(TableStyle([
            ('ALIGN',           (0, 0), (7, 0), 'LEFT'),
            ('ALIGN',           (8, 0), (8, 0), 'RIGHT'),
            ('ALIGN',           (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN',           (4, 2), (8, 2), 'CENTER'),
            ('ALIGN',           (4, 6), (8, 6), 'CENTER'),
            ('VALIGN',          (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',      (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING',   (0, 0), (-1, -1), 1),
            ('SPAN', (0, 0), (7, 0)),
            ('SPAN', (0, 1), (8, 1)),
            ('SPAN', (0, 2), (3, 2)),
            ('SPAN', (4, 2), (8, 2)),
            ('SPAN', (0, 4), (8, 4)),
            ('SPAN', (4, 6), (8, 6)),
        ]))

        story.append(footer_table)
        return story


def create_dc_pdf_from_excel_data(dc_data, output_path):
    """
    Convenience function to create PDF from the same data used for Excel generation
    
    Args:
        dc_data: DC data dictionary (same format as Excel generator)
        output_path: Path where PDF should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    generator = DCPDFGenerator()
    return generator.create_dc_pdf(dc_data, output_path) 