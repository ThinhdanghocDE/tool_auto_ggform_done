"""
Script để liệt kê tất cả câu hỏi trong Google Form
"""

from google_form_auto_fill import GoogleFormAutoFill

def main():
    # URL của Google Form
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"
    
    # Tạo instance
    form_filler = GoogleFormAutoFill(form_url)
    
    # Hiển thị danh sách câu hỏi
    form_filler.list_questions()
    
    # Lấy danh sách câu hỏi dạng list (để xử lý trong code)
    questions = form_filler.get_questions()
    
    print("\n" + "="*70)
    print("DỮ LIỆU DẠNG LIST (để xử lý trong code):")
    print("="*70)
    print(f"\nTổng số câu hỏi: {len(questions)}\n")
    
    # In dạng JSON để dễ copy
    import json
    print("JSON format:")
    print(json.dumps(questions, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

