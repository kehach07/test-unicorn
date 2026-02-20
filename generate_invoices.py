import json
import csv
import random
from datetime import datetime, timedelta

TOTAL_RECORDS = 1000

products = [
    "Laptop", "Mouse", "Keyboard", "USB Cable", "Monitor",
    "Headphones", "Office Chair", "Desk Lamp", "Notebook",
    "Pen Set", "Shampoo", "Face Wash", "Soap", "Body Lotion",
    "Water Bottle", "Backpack", "Charger", "Power Bank",
    "Tablet", "Smartphone"
]

departments = [
    "Electronics",
    "Stationery",
    "Personal Care",
    "Accessories",
    "Home",
    "Office"
]

start_date = datetime(2026, 1, 1)

header = [
    "invoice_number", "invoice_date",
    "product1_name", "product1_price",
    "product2_name", "product2_price",
    "product3_name", "product3_price",
    "product4_name", "product4_price",
    "pos_number", "dept_location", "pincode"
]

# Open files
json_file = open("invoices_1000.json", "w")
csv_file = open("invoices_1000.csv", "w", newline="")
tab_file = open("invoices_1000.tab", "w", newline="")
ndjson_file = open("invoices_1000.ndjson", "w")

csv_writer = csv.writer(csv_file)
tab_writer = csv.writer(tab_file, delimiter="\t")

csv_writer.writerow(header)
tab_writer.writerow(header)

json_file.write("[\n")

for i in range(1, TOTAL_RECORDS + 1):
    invoice_number = f"INV-{100000 + i}"
    invoice_date = (start_date + timedelta(days=i % 365)).strftime("%Y-%m-%d")

    items = random.sample(products, 4)
    prices = [random.randint(100, 80000) for _ in range(4)]

    invoice = {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "invoice_items": [
            {"product_name": items[0], "price": prices[0]},
            {"product_name": items[1], "price": prices[1]},
            {"product_name": items[2], "price": prices[2]},
            {"product_name": items[3], "price": prices[3]}
        ],
        "pos_number": f"POS-{random.randint(1,20):02d}",
        "dept_location": random.choice(departments),
        "pincode": str(random.randint(460000, 469999))
    }

    # ---- JSON array ----
    json.dump(invoice, json_file)
    if i != TOTAL_RECORDS:
        json_file.write(",\n")
    else:
        json_file.write("\n")

    # ---- NDJSON ----
    ndjson_file.write(json.dumps(invoice) + "\n")

    # ---- CSV/TAB row ----
    row = [
        invoice["invoice_number"],
        invoice["invoice_date"],
        invoice["invoice_items"][0]["product_name"],
        invoice["invoice_items"][0]["price"],
        invoice["invoice_items"][1]["product_name"],
        invoice["invoice_items"][1]["price"],
        invoice["invoice_items"][2]["product_name"],
        invoice["invoice_items"][2]["price"],
        invoice["invoice_items"][3]["product_name"],
        invoice["invoice_items"][3]["price"],
        invoice["pos_number"],
        invoice["dept_location"],
        invoice["pincode"]
    ]

    csv_writer.writerow(row)
    tab_writer.writerow(row)

json_file.write("]")

# Close files
json_file.close()
csv_file.close()
tab_file.close()
ndjson_file.close()

print("Generated files:")
print("invoices_1000.json")
print("invoices_1000.csv")
print("invoices_1000.tab")
print("invoices_1000.ndjson")