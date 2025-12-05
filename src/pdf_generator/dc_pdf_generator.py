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
    Exactly matches Excel template structure and layout
    """
    
    def __init__(self):
        # Page setup - Landscape A4 to match Excel print layout
        self.page_size = landscape(A4)
        self.page_width = self.page_size[0]
        self.page_height = self.page_size[1]
        
        # Margins - matching Excel print margins
        self.margin_left = 20
        self.margin_right = 20
        self.margin_top = 25
        self.margin_bottom = 25
        
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
        """Setup custom paragraph and text styles to match Excel"""
        # Title style - matches Excel title formatting
        self.styles.add(ParagraphStyle(
            name='DCTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        # Header style - matches Excel header font
        self.styles.add(ParagraphStyle(
            name='DCHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            leading=10
        ))
        
        # Data style - matches Excel data font
        self.styles.add(ParagraphStyle(
            name='DCData',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=colors.black,
            leading=10
        ))
        
        # Small text style for compact areas
        self.styles.add(ParagraphStyle(
            name='DCSmall',
            parent=self.styles['Normal'],
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.black,
            leading=8
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
            
            # Row 2: Empty spacer row
            story.append(Spacer(1, 8))
            
            # Rows 3-6: Header information (exactly matching Excel layout)
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
        """Create Row 1: Title and Logo (matching Excel A1:I1 layout)"""
        story = []
        
        # Create title table matching Excel merged cells structure
        title_data = []
        
        # Title spans A1:G1, Logo spans H1:I1
        title_para = Paragraph("Delivery Challan", self.styles['DCTitle'])
        
        # Logo cell
        logo_cell = ""
        if os.path.exists(self.logo_path):
            try:
                logo_img = Image(self.logo_path, width=60, height=20)
                logo_cell = logo_img
            except Exception as e:
                print(f"⚠️ Could not load logo: {e}")
                logo_cell = ""
        
        title_data.append([title_para, logo_cell])
        
        # Column widths matching Excel columns A-I
        col_widths = [
            self.content_width * 0.85,  # A1:G1 merged (title)
            self.content_width * 0.15   # H1:I1 merged (logo)
        ]
        
        title_table = Table(title_data, colWidths=col_widths)
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Remove borders for clean look
        ]))
        
        story.append(title_table)
        
        return story
    
    def _create_header_rows(self, dc_data):
        """Create Rows 3-6: Header information (matching Excel layout exactly)"""
        story = []
        
        # Get hub details
        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')
        hub_details = HUB_CONSTANTS.get(hub_key, {})
        
        # Use dynamic hub data if available, no hardcoded fallbacks
        place_of_supply = dc_data.get('place_of_supply', hub_details.get('place_of_supply', ''))
        hub_state = dc_data.get('hub_state', hub_details.get('state', ''))
        
        print(f"🏢 PDF Generator using dynamic data:")
        print(f"   Place of Supply: {place_of_supply}")
        print(f"   Hub State: {hub_state}")
        
        # Excel structure:
        # Row 3: A3="Serial no. of Challan:", C3=value, D3="Transport Mode:", I3="By Road"
        # Row 4: A4="Date of Challan:", C4=value, D4="Vehicle number:", (vehicle number in separate field)
        # Row 5: A5="Place of Supply:", C5=value
        # Row 6: A6="State:", C6=value
        
        header_data = [
            # Row 3
            [
                Paragraph("<b>Serial no. of Challan:</b>", self.styles['DCHeader']),
                "",  # B3
                Paragraph(str(dc_data.get('serial_number', '')), self.styles['DCData']),  # C3
                Paragraph("<b>Transport Mode:</b>", self.styles['DCHeader']),  # D3
                "", "", "", "",  # E3-H3
                Paragraph("By Road", self.styles['DCData'])  # I3
            ],
            # Row 4
            [
                Paragraph("<b>Date of Challan:</b>", self.styles['DCHeader']),  # A4
                "",  # B4
                Paragraph(dc_data.get('date', datetime.now()).strftime('%d-%b-%Y'), self.styles['DCData']),  # C4
                Paragraph("<b>Vehicle number:</b>", self.styles['DCHeader']),  # D4
                "", "", "", "",  # E4-H4
                Paragraph(str(dc_data.get('vehicle_number', '')), self.styles['DCData'])  # I4
            ],
            # Row 5
            [
                Paragraph("<b>Place of Supply:</b>", self.styles['DCHeader']),  # A5
                "",  # B5
                Paragraph(place_of_supply, self.styles['DCData']),  # C5 - Dynamic place of supply
                "", "", "", "", "", ""  # D5-I5
            ],
            # Row 6
            [
                Paragraph("<b>State:</b>", self.styles['DCHeader']),  # A6
                "",  # B6
                Paragraph(hub_state, self.styles['DCData']),  # C6 - Dynamic state
                "", "", "", "", "", ""  # D6-I6
            ]
        ]
        
        # Column widths matching Excel columns A-I - FIXED: Same improved distribution as header
        col_widths = [
            self.content_width * 0.12,  # A - Label column
            self.content_width * 0.08,  # B - Data column (reduced for better space distribution)
            self.content_width * 0.12,  # C - Data/Label column
            self.content_width * 0.08,  # D - Label column
            self.content_width * 0.10,  # E - Label column (reduced)
            self.content_width * 0.12,  # F - Data column (reduced)
            self.content_width * 0.12,  # G - Label column (reduced)
            self.content_width * 0.08,  # H - Data column (reduced)
            self.content_width * 0.18   # I - Extra space (consistent with header)
        ]
        
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Remove borders for clean look
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable text wrapping
            ('FONTSIZE', (8, 0), (8, -1), 8),      # Ensure column I has readable font size
        ]))
        
        story.append(header_table)
        
        return story
    
    def _create_party_details_rows(self, dc_data):
        """Create Rows 7-12: Party details (matching Excel layout exactly)"""
        story = []
        
        # Get hub details
        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')
        
        # CRITICAL FIX: Use FACILITY STATE for GSTIN lookup (FC location, not destination hub)
        # GSTIN is based on where the FC is located (seller), not where goods are going
        facility_state = dc_data.get('facility_state', '')
        facility_name = dc_data.get('facility_name', '')
        
        print(f"🔍 PDF: Starting GSTIN lookup for {hub_key}")
        print(f"   facility_state: {facility_state}")
        print(f"   facility_name: {facility_name}")
        
        # If facility_state not available, fallback to hub_state
        if not facility_state:
            facility_state = dc_data.get('hub_state', '')
            print(f"⚠️  PDF: Facility state not found, using hub state: {facility_state}")
        
        # Dynamic lookup with actual state for correct GSTIN
        if facility_state:
            try:
                dhc = get_dynamic_hub_constants()
                hub_details = dhc.get_hub_constants(hub_key, state=facility_state, fc_name=facility_name)
                print(f"✅ PDF: Using DYNAMIC hub constants for {hub_key} in {facility_state}")
                print(f"   Facility: {facility_name}")
                print(f"   GSTIN: {hub_details.get('sender_gstin', 'N/A')}")
            except Exception as e:
                print(f"❌ PDF: Error getting dynamic hub constants: {e}")
                print(f"   Falling back to static HUB_CONSTANTS")
                hub_details = HUB_CONSTANTS.get(hub_key, {})
        else:
            # Fallback to static if state not available
            hub_details = HUB_CONSTANTS.get(hub_key, {})
            print(f"⚠️  PDF: Using STATIC hub constants for {hub_key} (state not available)")
        
        # Get dynamic hub state information - no hardcoded fallbacks
        hub_state = dc_data.get('hub_state', hub_details.get('state', ''))
        hub_state_code = dc_data.get('hub_state_code', hub_details.get('state_code', ''))
        
        # CRITICAL FIX: Use dynamic facility address from dc_data instead of hardcoded mapping
        facility_name = dc_data.get('facility_name', 'Unknown')
        if dc_data.get('facility_address'):
            # Use facility-specific address from DC data
            sender_address = dc_data['facility_address']
            print(f"🏢 PDF Generator: Using facility-specific address for {facility_name}")
            print(f"   Address: {sender_address}")
        else:
            # Fallback to hardcoded mapping, then hub default
            facility_address_info = FACILITY_ADDRESS_MAPPING.get(facility_name)
            if facility_address_info:
                sender_address = facility_address_info['address']
                print(f"🏢 PDF Generator: Using mapped address for {facility_name}")
                print(f"   Address: {sender_address}")
            else:
                sender_address = hub_details.get('sender_address', '')
                print(f"⚠️ PDF Generator: Using fallback address (facility address not available)")
                print(f"   Available DC fields: {list(dc_data.keys())}")
                print(f"   facility_address: {dc_data.get('facility_address', 'MISSING')}")

        # Excel structure:
        # Row 7: A7:D7 merged="Details from Dispatch", E7:I7 merged="Details of Receiver"
        # Row 8: A8="Name:", B8:D8 merged=sender_name, E8="Name:", F8:I8 merged=receiver_name
        # Row 9: A9="Address:", B9:D9 merged=sender_address, E9="Address:", F9:I9 merged=receiver_address
        # Row 10: A10="GSTIN/UIN:", B10:D10 merged=sender_gstin, E10="GSTIN/UIN:", F10:I10 merged=receiver_gstin
        # Row 11: A11="FSSAI:", B11:D11 merged=blank, E11="FSSAI:", F11:I11 merged=blank
        # Row 12: A12="State:", B12=state, C12="State Code:", D12=state_code, E12="State:", F12=state, G12="State Code:", H12=state_code
        
        party_data = [
            # Row 7: Headers
            [
                Paragraph("<b>Details from Dispatch</b>", self.styles['DCHeader']),
                "", "", "",  # B7:D7 (part of merged A7:D7)
                Paragraph("<b>Details of Receiver</b>", self.styles['DCHeader']),
                "", "", "", ""  # F7:I7 (part of merged E7:I7)
            ],
            # Row 8: Names
            [
                Paragraph("<b>Name:</b>", self.styles['DCHeader']),  # A8
                Paragraph(dc_data.get('sender_name', ''), self.styles['DCData']),  # B8:D8
                "", "",  # C8, D8 (merged with B8)
                Paragraph("<b>Name:</b>", self.styles['DCHeader']),  # E8
                Paragraph(dc_data.get('receiver_name', ''), self.styles['DCData']),  # F8:I8
                "", "", ""  # G8, H8, I8 (merged with F8)
            ],
            # Row 9: Addresses - FIXED: Use dynamic facility address
            [
                Paragraph("<b>Address:</b>", self.styles['DCHeader']),  # A9
                Paragraph(sender_address, self.styles['DCSmall']),  # B9:D9 - Use dynamic facility address
                "", "",  # C9, D9 (merged with B9)
                Paragraph("<b>Address:</b>", self.styles['DCHeader']),  # E9
                Paragraph(dc_data.get('hub_address', ''), self.styles['DCSmall']),  # F9:I9
                "", "", ""  # G9, H9, I9 (merged with F9)
            ],
            # Row 10: GSTIN - CRITICAL: Uses dynamic GSTIN from facility_state
            [
                Paragraph("<b>GSTIN/UIN:</b>", self.styles['DCHeader']),  # A10
                Paragraph(hub_details.get('sender_gstin', ''), self.styles['DCData']),  # B10:D10 - Dynamic GSTIN
                "", "",  # C10, D10 (merged with B10)
                Paragraph("<b>GSTIN/UIN:</b>", self.styles['DCHeader']),  # E10
                Paragraph(hub_details.get('sender_gstin', ''), self.styles['DCData']),  # F10:I10 - Dynamic GSTIN
                "", "", ""  # G10, H10, I10 (merged with F10)
            ],
            # Row 11: FSSAI (blank as per requirement)
            [
                Paragraph("<b>FSSAI:</b>", self.styles['DCHeader']),  # A11
                Paragraph("", self.styles['DCData']),  # B11:D11
                "", "",  # C11, D11 (merged with B11)
                Paragraph("<b>FSSAI:</b>", self.styles['DCHeader']),  # E11
                Paragraph("", self.styles['DCData']),  # F11:I11
                "", "", ""  # G11, H11, I11 (merged with F11)
            ],
            # Row 12: State and State Code
            [
                Paragraph("<b>State:</b>", self.styles['DCHeader']),  # A12
                Paragraph(hub_state, self.styles['DCData']),  # B12 - Dynamic state
                Paragraph("<b>State Code:</b>", self.styles['DCHeader']),  # C12
                Paragraph(hub_state_code, self.styles['DCData']),  # D12 - Dynamic state code
                Paragraph("<b>State:</b>", self.styles['DCHeader']),  # E12
                Paragraph(hub_state, self.styles['DCData']),  # F12 - Dynamic state
                Paragraph("<b>State Code:</b>", self.styles['DCHeader']),  # G12
                Paragraph(hub_state_code, self.styles['DCData']),  # H12 - Dynamic state code
                ""  # I12
            ]
        ]
        
        # Column widths matching Excel columns A-I - adjusted for better text fitting
        col_widths = [
            self.content_width * 0.12,  # A - Label column
            self.content_width * 0.10,  # B - Data column (increased for better spacing)
            self.content_width * 0.15,  # C - Data/Label column
            self.content_width * 0.08,  # D - Label column
            self.content_width * 0.12,  # E - Empty/spacing
            self.content_width * 0.15,  # F - Empty/spacing
            self.content_width * 0.15,  # G - Empty/spacing
            self.content_width * 0.08,  # H - Empty/spacing
            self.content_width * 0.05   # I - Data column
        ]
        
        party_table = Table(party_data, colWidths=col_widths)
        
        # Style matching Excel formatting
        party_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Remove borders for clean look
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable text wrapping for better formatting
            # Row 7 header background
            ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),  # A7:D7
            ('BACKGROUND', (4, 0), (8, 0), colors.lightgrey),  # E7:I7
            # Merge cells styling (spans)
            ('SPAN', (0, 0), (3, 0)),  # A7:D7 merged
            ('SPAN', (4, 0), (8, 0)),  # E7:I7 merged
            ('SPAN', (1, 1), (3, 1)),  # B8:D8 merged (sender name)
            ('SPAN', (5, 1), (8, 1)),  # F8:I8 merged (receiver name)
            ('SPAN', (1, 2), (3, 2)),  # B9:D9 merged (sender address)
            ('SPAN', (5, 2), (8, 2)),  # F9:I9 merged (receiver address)
            ('SPAN', (1, 3), (3, 3)),  # B10:D10 merged (sender GSTIN)
            ('SPAN', (5, 3), (8, 3)),  # F10:I10 merged (receiver GSTIN)
            ('SPAN', (1, 4), (3, 4)),  # B11:D11 merged (sender FSSAI)
            ('SPAN', (5, 4), (8, 4)),  # F11:I11 merged (receiver FSSAI)
        ]))
        
        story.append(party_table)
        
        return story
    
    def _create_product_table(self, dc_data):
        """Create product table matching Excel structure exactly"""
        story = []
        
        # Product table headers (Row 13)
        headers = [
            "S. No.", "Product Description", "HSN code", "Qty", 
            "Taxable Value", "GST Rate", "CGST Amount", "SGST Amount", "Cess"
        ]
        
        # Create header row
        header_row = []
        for header in headers:
            header_row.append(Paragraph(f"<b>{header}</b>", self.styles['DCHeader']))
        
        # Product data rows (starting from Row 14)
        product_data = [header_row]
        
        # Calculate totals (matching Excel calculation logic exactly)
        total_qty = Decimal('0')
        total_taxable_value = Decimal('0')
        total_cgst = Decimal('0')
        total_sgst = Decimal('0')
        total_cess = Decimal('0')
        TWO_PLACES = Decimal('0.01')
        
        # Process each product (matching Excel populate_dc_data logic)
        for idx, product in enumerate(dc_data.get('products', []), 1):
            value = product.get('Value', 0)
            if isinstance(value, str):
                value = Decimal(value.replace(',', ''))
            else:
                value = Decimal(str(value))
                
            gst_rate = Decimal(str(product.get('GST Rate', 0)))
            
            # Calculate tax amounts (matching Excel formulas exactly)
            cgst_amount = (value * gst_rate * Decimal('0.5') / Decimal('100')).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            sgst_amount = cgst_amount
            
            # CESS calculation (matching Excel fix)
            cess_rate = product.get('Cess', 0)
            if isinstance(cess_rate, str):
                cess_rate = Decimal(cess_rate.replace(',', '').replace('%', ''))
            else:
                cess_rate = Decimal(str(cess_rate))
            cess_amount = (cess_rate * value / Decimal('100')).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            
            # Add to totals
            quantity = Decimal(str(product.get('Quantity', 0)))
            total_qty += quantity
            total_taxable_value += value
            total_cgst += cgst_amount
            total_sgst += sgst_amount
            total_cess += cess_amount
            
            # Create product row (matching Excel cell formatting)
            product_row = [
                Paragraph(str(idx), self.styles['DCData']),
                Paragraph(str(product.get('Description', '')), self.styles['DCData']),
                Paragraph(str(product.get('HSN', '')), self.styles['DCData']),
                Paragraph(f"{float(quantity):,.0f}", self.styles['DCData']),
                Paragraph(f"{float(value):,.2f}", self.styles['DCData']),  # Numbers only
                Paragraph(f"{float(gst_rate):.1f}%", self.styles['DCData']),
                Paragraph(f"{float(cgst_amount):,.2f}", self.styles['DCData']),  # Numbers only
                Paragraph(f"{float(sgst_amount):,.2f}", self.styles['DCData']),  # Numbers only
                Paragraph(f"{float(cess_amount):,.2f}", self.styles['DCData'])   # Numbers only
            ]
            
            product_data.append(product_row)
        
        # Add totals row (matching Excel totals row)
        totals_row = [
            Paragraph("<b>Total</b>", self.styles['DCHeader']),
            "",
            "",
            Paragraph(f"<b>{float(total_qty):,.0f}</b>", self.styles['DCHeader']),
            Paragraph(f"<b>{float(total_taxable_value):,.2f}</b>", self.styles['DCHeader']),  # Numbers only
            "",
            Paragraph(f"<b>{float(total_cgst):,.2f}</b>", self.styles['DCHeader']),  # Numbers only
            Paragraph(f"<b>{float(total_sgst):,.2f}</b>", self.styles['DCHeader']),  # Numbers only
            Paragraph(f"<b>{float(total_cess):,.2f}</b>", self.styles['DCHeader'])   # Numbers only
        ]
        product_data.append(totals_row)
        
        # Column widths matching Excel columns A-I
        col_widths = [
            self.content_width * 0.08,  # A: S.No
            self.content_width * 0.30,  # B: Description
            self.content_width * 0.10,  # C: HSN
            self.content_width * 0.08,  # D: Qty
            self.content_width * 0.12,  # E: Taxable Value
            self.content_width * 0.08,  # F: GST Rate
            self.content_width * 0.08,  # G: CGST
            self.content_width * 0.08,  # H: SGST
            self.content_width * 0.08   # I: CESS
        ]
        
        product_table = Table(product_data, colWidths=col_widths)
        
        # Style matching Excel formatting exactly
        table_style = [
            # Alignment matching Excel
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),   # S.No right (matching Excel)
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Description left
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # HSN left (matching Excel)
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # All numeric columns right
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Totals background
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            # Totals row special formatting
            ('SPAN', (0, -1), (2, -1)),  # Merge A:C for "Total" label (matching Excel)
        ]
        
        product_table.setStyle(TableStyle(table_style))
        
        story.append(product_table)
        
        # Store totals for footer
        dc_data['_pdf_totals'] = {
            'total_taxable_value': total_taxable_value,
            'total_cgst': total_cgst,
            'total_sgst': total_sgst,
            'total_cess': total_cess,
            'grand_total': total_taxable_value + total_cgst + total_sgst + total_cess
        }
        
        return story
    
    def _create_footer_section(self, dc_data):
        """Create footer section matching Excel footer layout exactly"""
        story = []
        
        # Get totals and calculate grand total (matching Excel logic)
        totals = dc_data.get('_pdf_totals', {})
        grand_total = totals.get('grand_total', Decimal('0'))
        
        # Convert amount to words (matching Excel logic)
        try:
            grand_total_float = float(grand_total)
            amount_in_words = num2words(grand_total_float, to='currency', lang='en_IN', currency='INR').title()
        except Exception as e:
            print(f"Warning: Could not convert amount to words: {e}")
            amount_in_words = "Amount conversion error"
        
        # Get hub details
        hub_key = dc_data.get('hub_type', 'SOURCINGBEE')
        hub_details = HUB_CONSTANTS.get(hub_key, {})
        
        # Footer section matching Excel structure:
        # footer_start_row: A="Total in Words: ... Only", I=grand_total
        # footer_start_row+1: A:I merged="Certified that..."
        # footer_start_row+2: A:D merged="Reasons...", E:I merged=company_name
        # footer_start_row+4: A:I merged="Terms & Conditions"
        # footer_start_row+7: A="Signature of Receiver", E:I merged="Authorised signatory"
        
        footer_data = [
            # Total in words row
            [
                Paragraph(f"<b>Total in Words: {amount_in_words} Only</b>", self.styles['DCHeader']),
                "", "", "", "", "", "", "",  # B-H
                Paragraph(f"<b>{float(grand_total):,.2f}</b>", self.styles['DCHeader'])  # I - Numbers only
            ],
            # Certification row
            [
                Paragraph("Certified that the particulars given above are true and correct", self.styles['DCSmall']),
                "", "", "", "", "", "", "", ""  # B-I (merged with A)
            ],
            # Reasons and company row
            [
                Paragraph("Reasons for transportation other than by way of supply: Intrastate Stock transfer between units of same entity", self.styles['DCSmall']),
                "", "", "",  # B-D (merged with A)
                Paragraph(f"<b>{hub_details.get('company_name', '')}</b>", self.styles['DCHeader']),
                "", "", "", ""  # F-I (merged with E)
            ],
            # Empty row
            ["", "", "", "", "", "", "", "", ""],
            # Terms & Conditions row
            [
                Paragraph("<b>Terms & Conditions</b>", self.styles['DCHeader']),
                "", "", "", "", "", "", "", ""  # B-I (merged with A)
            ],
            # Empty rows for spacing
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            # Signature row
            [
                Paragraph("Signature of Receiver", self.styles['DCData']),
                "", "", "",  # B-D
                Paragraph("<b>Authorised signatory</b>", self.styles['DCHeader']),
                "", "", "", ""  # F-I (merged with E)
            ]
        ]
        
        # Same column widths as other sections
        col_widths = [
            self.content_width * 0.15,  # A
            self.content_width * 0.05,  # B  
            self.content_width * 0.20,  # C
            self.content_width * 0.15,  # D
            self.content_width * 0.10,  # E
            self.content_width * 0.10,  # F
            self.content_width * 0.10,  # G
            self.content_width * 0.05,  # H
            self.content_width * 0.10   # I
        ]
        
        footer_table = Table(footer_data, colWidths=col_widths)
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (7, 0), 'LEFT'),     # Total in words left
            ('ALIGN', (8, 0), (8, 0), 'RIGHT'),    # Grand total right
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # All other rows left
            ('ALIGN', (4, 2), (8, 2), 'CENTER'),   # Company name center
            ('ALIGN', (4, 7), (8, 7), 'CENTER'),   # Authorised signatory center
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Remove borders for clean look
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            # Merge cells matching Excel structure
            ('SPAN', (0, 0), (7, 0)),  # A:H for total in words
            ('SPAN', (0, 1), (8, 1)),  # A:I for certification
            ('SPAN', (0, 2), (3, 2)),  # A:D for reasons
            ('SPAN', (4, 2), (8, 2)),  # E:I for company name
            ('SPAN', (0, 4), (8, 4)),  # A:I for terms & conditions
            ('SPAN', (4, 7), (8, 7)),  # E:I for authorised signatory
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