"""
Demo: Minh họa cách hoạt động của Fixed và Random
"""

from google_form_auto_fill import GoogleFormAutoFill
import json

# URL form
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"

# Cấu hình ví dụ:
# - Giới tính: Fixed = "Nam" (luôn giống nhau)
# - Độ tuổi: Random từ ["Từ 25 - 34 tuổi", "Từ 35 - 44 tuổi"] (khác nhau mỗi lần)
# - Thu nhập: Random từ tất cả options (khác nhau mỗi lần)

field_config = {
    'fields': {
        'entry.667922728': {  # Giới tính
            'mode': 'fixed',
            'value': 'Nam'
        },
        'entry.1830200648': {  # Độ tuổi
            'mode': 'random',
            'random_from': ['Từ 25 - 34 tuổi', 'Từ 35 - 44 tuổi']
        },
        'entry.463079656': {  # Thu nhập - random từ tất cả
            'mode': 'random'
            # Không có random_from = random từ tất cả options
        }
    }
}

print("="*70)
print("DEMO: Fixed vs Random")
print("="*70)
print("\nCấu hình:")
print("- Giới tính: Fixed = 'Nam' (luôn giống nhau)")
print("- Độ tuổi: Random từ ['Từ 25 - 34 tuổi', 'Từ 35 - 44 tuổi'] (khác nhau)")
print("- Thu nhập: Random từ tất cả options (khác nhau)")
print("\n" + "="*70)

form_filler = GoogleFormAutoFill(form_url)
fields = form_filler.get_form_fields()

# Tạo 5 bộ dữ liệu mẫu
print("\nTạo 5 bộ dữ liệu mẫu:\n")
for i in range(5):
    data = form_filler.generate_random_data(fields, field_config=field_config)
    
    print(f"Lần {i+1}:")
    print(f"  Giới tính (Fixed): {data.get('entry.667922728', 'N/A')}")
    print(f"  Độ tuổi (Random): {data.get('entry.1830200648', 'N/A')}")
    print(f"  Thu nhập (Random): {data.get('entry.463079656', 'N/A')}")
    print()

print("="*70)
print("KẾT LUẬN:")
print("- Giới tính: LUÔN là 'Nam' (Fixed)")
print("- Độ tuổi: KHÁC NHAU mỗi lần (Random từ 2 options)")
print("- Thu nhập: KHÁC NHAU mỗi lần (Random từ tất cả options)")
print("="*70)

