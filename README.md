# verizon_invoice_pdf
This pulls in the Verizon Invoice PDF. It rotates tables and then reads the data. Users must provide their own input PDF. The script processes potentially sensitive data, so users should avoid sharing output files. Just to be clear, I use this on the new Verizon invoices which have data tables which are rotated 90 degrees.

## Prerequisites
- Python 3.10+
- Install Ghostscript: https://www.ghostscript.com/download/gsdnld.html
- Install dependencies: `pip install -r requirements.txt`
