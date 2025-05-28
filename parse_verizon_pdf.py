import argparse
import camelot
from PyPDF2 import PdfReader, PdfWriter
import warnings
import os
import pandas as pd  # Explicitly import pandas for clarity
import atexit

# Suppress the CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

###############################################
# DEFINING VARIABLES
###############################################
# Define file paths
parser = argparse.ArgumentParser(description="Parse Verizon invoice PDF")
parser.add_argument("--pdf", default="verizon_invoice.pdf", help="Path to input PDF")
parser.add_argument("--output-dir", default="output_csvs", help="Output directory for CSV files")
args = parser.parse_args()

pdf_path = args.pdf
output_dir = args.output_dir
rotated_pdf_path = os.path.join(os.path.dirname(pdf_path), "rotated_verizon_invoice.pdf")

###############################################
# CLEANING UP TEMP FILES
###############################################
# Check if input PDF exists
if not os.path.exists(pdf_path):
    print(f"Error: Input PDF '{pdf_path}' not found.")
    exit(1)

# Clean up temporary files on exit
def cleanup():
    if os.path.exists(rotated_pdf_path):
        os.remove(rotated_pdf_path)
        print(f"Cleaned up temporary file: {rotated_pdf_path}")

atexit.register(cleanup)

# Check if input PDF exists
if not os.path.exists(pdf_path):
    print(f"Error: Input PDF '{pdf_path}' not found.")
    exit(1)

###############################################
# ROTATING PDF PAGES
###############################################
# Function to rotate PDF pages
def rotate_pdf(input_path, output_path, rotation):
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(rotation)
            writer.add_page(page)
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    except FileNotFoundError as e:
            print(f"Error: Input PDF '{input_path}' not found: {e}")
            exit(1)
    except PermissionError as e:
        print(f"Error: Cannot write to output path '{output_path}': {e}")
        exit(1)
    except Exception as e:
        print(f"Error rotating PDF: {e}")
        exit(1)

###############################################
# STACKING/APPENDING TABLES
###############################################
# Function to stack tables with the same number of columns
def stack_tables(tables, table_indices):
    """
    Stack specified tables vertically if they have the same number of columns.
    
    Parameters:
    - tables: List of Camelot table objects
    - table_indices: List of table indices to stack (e.g., [1, 2, 3])
    
    Returns:
    - Combined DataFrame or None if stacking fails
    """
    if not table_indices or len(table_indices) < 1:
        print("No table indices provided for stacking.")
        return None
    
    # Validate indices
    valid_indices = [i for i in table_indices if i < len(tables)]
    if len(valid_indices) != len(table_indices):
        print(f"Warning: Some indices {set(table_indices) - set(valid_indices)} are invalid.")
        return None
    
    # Get the DataFrames for the specified tables
    dfs = [tables[i].df for i in valid_indices]
    
    # Check if all tables have the same number of columns
    num_columns = dfs[0].shape[1]
    if not all(df.shape[1] == num_columns for df in dfs):
        print("Error: Selected tables do not have the same number of columns.")
        print("Column counts:", [df.shape[1] for df in dfs])
        return None
    
    # Stack the DataFrames vertically
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Stacked tables {valid_indices} into a DataFrame with {combined_df.shape[0]} rows and {combined_df.shape[1]} columns.")
    
    return combined_df


# Create output_csvs directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Rotate the PDF by 90 degrees
rotate_pdf(pdf_path, rotated_pdf_path, rotation=90)

try:
    tables = camelot.read_pdf(rotated_pdf_path, flavor='stream', pages='all')
except Exception as e:
    print(f"Error reading PDF with Camelot: {e}")
    exit(1)

###############################################
# REFORMATTING MONETARY VALUES FOR SUMMATION
###############################################
# Function to clean and convert monetary string to float
def clean_monetary_value(value):
    cleaned = str(value).replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        print(f"Warning: Could not convert '{value}' to float, returning 0.0")
        return 0.0

