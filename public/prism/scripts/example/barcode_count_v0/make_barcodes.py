#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2026
Martin Guthrie

Make a printable PDF sheet of QR codes, P###-S#####, for the count_0.scr example.

    python make_barcodes.py --product P001 --start 123 --count 24

"""
import os
import re
import argparse
import tempfile
import qrcode
from fpdf import FPDF

PRODUCT_RE = r"^P\d{3}$"   # matches count_0.scr TST000_Scan args regex
SERIAL_MAX = 99999          # five digits

# Letter page layout, mm
COLS = 3
ROWS = 4
QR_SIZE_MM = 45
CELL_W_MM = 65
CELL_H_MM = 62
MARGIN_X_MM = 10
MARGIN_Y_MM = 12
LABEL_FONT_PT = 12


def barcode_strings(product, start, count):
    """ :return: list of "P###-S#####" strings """
    return ["{}-S{:05d}".format(product, sn) for sn in range(start, start + count)]


def make_pdf(codes, out_file):
    """ Write the codes as a sheet of labelled QR codes """
    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(False)
    pdf.set_font("Arial", size=LABEL_FONT_PT)
    per_page = COLS * ROWS

    with tempfile.TemporaryDirectory() as tmp:
        for idx, code in enumerate(codes):
            if idx % per_page == 0:
                pdf.add_page()
            col = idx % COLS
            row = (idx % per_page) // COLS
            x = MARGIN_X_MM + col * CELL_W_MM
            y = MARGIN_Y_MM + row * CELL_H_MM

            img_file = os.path.join(tmp, "{}.png".format(idx))
            qrcode.make(code, border=2).save(img_file)
            pdf.image(img_file, x=x + (CELL_W_MM - QR_SIZE_MM) / 2, y=y, w=QR_SIZE_MM)
            pdf.set_xy(x, y + QR_SIZE_MM)
            pdf.cell(CELL_W_MM, LABEL_FONT_PT / 2, code, align="C")

        pdf.output(out_file)


def parse_args():
    parser = argparse.ArgumentParser(description="Make a PDF sheet of P###-S##### QR codes")
    parser.add_argument("--product", required=True, help="P###, P and three digits")
    parser.add_argument("--start", type=int, default=1, help="first serial number")
    parser.add_argument("--count", type=int, default=COLS * ROWS, help="number of codes")
    parser.add_argument("--out", default=None, help="PDF file, default barcodes_<P###>.pdf")
    return parser.parse_args()


def main():
    args = parse_args()
    if not re.match(PRODUCT_RE, args.product):
        print("product must be P and three digits: {}".format(args.product))
        return 1
    if args.count < 1 or args.start < 0 or args.start + args.count - 1 > SERIAL_MAX:
        print("serial numbers must be 0 to {}".format(SERIAL_MAX))
        return 1

    out_file = args.out or "barcodes_{}.pdf".format(args.product)
    make_pdf(barcode_strings(args.product, args.start, args.count), out_file)
    print("Wrote {} codes to {}".format(args.count, out_file))
    return 0


if __name__ == "__main__":
    exit(main())
