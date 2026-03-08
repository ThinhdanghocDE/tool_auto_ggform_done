"""
Ví dụ sử dụng Selenium để điền Google Form
"""

from google_form_selenium import GoogleFormAutoFillSelenium
from google_form_auto_fill import GoogleFormAutoFill

# URL của Google Form
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"

def example_1_selenium_basic():
    """Ví dụ 1: Sử dụng Selenium cơ bản"""
    print("=" * 60)
    print("VÍ DỤ 1: Submit với Selenium (hiển thị browser)")
    print("=" * 60)
    
    # Tạo instance (headless=False để xem browser)
    form_filler = GoogleFormAutoFillSelenium(FORM_URL, headless=False)
    
    try:
        # Lấy danh sách câu hỏi
        api_filler = GoogleFormAutoFill(FORM_URL)
        questions = api_filler.get_questions()
        fields = api_filler.get_form_fields()
        
        # Tạo dữ liệu ngẫu nhiên
        data = api_filler.generate_random_data(fields)
        
        # Submit
        form_filler.submit_form(data, questions=questions, delay=1.0)
        
    finally:
        form_filler.close()


def example_2_selenium_multiple():
    """Ví dụ 2: Submit nhiều lần với Selenium"""
    print("\n" + "=" * 60)
    print("VÍ DỤ 2: Submit nhiều lần với Selenium")
    print("=" * 60)
    
    # Tạo instance (headless=True để ẩn browser)
    form_filler = GoogleFormAutoFillSelenium(FORM_URL, headless=True)
    
    try:
        # Lấy danh sách câu hỏi
        api_filler = GoogleFormAutoFill(FORM_URL)
        questions = api_filler.get_questions()
        
        # Submit nhiều lần
        form_filler.auto_fill_and_submit(
            num_submissions=3,
            questions=questions,
            delay=3.0
        )
        
    finally:
        form_filler.close()


def example_3_selenium_custom_data():
    """Ví dụ 3: Submit với dữ liệu tùy chỉnh"""
    print("\n" + "=" * 60)
    print("VÍ DỤ 3: Submit với dữ liệu tùy chỉnh")
    print("=" * 60)
    
    # Dữ liệu tùy chỉnh
    custom_data = {
        'entry.667922728': 'Nam',
        'entry.1830200648': 'Dưới 25 tuổi',
        'entry.463079656': 'Dưới 10 triệu VNĐ',
        # Thêm các entry IDs khác...
    }
    
    form_filler = GoogleFormAutoFillSelenium(FORM_URL, headless=False)
    
    try:
        # Lấy danh sách câu hỏi
        api_filler = GoogleFormAutoFill(FORM_URL)
        questions = api_filler.get_questions()
        
        # Submit với dữ liệu tùy chỉnh
        form_filler.submit_form(custom_data, questions=questions, delay=1.0)
        
    finally:
        form_filler.close()


if __name__ == "__main__":
    # Chọn ví dụ muốn chạy
    example_1_selenium_basic()
    # example_2_selenium_multiple()
    # example_3_selenium_custom_data()

