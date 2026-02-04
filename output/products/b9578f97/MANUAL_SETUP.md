# Manual Setup Instructions

Follow these steps to create the "Supplier Communication Mess Tracker" spreadsheet manually in Google Sheets.

## Step 1: Create a New Spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click the "+" button to create a new spreadsheet
3. Name it: **Supplier Communication Mess Tracker**

## Step 2: Create "Dashboard" Worksheet

1. Double-click "Sheet1" tab at the bottom
2. Rename it to: **Dashboard**

### Headers (Row 1)

Enter these headers in row 1:

| Cell | Value |
|------|-------|
| A1 | Item |
| B1 | Value |
| C1 | Target |
| D1 | Status |

### Sample Data

Enter this sample data (starting row 2):

**Row 2:** A2=Metric 1, B2=75, C2=100

**Row 3:** A3=Metric 2, B3=150, C3=100

### Formulas

Add these formulas:

| Cell | Formula |
|------|---------|
| D2 | `=IF(B2>=C2, "On Track", "Behind")` |
| D3 | `=IF(B3>=C3, "On Track", "Behind")` |

## Step 3: Create "Data Entry" Worksheet

1. Click the "+" at the bottom to add a new sheet
2. Double-click the tab and rename it to: **Data Entry**

### Headers (Row 1)

Enter these headers in row 1:

| Cell | Value |
|------|-------|
| A1 | Date |
| B1 | Category |
| C1 | Amount |
| D1 | Notes |

### Sample Data

Enter this sample data (starting row 2):

**Row 2:** A2=2024-01-01, B2=Type A, C2=100, D2=Sample entry

**Row 3:** A3=2024-01-02, B3=Type B, C3=200, D3=Another entry

## Step Final: Save and Share

1. Your spreadsheet auto-saves to Google Drive
2. To share: Click "Share" button in top right
3. Choose sharing settings appropriate for your use case

---

*Generated from sheet_definition.json*
