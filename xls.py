import pandas as pd
import random
import os



# Number of rows
num_rows = 50

# Some sample names to pick from
sample_names = [
    "Aravind.S(HT)", "Sathish Kumar.S", "Priya R", "Rahul K", "Anitha M",
    "Vijay P", "Lakshmi T", "Karthik S", "Divya N", "Ramesh B"
]

data = []

for i in range(1, num_rows + 1):
    # 5% completely empty row
    if random.random() < 0.05:
        data.append([i, '', '', '', '', ''])
        continue

    # Donor name: 10% empty
    donor = random.choice(sample_names) if random.random() > 0.1 else ''

    # Receiver name: pick random
    receiver = random.choice(sample_names)

    # Amount: 10% zero
    amount = round(random.uniform(100, 5000), 2) if random.random() > 0.1 else 0

    # Date: 10% invalid format
    if random.random() > 0.1:
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(17, 25)
        date = f"{day:02d}.{month:02d}.{year:02d}"  # DD.MM.YY
    else:
        date = f"{random.randint(2000,2025)}/{random.randint(1,12)}/{random.randint(1,28)}"  # Invalid

    # Receipt number: 90% empty
    if random.random() < 0.9:  
        receipt = ''  
    else:
        # 10% chance to have a value (with possible duplicates)
        receipt = f"HT{1000 + random.randint(1,50)}"

    data.append([i, donor, receiver, amount, date, receipt])

# Create DataFrame
df = pd.DataFrame(data, columns=["S.NO", "DONOR NAME", "RECEIVER NAME", "AMOUNT", "D.O.D", "RECEIPT NUMBER"])

# Save to Excel

output_file = os.path.join(os.getcwd(), "dummy_donors_edge.xlsx")
df.to_excel(output_file, index=False)
print(f"Dummy Excel file generated at: {output_file}")

# df.to_excel("dummy_donors_edge.xlsx", index=False)

print("Dummy Excel file 'dummy_donors_edge.xlsx' generated with 50 rows.")
