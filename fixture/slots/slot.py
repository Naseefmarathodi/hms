import json
from datetime import datetime, timedelta

# List to store the slots data
slots_data = []

# Starting time: 00:00
start_time = datetime.strptime("00:00", "%H:%M")

# Generate 96 slots (for 24 hours with 15-minute intervals)
for i in range(96):
    end_time = start_time + timedelta(minutes=15)
    
    # Format the times as required
    start_time_str = start_time.strftime("%H:%M")
    end_time_str = end_time.strftime("%H:%M")
    
    # Create the dictionary to store in the JSON format
    slot = {
        "model": "adminpanel.doctorslot",
        "pk": i + 1,
        "fields": {
            "start_time": start_time_str,
            "end_time": end_time_str
        }
    }
    
    slots_data.append(slot)
    
    # Move to the next 15-minute interval
    start_time = end_time

# Write the data to a JSON file
with open('./fixture/slots/doctor_slots.json', 'w') as json_file:
    json.dump(slots_data, json_file, indent=4)

print("✅ JSON file for doctor slots created successfully!")