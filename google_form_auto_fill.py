"""
Tool tự động điền Google Form
Hỗ trợ điền và submit form tự động với dữ liệu ngẫu nhiên hoặc tùy chỉnh
"""

import requests
import time
import random
from typing import Dict, List, Optional
import json
from bs4 import BeautifulSoup


class GoogleFormAutoFill:
    def __init__(self, form_url: str):
        """
        Khởi tạo với URL của Google Form
        
        Args:
            form_url: URL của Google Form (có thể là viewform hoặc formResponse)
        """
        self.form_url = form_url
        self.submit_url = self._convert_to_submit_url(form_url)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _convert_to_submit_url(self, url: str) -> str:
        """Chuyển đổi URL từ viewform sang formResponse"""
        if 'formResponse' in url:
            return url
        if '/viewform' in url:
            return url.replace('/viewform', '/formResponse')
        # Nếu không có viewform, thử thêm formResponse
        if '/d/e/' in url:
            parts = url.split('/d/e/')
            if len(parts) == 2:
                form_id = parts[1].split('/')[0]
                return f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
        return url
    
    def _parse_form_data_from_js(self, html_content: str) -> Dict:
        """
        Parse form data từ JavaScript (Google Forms thường load tất cả data trong JS)
        Hỗ trợ form nhiều trang/section
        Cấu trúc: FB_PUBLIC_LOAD_DATA_[1][1] chứa list questions
        """
        import re
        import json
        
        fields = {}
        
        try:
            # Tìm FB_PUBLIC_LOAD_DATA hoặc FB_PUBLIC_LOAD_DATA_ (có thể có dấu gạch dưới)
            patterns = [
                r'var\s+FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);',  # Với dấu gạch dưới
                r'var\s+FB_PUBLIC_LOAD_DATA\s*=\s*(\[.*?\]);',   # Không có dấu gạch dưới
            ]
            
            match = None
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    break
            
            if match:
                try:
                    # Parse JSON data
                    js_data = match.group(1)
                    # Fix JSON nếu có vấn đề với trailing commas
                    js_data = re.sub(r',(\s*[}\]])', r'\1', js_data)
                    form_data = json.loads(js_data)
                    
                    # Cấu trúc: [null, [description, [questions...]], ...]
                    # FB_PUBLIC_LOAD_DATA_[1] = [description, [questions...]]
                    if isinstance(form_data, list) and len(form_data) > 1:
                        # form_data[1] chứa [description, [questions...]]
                        if isinstance(form_data[1], list) and len(form_data[1]) > 1:
                            questions_list = form_data[1][1]  # Lấy list questions
                            
                            if isinstance(questions_list, list):
                                for question in questions_list:
                                    if isinstance(question, list) and len(question) > 4:
                                        # Cấu trúc question: [id, text, desc, type, [entry_id, [choices...]], required, ...]
                                        question_id = question[0] if len(question) > 0 else None
                                        question_text = question[1] if len(question) > 1 and isinstance(question[1], str) else ""
                                        question_type = question[3] if len(question) > 3 else 0
                                        
                                        # question[4] = [[entry_id, [choices...]], ...] hoặc [entry_id, [choices...]]
                                        if len(question) > 4 and isinstance(question[4], list) and len(question[4]) > 0:
                                            # Kiểm tra xem question[4][0] có phải là list không
                                            if isinstance(question[4][0], list) and len(question[4][0]) > 0:
                                                entry_id = question[4][0][0]  # Nested list structure
                                            else:
                                                entry_id = question[4][0]  # Direct structure
                                            
                                            # Map question type
                                            type_map = {
                                                0: 'text',
                                                1: 'radio',  # Lựa chọn đơn
                                                2: 'radio',  # Multiple choice (chọn 1) - thực tế là radio
                                                3: 'dropdown',
                                                4: 'checkbox',  # Multiple choice checkbox (chọn nhiều)
                                                5: 'linear_scale',  # Scale 1-5
                                                6: 'date',
                                                7: 'time',
                                                8: 'section_header'  # Section header
                                            }
                                            
                                            field_type = type_map.get(question_type, 'text')
                                            
                                            # Check required (thường ở index 5)
                                            is_required = len(question) > 5 and question[5] == 1
                                            
                                            # Bỏ qua section headers (type 8)
                                            if question_type != 8:
                                                entry_name = f'entry.{entry_id}'
                                                
                                                # Lấy danh sách lựa chọn (choices) nếu có
                                                choices = []
                                                if isinstance(question[4][0], list) and len(question[4][0]) > 1:
                                                    choices_data = question[4][0][1]  # [choices...]
                                                    if isinstance(choices_data, list):
                                                        for choice in choices_data:
                                                            if isinstance(choice, list) and len(choice) > 0:
                                                                choice_text = choice[0] if isinstance(choice[0], str) else str(choice[0])
                                                                choices.append(choice_text)
                                                
                                                # Lấy scale range cho linear_scale (nếu có)
                                                scale_min = None
                                                scale_max = None
                                                if question_type == 5 and isinstance(question[4][0], list) and len(question[4][0]) > 1:
                                                    scale_data = question[4][0][1]
                                                    if isinstance(scale_data, list) and len(scale_data) > 0:
                                                        # Scale thường là ["1", "2", "3", "4", "5"]
                                                        if all(isinstance(x, list) and len(x) > 0 for x in scale_data):
                                                            scale_values = [x[0] for x in scale_data if isinstance(x[0], (str, int))]
                                                            if scale_values:
                                                                try:
                                                                    scale_min = int(scale_values[0])
                                                                    scale_max = int(scale_values[-1])
                                                                except:
                                                                    pass
                                                
                                                fields[entry_name] = {
                                                    'type': field_type,
                                                    'required': is_required,
                                                    'label': question_text,
                                                    'choices': choices if choices else None,
                                                    'scale_min': scale_min,
                                                    'scale_max': scale_max
                                                }
                except Exception as e:
                    print(f"Lỗi parse JSON từ JS: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Nếu không tìm thấy FB_PUBLIC_LOAD_DATA, thử tìm entry IDs trong JS
            if not fields:
                matches = re.findall(r'entry\.(\d+)', html_content)
                for entry_id in set(matches):
                    entry_name = f'entry.{entry_id}'
                    if entry_name not in fields:
                        fields[entry_name] = {
                            'type': 'text',
                            'required': False,
                            'label': f'Field {entry_id}'
                        }
            
        except Exception as e:
            print(f"Lỗi khi parse JS: {e}")
            import traceback
            traceback.print_exc()
        
        return fields
    
    def get_form_fields(self) -> Dict:
        """
        Lấy thông tin các trường trong form bằng cách parse HTML và JavaScript
        Hỗ trợ form nhiều trang/section
        Trả về dictionary với entry IDs và loại field
        """
        try:
            viewform_url = self.form_url.replace('/formResponse', '/viewform')
            if '/formResponse' not in viewform_url and '/viewform' not in viewform_url:
                viewform_url = self.form_url
            
            response = self.session.get(viewform_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            fields = {}
            
            # Cách 1: Parse từ JavaScript (ưu tiên - lấy được tất cả sections)
            js_fields = self._parse_form_data_from_js(html_content)
            if js_fields:
                fields.update(js_fields)
                print(f"✓ Đã parse {len(fields)} fields từ JavaScript (bao gồm tất cả sections)")
            
            # Cách 2: Parse từ HTML (backup)
            if not fields:
                inputs = soup.find_all(['input', 'textarea', 'select'])
                
                for inp in inputs:
                    name = inp.get('name', '')
                    if name.startswith('entry.'):
                        field_type = inp.get('type', 'text')
                        if not field_type and inp.name == 'textarea':
                            field_type = 'textarea'
                        elif not field_type and inp.name == 'select':
                            field_type = 'select'
                        
                        if name not in fields:  # Chỉ thêm nếu chưa có từ JS
                            fields[name] = {
                                'type': field_type,
                                'required': inp.has_attr('required'),
                                'label': self._find_label(soup, inp)
                            }
            
            return fields
        except Exception as e:
            print(f"Lỗi khi lấy thông tin form: {e}")
            return {}
    
    def _find_label(self, soup: BeautifulSoup, element) -> str:
        """Tìm label tương ứng với field"""
        try:
            # Tìm label bằng aria-label hoặc label tag
            label = element.get('aria-label', '')
            if not label:
                # Tìm label tag gần nhất
                parent = element.find_parent()
                if parent:
                    label_tag = parent.find('label')
                    if label_tag:
                        label = label_tag.get_text(strip=True)
            return label
        except:
            return ""
    
    def get_questions(self) -> List[Dict]:
        """
        Lấy danh sách câu hỏi trong form với thông tin chi tiết
        Hỗ trợ form nhiều trang/section
        
        Returns:
            List các dictionary chứa thông tin câu hỏi
        """
        try:
            viewform_url = self.form_url.replace('/formResponse', '/viewform')
            if '/formResponse' not in viewform_url and '/viewform' not in viewform_url:
                viewform_url = self.form_url
            
            response = self.session.get(viewform_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            questions = []
            
            # Ưu tiên: Parse từ JavaScript (lấy được tất cả sections)
            import re
            import json
            
            # Tìm FB_PUBLIC_LOAD_DATA hoặc FB_PUBLIC_LOAD_DATA_
            patterns = [
                r'var\s+FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);',
                r'var\s+FB_PUBLIC_LOAD_DATA\s*=\s*(\[.*?\]);',
            ]
            
            match = None
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    break
            
            if match:
                try:
                    js_data = match.group(1)
                    js_data = re.sub(r',(\s*[}\]])', r'\1', js_data)
                    form_data = json.loads(js_data)
                    
                    # Cấu trúc thực tế: [null, [description, [questions...]], ...]
                    # form_data[1] = [description, [questions...]]
                    if isinstance(form_data, list) and len(form_data) > 1:
                        if isinstance(form_data[1], list) and len(form_data[1]) > 1:
                            questions_list = form_data[1][1]  # Lấy list questions
                            
                            if isinstance(questions_list, list):
                                for question in questions_list:
                                    if isinstance(question, list) and len(question) > 4:
                                        # Cấu trúc: [id, text, desc, type, [entry_id, [choices...]], required, ...]
                                        question_text = question[1] if len(question) > 1 and isinstance(question[1], str) else ""
                                        question_type = question[3] if len(question) > 3 else 0
                                        
                                        # question[4] = [[entry_id, [choices...]], ...] hoặc [entry_id, [choices...]]
                                        if isinstance(question[4], list) and len(question[4]) > 0:
                                            # Kiểm tra xem question[4][0] có phải là list không
                                            if isinstance(question[4][0], list) and len(question[4][0]) > 0:
                                                entry_id = question[4][0][0]  # Nested list structure
                                            else:
                                                entry_id = question[4][0]  # Direct structure
                                            
                                            type_map = {
                                                0: 'text', 1: 'radio', 2: 'radio', 3: 'dropdown',
                                                4: 'checkbox', 5: 'linear_scale', 6: 'date', 7: 'time', 8: 'section_header'
                                            }
                                            
                                            field_type = type_map.get(question_type, 'text')
                                            is_required = len(question) > 5 and question[5] == 1
                                            
                                            # Bỏ qua section headers (type 8)
                                            if question_type != 8:
                                                # Lấy danh sách lựa chọn (choices) nếu có
                                                choices = []
                                                if isinstance(question[4][0], list) and len(question[4][0]) > 1:
                                                    choices_data = question[4][0][1]
                                                    if isinstance(choices_data, list):
                                                        for choice in choices_data:
                                                            if isinstance(choice, list) and len(choice) > 0:
                                                                choice_text = choice[0] if isinstance(choice[0], str) else str(choice[0])
                                                                choices.append(choice_text)
                                                
                                                # Lấy scale range cho linear_scale
                                                scale_min = None
                                                scale_max = None
                                                if question_type == 5 and isinstance(question[4][0], list) and len(question[4][0]) > 1:
                                                    scale_data = question[4][0][1]
                                                    if isinstance(scale_data, list) and len(scale_data) > 0:
                                                        if all(isinstance(x, list) and len(x) > 0 for x in scale_data):
                                                            scale_values = [x[0] for x in scale_data if isinstance(x[0], (str, int))]
                                                            if scale_values:
                                                                try:
                                                                    scale_min = int(scale_values[0])
                                                                    scale_max = int(scale_values[-1])
                                                                except:
                                                                    pass
                                                
                                                questions.append({
                                                    'entry_id': f'entry.{entry_id}',
                                                    'question': question_text or f'Field {entry_id}',
                                                    'type': field_type,
                                                    'required': is_required,
                                                    'choices': choices if choices else None,
                                                    'scale_min': scale_min,
                                                    'scale_max': scale_max
                                                })
                except Exception as e:
                    print(f"Lỗi parse questions từ JS: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Nếu không parse được từ JS, dùng cách cũ (parse từ HTML)
            if not questions:
                # Google Forms thường dùng các class này cho câu hỏi
                # Tìm các item container
                question_containers = soup.find_all(['div'], class_=lambda x: x and (
                    'freebirdFormviewerViewItemsItemItem' in x or
                    'ItemItem' in x or
                    'form-field' in x.lower()
                ))
                
                # Nếu không tìm thấy bằng class, thử tìm bằng structure
                if not question_containers:
                    # Tìm các div chứa input/textarea/select và lấy parent
                    inputs = soup.find_all(['input', 'textarea', 'select'], {'name': lambda x: x and x.startswith('entry.')})
                    seen_entries = set()
                    
                    for inp in inputs:
                        entry_name = inp.get('name', '')
                        if entry_name and entry_name not in seen_entries:
                            seen_entries.add(entry_name)
                            
                            # Tìm câu hỏi từ parent elements
                            parent = inp.find_parent()
                            question_text = ""
                            field_type = inp.get('type', 'text')
                            
                            # Tìm title/label của câu hỏi
                            if parent:
                                # Tìm trong các class phổ biến của Google Forms
                                title_elem = parent.find(['div', 'span', 'label'], class_=lambda x: x and (
                                    'ItemTitle' in x or 'title' in x.lower() or 'label' in x.lower()
                                ))
                                if title_elem:
                                    question_text = title_elem.get_text(strip=True)
                                
                                # Nếu không tìm thấy, thử aria-label
                                if not question_text:
                                    question_text = inp.get('aria-label', '')
                                
                                # Nếu vẫn không có, thử tìm label tag
                                if not question_text:
                                    label_tag = parent.find('label')
                                    if label_tag:
                                        question_text = label_tag.get_text(strip=True)
                            
                            # Xác định loại field
                            if inp.name == 'textarea':
                                field_type = 'textarea'
                            elif inp.name == 'select':
                                field_type = 'select'
                            elif field_type == 'radio':
                                field_type = 'radio'
                            elif field_type == 'checkbox':
                                field_type = 'checkbox'
                            
                            questions.append({
                                'entry_id': entry_name,
                                'question': question_text or f'Câu hỏi {entry_name}',
                                'type': field_type,
                                'required': inp.has_attr('required')
                            })
                else:
                    # Parse từ question containers
                    for container in question_containers:
                        # Tìm entry ID
                        inp = container.find(['input', 'textarea', 'select'], {'name': lambda x: x and x.startswith('entry.')})
                        if inp:
                            entry_name = inp.get('name', '')
                            field_type = inp.get('type', 'text')
                            
                            # Tìm câu hỏi
                            title_elem = container.find(['div', 'span'], class_=lambda x: x and 'title' in x.lower())
                            question_text = title_elem.get_text(strip=True) if title_elem else ""
                            
                            questions.append({
                                'entry_id': entry_name,
                                'question': question_text or f'Câu hỏi {entry_name}',
                                'type': field_type,
                                'required': inp.has_attr('required')
                            })
            
            # Nếu vẫn không tìm thấy, dùng cách cũ
            if not questions:
                fields = self.get_form_fields()
                for entry_id, field_info in fields.items():
                    questions.append({
                        'entry_id': entry_id,
                        'question': field_info.get('label', f'Field {entry_id}'),
                        'type': field_info.get('type', 'text'),
                        'required': field_info.get('required', False)
                    })
            
            return questions
        except Exception as e:
            print(f"Lỗi khi lấy danh sách câu hỏi: {e}")
            return []
    
    def list_questions(self):
        """
        Hiển thị danh sách câu hỏi trong form một cách đẹp mắt
        """
        print("\n" + "="*70)
        print("DANH SÁCH CÂU HỎI TRONG FORM")
        print("="*70)
        
        questions = self.get_questions()
        
        if not questions:
            print("⚠ Không tìm thấy câu hỏi nào trong form.")
            print("\nCó thể form sử dụng JavaScript để render.")
            print("Hãy thử mở form trong trình duyệt và inspect để xem cấu trúc.")
            return
        
        print(f"\nTìm thấy {len(questions)} câu hỏi:\n")
        
        for idx, q in enumerate(questions, 1):
            required_mark = " [BẮT BUỘC]" if q['required'] else ""
            type_name = {
                'text': 'Văn bản',
                'textarea': 'Văn bản dài',
                'email': 'Email',
                'number': 'Số',
                'date': 'Ngày tháng',
                'radio': 'Lựa chọn đơn',
                'checkbox': 'Lựa chọn nhiều',
                'select': 'Dropdown'
            }.get(q['type'], q['type'].upper())
            
            print(f"{idx}. {q['question']}{required_mark}")
            print(f"   Entry ID: {q['entry_id']}")
            print(f"   Loại: {type_name}")
            print()
        
        print("="*70)
        print("\nĐể sử dụng trong code:")
        print("-"*70)
        print("custom_data = {")
        for q in questions:
            print(f"    '{q['entry_id']}': 'Giá trị của bạn',  # {q['question']}")
        print("}")
        print("="*70 + "\n")
    
    def generate_random_data(self, fields: Dict, field_config: Optional[Dict] = None) -> Dict:
        """
        Tạo dữ liệu ngẫu nhiên cho các trường trong form
        Sử dụng choices từ form để tạo dữ liệu thực tế
        Hỗ trợ cấu hình fixed/random cho từng field
        
        Args:
            fields: Dictionary chứa thông tin các trường (có thể có 'choices', 'scale_min', 'scale_max')
            field_config: Dictionary cấu hình cho từng field:
                {
                    "entry.xxx": {
                        "mode": "fixed" hoặc "random",
                        "value": "Giá trị cố định (nếu fixed)",
                        "random_from": ["option1", "option2"] (nếu random, để trống = random từ tất cả)
                    }
                }
            
        Returns:
            Dictionary với entry IDs và giá trị tương ứng
        """
        data = {}
        
        # Dữ liệu mẫu fallback
        names = ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Phạm Thị D", "Hoàng Văn E"]
        emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
        comments = [
            "Rất hài lòng với dịch vụ!",
            "Cần cải thiện thêm một số điểm.",
            "Tuyệt vời, sẽ giới thiệu cho bạn bè.",
            "Ổn, nhưng có thể tốt hơn.",
            "Rất tốt, cảm ơn!"
        ]
        
        for entry_id, field_info in fields.items():
            field_type = field_info.get('type', 'text')
            label = field_info.get('label', '').lower()
            choices = field_info.get('choices')
            
            # Kiểm tra config cho field này
            field_cfg = None
            if field_config and 'fields' in field_config:
                field_cfg = field_config['fields'].get(entry_id)
            
            # Nếu có config, sử dụng config
            if field_cfg:
                mode = field_cfg.get('mode', 'random')
                
                if mode == 'fixed':
                    # Giá trị cố định
                    data[entry_id] = field_cfg.get('value', '')
                    continue
                elif mode == 'random':
                    # Random từ danh sách chỉ định
                    random_from = field_cfg.get('random_from', [])
                    if random_from and len(random_from) > 0:
                        # Random từ danh sách chỉ định
                        if field_type == 'checkbox':
                            # Checkbox: chọn 1-3 từ danh sách
                            num_choices = random.randint(1, min(3, len(random_from)))
                            data[entry_id] = random.sample(random_from, num_choices)
                        else:
                            # Radio/Dropdown: chọn 1
                            data[entry_id] = random.choice(random_from)
                        continue
            
            # Nếu không có config hoặc config không áp dụng, dùng logic mặc định
            # Radio (chọn 1) - sử dụng choices từ form
            if field_type == 'radio':
                if choices and len(choices) > 0:
                    data[entry_id] = random.choice(choices)
                else:
                    # Fallback nếu không có choices
                    data[entry_id] = random.choice(["Lựa chọn 1", "Lựa chọn 2", "Lựa chọn 3"])
            
            # Checkbox (chọn nhiều) - chọn 1-3 lựa chọn ngẫu nhiên
            elif field_type == 'checkbox':
                if choices and len(choices) > 0:
                    # Chọn từ 1 đến min(3, số lượng choices) lựa chọn
                    num_choices = random.randint(1, min(3, len(choices)))
                    selected = random.sample(choices, num_choices)
                    # Google Forms checkbox cần gửi dạng list hoặc string tùy format
                    data[entry_id] = selected  # Sẽ xử lý format khi submit
                else:
                    data[entry_id] = ["Lựa chọn 1"]
            
            # Linear Scale - sử dụng scale từ form
            elif field_type == 'linear_scale':
                # Kiểm tra config cho linear_scale
                if field_cfg and field_cfg.get('mode') == 'random' and field_cfg.get('random_from'):
                    # Random từ danh sách chỉ định
                    random_from = field_cfg.get('random_from', [])
                    if random_from:
                        data[entry_id] = str(random.choice(random_from))
                        continue
                
                scale_min = field_info.get('scale_min', 1)
                scale_max = field_info.get('scale_max', 5)
                if scale_min is not None and scale_max is not None:
                    data[entry_id] = str(random.randint(scale_min, scale_max))
                else:
                    data[entry_id] = str(random.randint(1, 5))
            
            # Dropdown - giống radio (chọn 1)
            elif field_type == 'dropdown':
                if choices and len(choices) > 0:
                    data[entry_id] = random.choice(choices)
                else:
                    data[entry_id] = "Lựa chọn 1"
            
            # Text fields
            elif 'email' in label or field_type == 'email':
                data[entry_id] = random.choice(emails)
            elif 'tên' in label or 'name' in label or 'họ' in label:
                data[entry_id] = random.choice(names)
            elif 'comment' in label or 'ý kiến' in label or 'feedback' in label or field_type == 'textarea':
                data[entry_id] = random.choice(comments)
            elif field_type == 'number':
                data[entry_id] = str(random.randint(1, 10))
            elif field_type == 'date':
                data[entry_id] = f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            else:
                # Text field mặc định
                data[entry_id] = f"Giá trị ngẫu nhiên {random.randint(1, 1000)}"
        
        return data
    
    def _get_hidden_fields(self, html_content: str) -> Dict:
        """
        Lấy các hidden fields cần thiết từ form HTML
        """
        from bs4 import BeautifulSoup
        import re
        
        hidden_fields = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Tìm các input hidden
            hidden_inputs = soup.find_all('input', type='hidden')
            for inp in hidden_inputs:
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    hidden_fields[name] = value
            
            # Tìm fbzx từ URL hoặc form data
            fbzx_match = re.search(r'fbzx=([^&"\']+)', html_content)
            if fbzx_match:
                hidden_fields['fbzx'] = fbzx_match.group(1)
            
            # Tìm từ form action
            form = soup.find('form', {'action': lambda x: x and 'formResponse' in x})
            if form:
                action = form.get('action', '')
                fbzx_match = re.search(r'fbzx=([^&"\']+)', action)
                if fbzx_match:
                    hidden_fields['fbzx'] = fbzx_match.group(1)
        
        except Exception as e:
            print(f"Lưu ý: Không lấy được hidden fields: {e}")
        
        return hidden_fields
    
    def submit_form(self, data: Dict, delay: float = 1.0) -> bool:
        """
        Submit form với dữ liệu đã cho
        
        Args:
            data: Dictionary chứa entry IDs và giá trị (có thể có list cho checkbox)
            delay: Thời gian delay trước khi submit (giây)
            
        Returns:
            True nếu submit thành công, False nếu có lỗi
        """
        time.sleep(delay)
        
        try:
            # Lấy HTML form để lấy hidden fields
            try:
                form_response = self.session.get(self.form_url.replace('/formResponse', '/viewform'))
                hidden_fields = self._get_hidden_fields(form_response.text)
            except:
                hidden_fields = {}
            
            # Xử lý checkbox - Google Forms cần gửi nhiều giá trị cùng key
            # Sử dụng list of tuples để requests có thể gửi nhiều giá trị cùng key
            submit_data_list = []
            
            # Thêm hidden fields trước
            for key, value in hidden_fields.items():
                if value:  # Chỉ thêm nếu có giá trị
                    submit_data_list.append((key, str(value)))
            
            # Thêm dữ liệu form
            for entry_id, value in data.items():
                if isinstance(value, list):
                    # Checkbox: gửi từng giá trị với cùng entry_id
                    for val in value:
                        submit_data_list.append((entry_id, str(val)))
                else:
                    submit_data_list.append((entry_id, str(value)))
            
            # Thêm các tham số cần thiết cho Google Forms
            params = {
                'submit': 'Submit'
            }
            
            # Gửi với list of tuples - requests sẽ tự xử lý nhiều giá trị cùng key
            response = self.session.post(
                self.submit_url,
                data=submit_data_list,
                params=params,
                allow_redirects=True,
                timeout=10
            )
            
            # Google Forms trả về 200 hoặc redirect nếu submit thành công
            # Kiểm tra nội dung response để xác nhận
            if response.status_code in [200, 302]:
                # Kiểm tra xem có thông báo thành công không
                if 'formResponse' in response.url or 'thankyou' in response.url.lower() or response.status_code == 200:
                    print(f"✓ Submit thành công! Status: {response.status_code}")
                    return True
            
            print(f"✗ Submit thất bại. Status: {response.status_code}")
            print(f"  URL response: {response.url[:100]}...")
            return False
                
        except Exception as e:
            print(f"✗ Lỗi khi submit: {e}")
            return False
    
    def auto_fill_and_submit(self, num_submissions: int = 1, custom_data: Optional[Dict] = None, delay: float = 2.0, field_config: Optional[Dict] = None):
        """
        Tự động điền và submit form nhiều lần
        
        Args:
            num_submissions: Số lần submit
            custom_data: Dữ liệu tùy chỉnh (nếu None sẽ dùng random)
            delay: Thời gian delay giữa các lần submit (giây)
        """
        print(f"Đang lấy thông tin form từ: {self.form_url}")
        fields = self.get_form_fields()
        
        if not fields:
            print("⚠ Không tìm thấy fields. Sẽ thử submit với dữ liệu mẫu...")
            # Nếu không parse được, thử với một số entry IDs phổ biến
            fields = {
                'entry.0': {'type': 'text', 'label': 'Field 1'},
                'entry.1': {'type': 'text', 'label': 'Field 2'},
            }
        
        print(f"Tìm thấy {len(fields)} trường trong form")
        print("\n" + "="*50)
        
        success_count = 0
        
        for i in range(num_submissions):
            print(f"\n[{i+1}/{num_submissions}] Đang submit...")
            
            if custom_data:
                data = custom_data.copy()
            else:
                data = self.generate_random_data(fields, field_config=field_config)
            
            # In ra một số dữ liệu để kiểm tra
            print(f"Dữ liệu mẫu: {list(data.items())[:3]}...")
            
            if self.submit_form(data, delay=0.5):
                success_count += 1
            
            # Delay giữa các lần submit
            if i < num_submissions - 1:
                time.sleep(delay)
        
        print("\n" + "="*50)
        print(f"Hoàn thành! Đã submit thành công {success_count}/{num_submissions} lần")


def main():
    """Hàm main để chạy script"""
    # URL của Google Form
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"
    
    # Tạo instance
    form_filler = GoogleFormAutoFill(form_url)
    
    # Tùy chỉnh dữ liệu (nếu muốn)
    # custom_data = {
    #     'entry.123456789': 'Giá trị tùy chỉnh 1',
    #     'entry.987654321': 'Giá trị tùy chỉnh 2',
    # }
    
    # Chạy auto fill
    # num_submissions: Số lần submit
    # custom_data: None để dùng random, hoặc dict để dùng dữ liệu tùy chỉnh
    # delay: Thời gian delay giữa các lần submit (giây)
    form_filler.auto_fill_and_submit(
        num_submissions=5,  # Số lần submit
        custom_data=None,   # None = random, hoặc dict với entry IDs
        delay=2.0           # Delay 2 giây giữa các lần
    )


if __name__ == "__main__":
    import sys
    
    # Kiểm tra argument để xem có muốn list questions không
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        # Chế độ list questions
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegeM6Ymz07IMSY3-354fgX4yBFqC7k63fwNJOkmLhlYSsUVQ/viewform"
        form_filler = GoogleFormAutoFill(form_url)
        form_filler.list_questions()
    else:
        # Chế độ submit bình thường
        main()

