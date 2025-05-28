# verizon_invoice_pdf
This pulls in the Verizon Invoice PDF. It rotates tables and then reads the data. Users must provide their own input PDF. The script processes potentially sensitive data, so users should avoid sharing output files. Just to be clear, I use this on the new Verizon invoices which have data tables which are rotated 90 degrees.

## KEEP IN MIND
I typically download the PDF from the Verizon portal. I then open it in Google and print/save only the first 25 pages because that is typically the end of the tables that show monthly summary charges for each wireless number. You would have to do the same. Again, my intent is to only get the summary charges per line. I recommend opening the PDF in a web browswer rather than some third party app like Revu/Bluebeam because the clarity of the PDF is better when saving from a web browswer.

## Prerequisites
- Python 3.10+
- Install Ghostscript: https://www.ghostscript.com/download/gsdnld.html
- Install dependencies: `pip install -r requirements.txt`
