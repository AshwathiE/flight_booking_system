import io
from datetime import date, datetime, time

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def format_value(value) -> str:
    """
    Safely convert any database value to a string
    that ReportLab Paragraph can handle.
    """
    if value is None:
        return ""

    return str(value)


def format_date(value) -> str:
    """
    Format flight date as DD-MM-YYYY.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y")

    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")

    return str(value)


def format_time(value) -> str:
    """
    Format flight time as HH:MM.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%H:%M")

    if isinstance(value, time):
        return value.strftime("%H:%M")

    return str(value)


def format_datetime(value) -> str:
    """
    Format booking datetime as DD-MM-YYYY HH:MM.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %H:%M")

    return str(value)


def generate_ticket_pdf(booking, flight, user) -> bytes:

    buffer = io.BytesIO()

    # ---------------------------------------------------------
    # PAGE SETUP
    # ---------------------------------------------------------

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # ---------------------------------------------------------
    # CUSTOM STYLES
    # ---------------------------------------------------------

    title_style = ParagraphStyle(
        "TicketTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=15,
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#475569"),
    )

    value_style = ParagraphStyle(
        "ValueStyle",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#0f172a"),
    )

    # ---------------------------------------------------------
    # ELEMENTS
    # ---------------------------------------------------------

    elements = []

    # ---------------------------------------------------------
    # 1. HEADER
    # ---------------------------------------------------------

    brand_style = ParagraphStyle(
        "Brand",
        parent=title_style,
        alignment=2,
    )

    header_data = [
        [
            Paragraph(
                "BOARDING PASS / FLIGHT TICKET",
                title_style,
            ),
            Paragraph(
                "<b>AI Flight Booking</b>",
                brand_style,
            ),
        ]
    ]

    header_table = Table(
        header_data,
        colWidths=[270, 270],
    )

    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 2. PASSENGER & BOOKING INFORMATION
    # ---------------------------------------------------------

    pnr_style = ParagraphStyle(
        "PNR",
        parent=value_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0284c7"),
    )

    status_style = ParagraphStyle(
        "Status",
        parent=value_style,
        textColor=(
            colors.HexColor("#16a34a")
            if booking.status == "CONFIRMED"
            else colors.HexColor("#dc2626")
        ),
    )

    passenger_name = format_value(user.name)
    email = format_value(user.email)
    mobile_number = format_value(
        getattr(user, "mobile_number", None) or "N/A"
    )

    booking_reference = format_value(
        booking.booking_reference
    )

    booking_date = format_datetime(
        booking.created_at
    )

    booking_status = format_value(
        booking.status
    )

    info_data = [
        [
            Paragraph("Passenger Name:", label_style),
            Paragraph(passenger_name, value_style),

            Paragraph("Booking Ref / PNR:", label_style),
            Paragraph(booking_reference, pnr_style),
        ],
        [
            Paragraph("Email Address:", label_style),
            Paragraph(email, value_style),

            Paragraph("Booking Date:", label_style),
            Paragraph(booking_date, value_style),
        ],
        [
            Paragraph("Mobile Number:", label_style),
            Paragraph(mobile_number, value_style),

            Paragraph("Booking Status:", label_style),
            Paragraph(
                f"<b>{booking_status}</b>",
                status_style,
            ),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[110, 160, 110, 160],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#f1f5f9"),
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # ---------------------------------------------------------
    # 3. FLIGHT DETAILS
    # ---------------------------------------------------------

    elements.append(
        Paragraph(
            "FLIGHT DETAILS",
            header_style,
        )
    )

    # Safely format database values
    airline = format_value(flight.airline)
    flight_id = format_value(flight.flight_id)
    origin = format_value(flight.origin)
    destination = format_value(flight.destination)

    departure_date = format_date(
        flight.date
    )

    travel_class = format_value(
        flight.travel_class
    )

    departure_time = format_time(
        flight.departure_time
    )

    arrival_time = format_time(
        flight.arrival_time
    )

    number_of_seats = format_value(
        booking.number_of_seats
    )

    # Make sure price is safely converted
    try:
        total_price = float(booking.total_price or 0)
    except (TypeError, ValueError):
        total_price = 0.0

    price_style = ParagraphStyle(
        "Price",
        parent=value_style,
        fontName="Helvetica-Bold",
    )

    flight_data = [
        [
            Paragraph("Airline:", label_style),
            Paragraph(airline, value_style),

            Paragraph("Flight Number:", label_style),
            Paragraph(flight_id, value_style),
        ],
        [
            Paragraph("Origin:", label_style),
            Paragraph(origin, value_style),

            Paragraph("Destination:", label_style),
            Paragraph(destination, value_style),
        ],
        [
            Paragraph("Departure Date:", label_style),
            Paragraph(departure_date, value_style),

            Paragraph("Travel Class:", label_style),
            Paragraph(travel_class, value_style),
        ],
        [
            Paragraph("Departure Time:", label_style),
            Paragraph(departure_time, value_style),

            Paragraph("Arrival Time:", label_style),
            Paragraph(arrival_time, value_style),
        ],
        [
            Paragraph("Seats Booked:", label_style),
            Paragraph(
                f"{number_of_seats} Seat(s)",
                value_style,
            ),

            Paragraph("Total Fare Paid:", label_style),
            Paragraph(
                f"INR {total_price:,.2f}",
                price_style,
            ),
        ],
    ]

    flight_table = Table(
        flight_data,
        colWidths=[110, 160, 110, 160],
    )

    flight_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(flight_table)
    elements.append(Spacer(1, 25))

    # ---------------------------------------------------------
    # 4. IMPORTANT INFORMATION
    # ---------------------------------------------------------

    elements.append(
        Paragraph(
            "IMPORTANT INFORMATION",
            header_style,
        )
    )

    instructions_text = (
        "1. Please report at the airport check-in counter at least "
        "2 hours before departure for domestic flights.<br/>"
        "2. Carry a valid photo identification card "
        "(Aadhaar, Passport, Driving License, etc.) "
        "for entry to the airport.<br/>"
        "3. Gate closing time is 45 minutes prior to flight departure.<br/>"
        "4. For cancellations or modifications, please visit your "
        "user dashboard at least 2 hours before departure.<br/>"
        "5. Check baggage allowance details with the airline before departure."
    )

    instruction_style = ParagraphStyle(
        "Inst",
        parent=body_style,
        fontSize=9,
        leading=14,
    )

    elements.append(
        Paragraph(
            instructions_text,
            instruction_style,
        )
    )

    # ---------------------------------------------------------
    # BUILD PDF
    # ---------------------------------------------------------

    doc.build(elements)

    pdf_bytes = buffer.getvalue()

    buffer.close()

    return pdf_bytes