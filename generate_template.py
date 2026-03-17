import pandas as pd

# These headers MUST match your Flask 'upload_buses' logic exactly
sample_data = [{
    "Bus Number": "KA05AP1124",
    "GPS Device ID": "352592577999675",
    "SIM Number": "5754085684979",
    "RFID Reader ID": "352592577999675",
    "Seater Capacity": "30",
    "Chassis Number": "308565"
}]

# Create the DataFrame
df = pd.DataFrame(sample_data)

# Export to Excel (index=False prevents adding an extra row of numbers)
try:
    df.to_excel("Bus_Fleet_Template.xlsx", index=False, engine='openpyxl')
    print("✅ Template created successfully: Bus_Fleet_Template.xlsx")
except Exception as e:
    print(f"❌ Error creating template: {e}")