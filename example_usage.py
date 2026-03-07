"""
Ví dụ sử dụng tool tự động điền Google Form
"""

from google_form_auto_fill import GoogleFormAutoFill

# URL của Google Form
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"

def example_1_random_data():
    """Ví dụ 1: Submit với dữ liệu ngẫu nhiên"""
    print("=" * 60)
    print("VÍ DỤ 1: Submit với dữ liệu ngẫu nhiên")
    print("=" * 60)
    
    form_filler = GoogleFormAutoFill(FORM_URL)
    form_filler.auto_fill_and_submit(
        num_submissions=3,  # Submit 3 lần
        custom_data=None,   # Dùng dữ liệu ngẫu nhiên
        delay=2.0           # Delay 2 giây giữa các lần
    )


def example_2_custom_data():
    """Ví dụ 2: Submit với dữ liệu tùy chỉnh"""
    print("\n" + "=" * 60)
    print("VÍ DỤ 2: Submit với dữ liệu tùy chỉnh")
    print("=" * 60)
    
    # LƯU Ý: Bạn cần thay các entry IDs này bằng entry IDs thực tế từ form
    # Chạy find_entry_ids.py để tìm entry IDs
    
    custom_data = {
        # Thay các entry IDs này bằng entry IDs thực tế
        # 'entry.123456789': 'Tên của bạn',
        # 'entry.987654321': 'Email của bạn',
        # 'entry.111222333': 'Ý kiến của bạn',
    }
    
    if not custom_data:
        print("⚠ Chưa có dữ liệu tùy chỉnh.")
        print("Hãy chạy find_entry_ids.py để tìm entry IDs, sau đó điền vào custom_data")
        return
    
    form_filler = GoogleFormAutoFill(FORM_URL)
    form_filler.auto_fill_and_submit(
        num_submissions=1,
        custom_data=custom_data,
        delay=1.0
    )


def example_3_single_submit():
    """Ví dụ 3: Submit một lần với dữ liệu ngẫu nhiên"""
    print("\n" + "=" * 60)
    print("VÍ DỤ 3: Submit một lần")
    print("=" * 60)
    
    form_filler = GoogleFormAutoFill(FORM_URL)
    
    # Lấy thông tin form
    fields = form_filler.get_form_fields()
    print(f"Tìm thấy {len(fields)} trường trong form")
    
    # Tạo dữ liệu ngẫu nhiên
    data = form_filler.generate_random_data(fields)
    
    # In dữ liệu để xem
    print("\nDữ liệu sẽ được submit:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    # Submit
    print("\nĐang submit...")
    success = form_filler.submit_form(data)
    
    if success:
        print("✓ Thành công!")
    else:
        print("✗ Thất bại!")


if __name__ == "__main__":
    # Chọn ví dụ muốn chạy
    # example_1_random_data()
    # example_2_custom_data()
    example_3_single_submit()