###############################################
# PULLING RELEVANT VALUES FROM INVOICE
###############################################
# Extracting variables from tables
if tables:
    table_0 = tables[0].df
    if table_0.shape[0] > 2 and table_0.shape[1] > 2:
        acct_number_value = table_0.iloc[3, 2]
        account_number = acct_number_value.split('\n')[0]
        print(f"Account number is: {account_number}")
        due_date = acct_number_value.split('\n')[1]
        print(f"Due date is: {due_date}")
        invoice_number_value = table_0.iloc[5, 2]
        invoice_number = invoice_number_value.split('\n')[1]
        print(f"Invoice number is: {invoice_number}")
        billing_date_range = table_0.iloc[7, 2]
        print(f"Billing date range is: {billing_date_range}")
        balance_forward = clean_monetary_value(table_0.iloc[14, 2])
        print(f"Balance forward is: {balance_forward}")
        monthly_charges = clean_monetary_value(table_0.iloc[15, 2])
        print(f"Monthly charges are: {monthly_charges}")
        voice_charges = clean_monetary_value(table_0.iloc[17, 2])
        print(f"Voice charges are: {voice_charges}")
    else:
        print("Table 0 does not have enough rows or columns for the 3rd record, 3rd value")

if len(tables) > 1:
    table_1 = tables[1].df
    if table_1.shape[0] > 2 and table_1.shape[1] > 1:
        messaging_charges = clean_monetary_value(table_1.iloc[4, 1])
        print(f"Messaging charges are: {messaging_charges}")
        data_charges = clean_monetary_value(table_1.iloc[5, 1])
        print(f"Charge type from table 1: {data_charges}")
        international_charges = clean_monetary_value(table_1.iloc[6, 1])
        print(f"International charges are: {international_charges}")
        equipment_charges = clean_monetary_value(table_1.iloc[7, 1])
        print(f"Equipment charges are: {equipment_charges}")
        surcharges = clean_monetary_value(table_1.iloc[9, 1])
        print(f"Surcharges are: {surcharges}")
        taxes = clean_monetary_value(table_1.iloc[10, 1])
        print(f"Taxes are: {taxes}")
    else:
        print("Table 1 does not have enough rows or columns for the specified values")
else:
    print("Table 1 not found in extracted tables")

# Adding up total charges
total_charges = (balance_forward + monthly_charges + voice_charges + 
                 messaging_charges + data_charges + international_charges + 
                 equipment_charges + surcharges + taxes)
print(f"Total charges are: {total_charges}")

###############################################
# SPECIFYING TABLES TO APPEND VIA TABLE INDEX
###############################################
# Stack specific tables (example: stack tables 1 and 2)
# Replace [1, 2] with the indices of the tables you want to stack
stacked_table = stack_tables(
    tables,
    table_indices=list(range(5, len(tables))),  # Specify the table indices to stack
)

