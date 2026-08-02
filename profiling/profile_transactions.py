import pandas as pd


def profile_general(df):
    print("\nGENERAL")
    print("-" * 40)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumn Names:")

    for column in df.columns:
        print(f"- {column}")


def profile_uniqueness(df):
    print("\nUNIQUENESS")
    print("-" * 40)

    invoice_numbers = df["Invoice Number"].dropna()

    print(f"Unique Invoices: {invoice_numbers.nunique()}")

    print(
        f"Actual Duplicate Invoices: "
        f"{invoice_numbers.duplicated().sum()}"
    )

    print(
        f"Rows Without Invoice Number: "
        f"{df['Invoice Number'].isna().sum()}"
    )

    print(f"Unique Beats: {df['Item Name'].nunique()}")

def profile_nulls(df):
    print("\nNULL VALUES")
    print("-" * 40)

    null_counts = df.isna().sum()

    for column, count in null_counts.items():
        print(f"{column}: {count}")

def profile_invoice_structure(df):
    print("\nINVOICE STRUCTURE")
    print("-" * 40)

    # Hämta första riktiga invoice-numret
    first_invoice = df["Invoice Number"].dropna().iloc[0]

    # Hitta raden där invoicen börjar
    start_index = df[df["Invoice Number"] == first_invoice].index[0]

    # Samla ihop alla rader tills nästa invoice börjar
    rows = []

    current_index = start_index

    while current_index < len(df):
        row = df.iloc[current_index]

        if (
            current_index != start_index
            and pd.notna(row["Invoice Number"])
        ):
            break

        rows.append(row)
        current_index += 1

    invoice_df = pd.DataFrame(rows)

    columns_to_display = [
        "Invoice Number",
        "Date",
        "Status",
        "Store Type",
        "Item Name",
        "List Price",
        "Discount",
        "Sale Price",
        "Split Payment Id",
        "Split Payment Type",
        "Processing Fee",
        "Split Payment Amount",
    ]

    print(
        invoice_df[columns_to_display].to_string(
            index=False
        )
    )

def profile_invoice_statistics(df):
    profile_df = df.copy()

    profile_df["Invoice Number"] = (
        profile_df["Invoice Number"]
        .ffill()
    )

    invoice_sizes = (
    profile_df
    .groupby("Invoice Number")
    .size()
)

    print(invoice_sizes.head(10))
    print("\nDistribution:")
    print(invoice_sizes.value_counts().sort_index())

def profile_distributions(df):
    print("\nDISTRIBUTIONS")
    print("-" * 40)

    columns = [
        "Status",
        "Store Type",
        "Split Payment Type",
    ]

    for column in columns:
        print(f"\n{column}:")
        print(
            df[column]
            .fillna("<NULL>")
            .value_counts(dropna=False)
            .to_string()
        )

def profile_item_structure(df):
    print("\nITEM STRUCTURE")
    print("-" * 40)

    profile_df = df.copy()

    profile_df["Invoice Number"] = (
        profile_df["Invoice Number"]
        .ffill()
    )

    profile_df["is_item_start"] = (
        profile_df["Item Name"]
        .notna()
    )

    item_start_rows = profile_df[
        profile_df["is_item_start"]
    ]

    print(
        f"Rows with Item Name: "
        f"{len(item_start_rows)}"
    )

    print(
        f"Unique invoices with items: "
        f"{item_start_rows['Invoice Number'].nunique()}"
    )

    print("\nItem starts per invoice:")

    item_counts = (
        item_start_rows
        .groupby("Invoice Number")
        .size()
    )

    print(
        item_counts
        .value_counts()
        .sort_index()
        .to_string()
    )

def main():
    df = pd.read_csv(
    "data/transactions/transactions.csv",
    skiprows=2,
)

    print("=" * 50)
    print("MAAM TRANSACTION PROFILE")
    print("=" * 50)

    profile_general(df)
    profile_uniqueness(df)
    profile_nulls(df)
    profile_invoice_structure(df)
    profile_invoice_statistics(df)
    profile_distributions(df)
    profile_item_structure(df)

if __name__ == "__main__":
    main()