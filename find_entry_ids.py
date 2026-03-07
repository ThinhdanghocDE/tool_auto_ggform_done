"""
Script helper để tìm Entry IDs trong Google Form
Chạy script này để xem các entry IDs có trong form
"""

import requests
from bs4 import BeautifulSoup
import re


def find_entry_ids(form_url: str):
    """
    Tìm tất cả entry IDs trong Google Form
    
    Args:
        form_url: URL của Google Form
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        print(f"Đang truy cập form: {form_url}\n")
        response = session.get(form_url)
        
        # Tìm entry IDs trong HTML
        entry_ids = set()
        
        # Tìm trong HTML content
        matches = re.findall(r'entry\.(\d+)', response.text)
        entry_ids.update(matches)
        
        # Parse HTML để tìm thêm
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm trong input, textarea, select
        for tag in soup.find_all(['input', 'textarea', 'select']):
            name = tag.get('name', '')
            if name.startswith('entry.'):
                entry_id = name.replace('entry.', '')
                entry_ids.add(entry_id)
        
        # Tìm trong JavaScript code
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                matches = re.findall(r'entry\.(\d+)', script.string)
                entry_ids.update(matches)
        
        if entry_ids:
            print(f"Tìm thấy {len(entry_ids)} entry IDs:\n")
            sorted_ids = sorted(entry_ids, key=lambda x: int(x) if x.isdigit() else 0)
            
            for entry_id in sorted_ids:
                print(f"  entry.{entry_id}")
            
            print("\n" + "="*50)
            print("Cách sử dụng trong code:")
            print("="*50)
            print("custom_data = {")
            for entry_id in sorted_ids:
                print(f"    'entry.{entry_id}': 'Giá trị của bạn',")
            print("}")
        else:
            print("⚠ Không tìm thấy entry IDs trong HTML.")
            print("\nCó thể form sử dụng JavaScript để render.")
            print("Hãy thử:")
            print("1. Mở form trong trình duyệt")
            print("2. Nhấn F12 để mở DevTools")
            print("3. Vào tab Network")
            print("4. Điền form thủ công và submit")
            print("5. Tìm request 'formResponse' trong Network tab")
            print("6. Xem Form Data để tìm entry IDs")
        
    except Exception as e:
        print(f"Lỗi: {e}")


if __name__ == "__main__":
    # URL form của bạn
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"
    
    find_entry_ids(form_url)