###############################################
# CLEANING UP STACKED TABLE
###############################################
"""
A lot of this is focused on dropping columns which do not
contain charges for wireless numbers. Additionally, I wanted 
to apply appropriate column names and order.
"""
if stacked_table is not None:
    # Remove duplicate rows (keeping the first occurrence)
    original_rows = stacked_table.shape[0]
    stacked_table = stacked_table.drop_duplicates()
    deduplicated_rows = stacked_table.shape[0]
    print(f"Removed {original_rows - deduplicated_rows} duplicate rows.")
    
    # Remove rows where the first column contains 'Roaming' or 'Data'
    pre_filter_rows = stacked_table.shape[0]
    if stacked_table.shape[1] > 0:  # Ensure there is at least one column
        stacked_table = stacked_table[~stacked_table.iloc[:, 0].isin(['Roaming', 'Data'])]
        post_filter_rows = stacked_table.shape[0]
        print(f"Removed {pre_filter_rows - post_filter_rows} rows where first column is 'Roaming' or 'Data'.")
    else:
        print("No columns in stacked table, cannot filter by first column.")
    
    # Remove rows where column 12 has values '', '--', NaN, or None
    pre_col12_filter_rows = stacked_table.shape[0]
    if stacked_table.shape[1] > 12:  # Ensure column 12 exists
        stacked_table = stacked_table[~stacked_table.iloc[:, 12].isin(['', '--']) & stacked_table.iloc[:, 12].notna()]
        post_col12_filter_rows = stacked_table.shape[0]
        print(f"Removed {pre_col12_filter_rows - post_col12_filter_rows} rows where column 12 is '', '--', NaN, or None.")
    else:
        print(f"Stacked table has only {stacked_table.shape[1]} columns, cannot filter by column 12.")

    # Remove rows where column 14 has values Nan
    pre_col14_filter_rows = stacked_table.shape[0]
    if stacked_table.shape[1] > 14:  # Ensure there is at least one column
        stacked_table = stacked_table[~stacked_table.iloc[:, 14].isin(['', '--'])]
        stacked_table = stacked_table[~stacked_table.iloc[:, 14].isin(['Total Current Charges'])]
        post_col14_filter_rows = stacked_table.shape[0]
        print(f"Removed {pre_col14_filter_rows - post_col14_filter_rows} rows where column 14 is NaN.")
    else:
        print(f"Stacked table has only {stacked_table.shape[1]} columns, cannot filter by column 14.")

    # Split column 14 into phone number (col 14) and name (new col 15)
    if stacked_table.shape[1] > 14:  # Ensure column 14 exists
        # Split on first space, maxsplit=1 for efficiency
        split_data = stacked_table.iloc[:, 14].str.split(' ', n=1, expand=True)
        # Ensure split produced expected columns
        if split_data.shape[1] == 2:
            stacked_table.iloc[:, 14] = split_data[0]  # Phone number in col 14
            stacked_table.insert(15, '15', split_data[1])  # Name in new col 15
            print("Split column 14 into phone number (col 14) and name (col 15).")
        else:
            print("Warning: Could not split column 14; unexpected format.")
    else:
        print(f"Stacked table has only {stacked_table.shape[1]} columns, cannot split column 14.") 

    # Rename columns and reverse their order
    if stacked_table.shape[1] >= 16:  # Ensure enough columns
        # Define new column names
        new_columns = {
            0: 'data_roaming',
            1: 'message_roaming',
            2: 'voice_roaming',
            3: 'data_usage',
            4: 'messaging_usage',
            5: 'voice_plan_usage',
            6: 'total_charges',
            7: 'third_party_charges',
            8: 'taxes',
            9: 'surcharges',
            10: 'equipment_charges',
            11: 'usage_charges',
            12: 'monthly_charges',
            13: 'page_number',
            14: 'wireless_number',
            15: 'user'
        }
        # Rename columns
        stacked_table.columns = [new_columns[i] for i in range(stacked_table.shape[1])]
        # Reverse column order
        reversed_columns = stacked_table.columns[::-1]
        stacked_table = stacked_table[reversed_columns]
        print("Renamed columns and reversed their order.")
    else:
        print(f"Stacked table has only {stacked_table.shape[1]} columns, cannot rename to 16 columns.")

    ###############################################
    # SAVING TABLE TO LOCAL MACHINE
    ###############################################        
    # Print and save the resulting table
    print("Stacked Table Contents:")
    print(stacked_table)
    try:
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"Cannot write to output directory: {output_dir}")
        output_csv_path = os.path.join(output_dir, "stacked_table.csv")
        stacked_table.to_csv(output_csv_path, index=False)
        print(f"Stacked table saved to {output_csv_path}")
    except PermissionError as e:
        print(f"Error: {e}. Please check directory permissions or specify a different output directory.")
        exit(1)
else:
    print("No stacked table was created, so no filtering applied.")
