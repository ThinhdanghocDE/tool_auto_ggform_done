"""
Module sử dụng Selenium để điền Google Form như người dùng thật
Giả lập hành vi người dùng: mở form, điền từng field, submit
"""

import time
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GoogleFormAutoFillSelenium:
    def __init__(self, form_url: str, headless: bool = False, browser: str = 'chrome'):
        """
        Khởi tạo với URL của Google Form
        
        Args:
            form_url: URL của Google Form (phải là viewform)
            headless: Chạy browser ở chế độ ẩn (không hiển thị cửa sổ)
            browser: Loại browser ('chrome' hoặc 'firefox')
        """
        self.form_url = form_url
        if '/formResponse' in form_url:
            self.form_url = form_url.replace('/formResponse', '/viewform')
        
        self.driver = None
        self.headless = headless
        self.browser = browser
        self._init_driver()
    
    def _init_driver(self):
        """Khởi tạo WebDriver"""
        try:
            if self.browser.lower() == 'chrome':
                chrome_options = Options()
                if self.headless:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                self.driver = webdriver.Chrome(options=chrome_options)
            else:
                raise ValueError(f"Browser {self.browser} chưa được hỗ trợ. Chỉ hỗ trợ 'chrome'")
            
            # Ẩn dấu hiệu automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            print(f"Lỗi khi khởi tạo WebDriver: {e}")
            print("Hãy đảm bảo đã cài đặt ChromeDriver và thêm vào PATH")
            raise
    
    def _find_element_safe(self, by, value, timeout=10):
        """Tìm element an toàn với timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def _fill_text_field(self, entry_id: str, value: str, delay: float = 0.5):
        """Điền text field"""
        try:
            # Tìm input/textarea với name = entry_id
            element = self._find_element_safe(By.NAME, entry_id)
            if element:
                element.clear()
                time.sleep(delay)
                element.send_keys(value)
                print(f"  ✓ Đã điền {entry_id}: {value}")
                return True
            else:
                print(f"  ✗ Không tìm thấy field {entry_id}")
                return False
        except Exception as e:
            print(f"  ✗ Lỗi khi điền {entry_id}: {e}")
            return False
    
    def _fill_radio(self, entry_id: str, value: str, delay: float = 0.5):
        """Chọn radio button - tìm bằng div[role="radio"] với data-value hoặc aria-label"""
        try:
            entry_num = entry_id.replace('entry.', '')
            
            # Cách 1: Tìm div[role="radio"] với data-value hoặc aria-label
            radios = self.driver.find_elements(By.CSS_SELECTOR, f'div[role="radio"][data-value], div[role="radio"][aria-label]')
            
            # Cách 2: Tìm trong container của entry này (nếu có)
            try:
                # Tìm container có chứa entry_id trong data-params
                containers = self.driver.find_elements(By.CSS_SELECTOR, 'div[jsmodel="CP1oW"][data-params*="' + entry_num + '"]')
                if containers:
                    for container in containers:
                        container_radios = container.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                        radios.extend(container_radios)
            except:
                pass
            
            # Cách 3: Fallback - tìm input[type="radio"]
            if not radios:
                radios = self.driver.find_elements(By.CSS_SELECTOR, f'input[type="radio"][name="{entry_id}"]')
            
            if not radios:
                print(f"  ✗ Không tìm thấy radio buttons cho {entry_id}")
                return False
            
            # Debug: In ra các options có sẵn
            available_options = []
            for radio in radios[:5]:  # Chỉ lấy 5 đầu để debug
                try:
                    option_text = radio.get_attribute('data-value') or radio.get_attribute('aria-label')
                    if option_text:
                        available_options.append(option_text)
                except:
                    pass
            
            if available_options:
                print(f"  Debug: Options có sẵn cho {entry_id}: {available_options}")
            
            # Tìm và click radio phù hợp
            for radio in radios:
                try:
                    # Lấy giá trị từ data-value hoặc aria-label
                    radio_value = radio.get_attribute('data-value') or radio.get_attribute('aria-label') or ''
                    radio_value = radio_value.strip()
                    
                    # So sánh chính xác
                    if radio_value == value:
                        # Click vào radio hoặc label của nó
                        try:
                            radio.click()
                        except:
                            # Thử click vào label
                            try:
                                label = radio.find_element(By.XPATH, './ancestor::label')
                                label.click()
                            except:
                                # Thử click bằng JavaScript
                                self.driver.execute_script("arguments[0].click();", radio)
                        
                        time.sleep(delay)
                        print(f"  ✓ Đã chọn radio {entry_id}: {value}")
                        return True
                    
                    # Thử partial match
                    if value in radio_value or radio_value in value:
                        try:
                            radio.click()
                        except:
                            try:
                                label = radio.find_element(By.XPATH, './ancestor::label')
                                label.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", radio)
                        
                        time.sleep(delay)
                        print(f"  ✓ Đã chọn radio {entry_id}: {value} (match với '{radio_value}')")
                        return True
                except:
                    continue
            
            # Nếu là input[type="radio"], thử cách cũ
            for radio in radios:
                try:
                    if radio.tag_name == 'input':
                        radio_value = radio.get_attribute('value')
                        if radio_value == value:
                            radio.click()
                            time.sleep(delay)
                            print(f"  ✓ Đã chọn radio {entry_id}: {value}")
                            return True
                except:
                    continue
            
            print(f"  ✗ Không tìm thấy option '{value}' cho radio {entry_id}")
            if available_options:
                print(f"     Các options có sẵn: {available_options}")
            return False
        except Exception as e:
            print(f"  ✗ Lỗi khi chọn radio {entry_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fill_checkbox(self, entry_id: str, values: List[str], delay: float = 0.5):
        """Chọn checkbox (có thể chọn nhiều) - tìm bằng div[role="checkbox"] với data-value"""
        try:
            entry_num = entry_id.replace('entry.', '')
            
            # Cách 1: Tìm div[role="checkbox"] với data-value hoặc aria-label
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, f'div[role="checkbox"][data-value], div[role="checkbox"][aria-label]')
            
            # Cách 2: Tìm trong container của entry này (nếu có)
            try:
                containers = self.driver.find_elements(By.CSS_SELECTOR, f'div[jsmodel="CP1oW"][data-params*="{entry_num}"]')
                if containers:
                    for container in containers:
                        container_checkboxes = container.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                        checkboxes.extend(container_checkboxes)
            except:
                pass
            
            # Cách 3: Fallback - tìm input[type="checkbox"]
            if not checkboxes:
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, f'input[type="checkbox"][name="{entry_id}"]')
            
            if not checkboxes:
                print(f"  ✗ Không tìm thấy checkbox buttons cho {entry_id}")
                return False
            
            # Debug: In ra các options có sẵn
            available_options = []
            for checkbox in checkboxes[:8]:  # Chỉ lấy 8 đầu để debug
                try:
                    option_text = checkbox.get_attribute('data-value') or checkbox.get_attribute('aria-label')
                    if option_text:
                        available_options.append(option_text)
                except:
                    pass
            
            if available_options:
                print(f"  Debug: Options có sẵn cho checkbox {entry_id}: {available_options}")
            
            selected_count = 0
            # Debug: In ra values cần chọn
            print(f"  Debug: Values cần chọn (type: {type(values)}): {values}")
            
            # Đảm bảo values là list
            if not isinstance(values, list):
                if isinstance(values, str):
                    # Thử parse nếu là string representation của list
                    import ast
                    try:
                        values = ast.literal_eval(values)
                        if not isinstance(values, list):
                            values = [values]
                    except:
                        values = [values]
                else:
                    values = [values]
            
            # Tìm và click các checkbox phù hợp
            for checkbox in checkboxes:
                try:
                    # Lấy giá trị từ data-value hoặc aria-label
                    checkbox_value = checkbox.get_attribute('data-value') or checkbox.get_attribute('aria-label') or ''
                    checkbox_value = checkbox_value.strip()
                    
                    if not checkbox_value:
                        continue
                    
                    # Kiểm tra xem có trong danh sách values cần chọn không
                    should_select = False
                    matched_value = None
                    for value in values:
                        value_str = str(value).strip()
                        # So sánh chính xác
                        if checkbox_value == value_str:
                            should_select = True
                            matched_value = value_str
                            break
                        # Thử partial match (nếu không match chính xác)
                        elif value_str in checkbox_value or checkbox_value in value_str:
                            should_select = True
                            matched_value = value_str
                            break
                    
                    if should_select:
                        # Kiểm tra xem đã được chọn chưa
                        is_checked = checkbox.get_attribute('aria-checked') == 'true' or checkbox.get_attribute('checked') == 'true'
                        
                        if not is_checked:
                            # Click vào checkbox hoặc label của nó
                            try:
                                checkbox.click()
                            except:
                                # Thử click vào label
                                try:
                                    label = checkbox.find_element(By.XPATH, './ancestor::label')
                                    label.click()
                                except:
                                    # Thử click bằng JavaScript
                                    self.driver.execute_script("arguments[0].click();", checkbox)
                            
                            time.sleep(delay)
                            selected_count += 1
                            print(f"  ✓ Đã chọn checkbox: '{checkbox_value}' (match với '{matched_value}')")
                except Exception as e:
                    print(f"  Debug: Lỗi khi xử lý checkbox: {e}")
                    continue
            
            # Nếu là input[type="checkbox"], thử cách cũ
            if selected_count == 0:
                input_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, f'input[type="checkbox"][name="{entry_id}"]')
                for checkbox in input_checkboxes:
                    try:
                        checkbox_value = checkbox.get_attribute('value')
                        if checkbox_value in values:
                            if not checkbox.is_selected():
                                checkbox.click()
                                time.sleep(delay)
                                selected_count += 1
                    except:
                        continue
            
            if selected_count > 0:
                print(f"  ✓ Đã chọn {selected_count} checkbox(es) cho {entry_id}: {values}")
                return True
            else:
                print(f"  ✗ Không tìm thấy options '{values}' cho checkbox {entry_id}")
                if available_options:
                    print(f"     Các options có sẵn: {available_options}")
                return False
        except Exception as e:
            print(f"  ✗ Lỗi khi chọn checkbox {entry_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fill_dropdown(self, entry_id: str, value: str, delay: float = 0.5):
        """Chọn dropdown"""
        try:
            # Tìm select element
            select = self._find_element_safe(By.CSS_SELECTOR, f'select[name="{entry_id}"]')
            if select:
                from selenium.webdriver.support.ui import Select
                select_obj = Select(select)
                
                # Thử chọn bằng visible text
                try:
                    select_obj.select_by_visible_text(value)
                    time.sleep(delay)
                    print(f"  ✓ Đã chọn dropdown {entry_id}: {value}")
                    return True
                except:
                    # Thử chọn bằng value
                    try:
                        select_obj.select_by_value(value)
                        time.sleep(delay)
                        print(f"  ✓ Đã chọn dropdown {entry_id}: {value}")
                        return True
                    except:
                        print(f"  ✗ Không tìm thấy option '{value}' trong dropdown {entry_id}")
                        return False
            else:
                print(f"  ✗ Không tìm thấy dropdown {entry_id}")
                return False
        except Exception as e:
            print(f"  ✗ Lỗi khi chọn dropdown {entry_id}: {e}")
            return False
    
    def _fill_linear_scale(self, entry_id: str, value: str, delay: float = 0.5):
        """Chọn linear scale (1-5, 1-10, etc.) - tìm bằng div[role="radio"] với data-value"""
        try:
            entry_num = entry_id.replace('entry.', '')
            
            # Cách 1: Tìm div[role="radio"] trong container của entry này
            radios = []
            try:
                containers = self.driver.find_elements(By.CSS_SELECTOR, f'div[jsmodel="CP1oW"][data-params*="{entry_num}"]')
                if containers:
                    for container in containers:
                        container_radios = container.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                        radios.extend(container_radios)
            except:
                pass
            
            # Cách 2: Tìm tất cả div[role="radio"] với data-value là số trong container
            if not radios:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, f'div[jsmodel="CP1oW"][data-params*="{entry_num}"]')
                    if containers:
                        for container in containers:
                            all_radios = container.find_elements(By.CSS_SELECTOR, 'div[role="radio"][data-value]')
                            # Lọc các radio có data-value là số (1-10)
                            for radio in all_radios:
                                radio_value = radio.get_attribute('data-value')
                                if radio_value and (radio_value.isdigit() or radio_value in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']):
                                    radios.append(radio)
                except:
                    pass
            
            # Cách 3: Fallback - tìm input[type="radio"]
            if not radios:
                radios = self.driver.find_elements(By.CSS_SELECTOR, f'input[type="radio"][name="{entry_id}"]')
            
            if not radios:
                print(f"  ✗ Không tìm thấy scale buttons cho {entry_id}")
                return False
            
            # Debug: In ra các values có sẵn
            available_values = []
            for r in radios[:10]:  # Chỉ lấy 10 đầu để debug
                try:
                    radio_value = r.get_attribute('data-value') or r.get_attribute('value') or r.get_attribute('aria-label')
                    if radio_value:
                        available_values.append(radio_value)
                except:
                    pass
            
            if available_values:
                print(f"  Debug: Scale values có sẵn cho {entry_id}: {available_values}")
            
            # Tìm và click radio với value phù hợp
            for radio in radios:
                try:
                    radio_value = radio.get_attribute('data-value') or radio.get_attribute('value') or ''
                    radio_value = radio_value.strip()
                    
                    # So sánh value (cả string và number)
                    if radio_value == str(value) or str(radio_value) == str(value):
                        # Click vào radio
                        try:
                            radio.click()
                        except:
                            # Thử click vào label
                            try:
                                label = radio.find_element(By.XPATH, './ancestor::label')
                                label.click()
                            except:
                                # Thử click bằng JavaScript
                                self.driver.execute_script("arguments[0].click();", radio)
                        
                        time.sleep(delay)
                        print(f"  ✓ Đã chọn scale {entry_id}: {value}")
                        return True
                except Exception as e:
                    print(f"  Debug: Lỗi khi xử lý scale radio: {e}")
                    continue
            
            print(f"  ✗ Không tìm thấy scale value '{value}' cho {entry_id}")
            if available_values:
                print(f"     Các values có sẵn: {available_values}")
            return False
        except Exception as e:
            print(f"  ✗ Lỗi khi chọn scale {entry_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_and_click_next(self) -> bool:
        """Tìm và click nút Next, trả về True nếu tìm thấy và click được"""
        try:
            # Thử nhiều cách tìm nút Next
            next_selectors_xpath = [
                '//span[contains(text(), "Next")]',
                '//span[contains(text(), "Tiếp")]',
                '//div[@role="button" and contains(., "Next")]',
                '//div[@role="button" and contains(., "Tiếp")]',
                '//button[contains(., "Next")]',
                '//button[contains(., "Tiếp")]',
            ]
            
            next_button = None
            
            # Thử tìm bằng XPath
            for selector in next_selectors_xpath:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            next_button = btn
                            break
                    if next_button:
                        break
                except:
                    continue
            
            # Nếu không tìm thấy, thử tìm bằng text trong tất cả buttons
            if not next_button:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="button"], button')
                    for btn in buttons:
                        text = btn.text.strip().lower()
                        if ('next' in text or 'tiếp' in text) and btn.is_displayed() and btn.is_enabled():
                            # Kiểm tra không phải là nút Back hoặc Clear
                            if 'back' not in text and 'clear' not in text and 'quay' not in text:
                                next_button = btn
                                break
                except:
                    pass
            
            if next_button:
                # Scroll đến nút
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                
                # Click nút Next
                next_button.click()
                print("  ✓ Đã click Next")
                time.sleep(2)  # Đợi trang mới load
                return True
            else:
                return False
        except Exception as e:
            print(f"  ✗ Lỗi khi tìm/click Next: {e}")
            return False
    
    def _wait_for_page_load(self, timeout: int = 5):
        """Đợi trang load xong và form render"""
        try:
            # Đợi document ready
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Đợi form render - tìm ít nhất 1 question container
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'div[jsmodel="CP1oW"]')) > 0
            )
            
            time.sleep(1)  # Đợi thêm một chút để form render hoàn toàn
        except TimeoutException:
            # Nếu không tìm thấy containers, đợi thêm
            time.sleep(2)
        except:
            time.sleep(2)  # Fallback: đợi cố định 2 giây
    
    def _get_visible_fields_on_page(self) -> Dict[str, Dict]:
        """
        Lấy danh sách entry IDs và thông tin fields hiển thị trên trang hiện tại
        Bằng cách parse HTML để tìm các questions
        Returns: Dict {entry_id: {'type': 'radio', 'options': [...]}}
        """
        visible_fields = {}
        try:
            # Tìm tất cả các question containers
            # Google Forms dùng div[jsmodel="CP1oW"] cho mỗi question
            question_containers = self.driver.find_elements(By.CSS_SELECTOR, 'div[jsmodel="CP1oW"]')
            
            print(f"  Debug: Tìm thấy {len(question_containers)} question containers")
            
            for container in question_containers:
                try:
                    # Lấy data-params để parse entry_id và options
                    data_params = container.get_attribute('data-params')
                    if not data_params:
                        continue
                    
                    # Parse entry_id từ data-params
                    # Format: %.@.[..., type_code, [entry_id, [[option1, ...], ...]], ...]
                    # data-params có thể bắt đầu bằng "%.@." (Google's special format)
                    import json
                    import re
                    
                    try:
                        # Loại bỏ "%.@." nếu có
                        clean_params = data_params
                        if clean_params.startswith('%.@.'):
                            clean_params = clean_params[4:]  # Bỏ "%.@."
                        
                        # Thử parse JSON
                        params = json.loads(clean_params)
                        
                        if isinstance(params, list) and len(params) >= 4:
                            # params[2] = type_code (2 = radio, 4 = checkbox, 5 = linear_scale)
                            type_code = params[2] if len(params) > 2 else 2
                            if type_code == 2:
                                field_type = 'radio'
                            elif type_code == 4:
                                field_type = 'checkbox'
                            elif type_code == 5:
                                field_type = 'linear_scale'
                            else:
                                field_type = 'text'
                            
                            # params[3] = [entry_id, [[option1, ...], ...], ...]
                            entry_data = params[3] if len(params) > 3 else None
                            
                            if isinstance(entry_data, list) and len(entry_data) > 0:
                                entry_info = entry_data[0]
                                if isinstance(entry_info, list) and len(entry_info) > 0:
                                    entry_id_num = entry_info[0]
                                    entry_id = f'entry.{entry_id_num}'
                                    
                                    # Lấy options
                                    options = []
                                    if len(entry_info) > 1 and isinstance(entry_info[1], list):
                                        for opt in entry_info[1]:
                                            if isinstance(opt, list) and len(opt) > 0:
                                                opt_text = opt[0]
                                                if opt_text:
                                                    options.append(str(opt_text))
                                    
                                    visible_fields[entry_id] = {
                                        'type': field_type,
                                        'options': options,
                                        'container': container
                                    }
                                    print(f"  Debug: Tìm thấy field {entry_id} (type: {field_type}, {len(options)} options)")
                    except (json.JSONDecodeError, ValueError) as e:
                        # Nếu không parse được JSON, thử parse bằng regex
                        try:
                            # Tìm entry_id trong data-params bằng regex
                            # Format: [[entry_id,[[option1,...]]]
                            entry_match = re.search(r'\[\[(\d+),\[\[', data_params)
                            if entry_match:
                                entry_id_num = entry_match.group(1)
                                entry_id = f'entry.{entry_id_num}'
                                
                                # Tìm type_code từ data-params
                                # Format: [..., type_code, [entry_id, [[option1, ...], ...]], ...]
                                # Thử nhiều pattern để tìm type_code
                                type_code = 2  # Default
                                
                                # Pattern 1: Tìm số trước [[entry_id
                                type_match = re.search(r',(\d+),\[\[', data_params)
                                if type_match:
                                    type_code = int(type_match.group(1))
                                else:
                                    # Pattern 2: Tìm trong format [id,"text",null,type_code
                                    type_match2 = re.search(r'\[(\d+),"[^"]*",null,(\d+)', data_params)
                                    if type_match2:
                                        type_code = int(type_match2.group(2))
                                
                                # Xác định field type
                                if type_code == 2:
                                    field_type = 'radio'
                                elif type_code == 4:
                                    field_type = 'checkbox'
                                elif type_code == 5:
                                    field_type = 'linear_scale'
                                else:
                                    field_type = 'text'
                                
                                print(f"  Debug: Parse type_code = {type_code}, field_type = {field_type} cho {entry_id}")
                                
                                # Tìm options bằng regex
                                options = []
                                option_matches = re.findall(r'\["([^"]+)"', data_params)
                                for opt in option_matches:
                                    if opt and opt not in options:
                                        options.append(opt)
                                
                                visible_fields[entry_id] = {
                                    'type': field_type,
                                    'options': options,
                                    'container': container
                                }
                                print(f"  Debug: Tìm thấy field {entry_id} bằng regex (type: {field_type}, {len(options)} options)")
                        except Exception as regex_error:
                            print(f"  Debug: Lỗi parse bằng regex: {regex_error}")
                    except Exception as e:
                        # Nếu không parse được JSON, thử cách khác
                        # Tìm entry_id từ hidden input trong container
                        try:
                            hidden_input = container.find_element(By.CSS_SELECTOR, 'input[type="hidden"][name^="entry."]:not([name*="_sentinel"])')
                            entry_id = hidden_input.get_attribute('name')
                            if entry_id and entry_id not in visible_fields:
                                # Tìm radio/checkbox trong container
                                radios = container.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                                checkboxes = container.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                                
                                field_type = 'radio' if radios else 'checkbox' if checkboxes else 'text'
                                options = []
                                
                                for elem in (radios if radios else checkboxes):
                                    try:
                                        option_text = elem.get_attribute('data-value') or elem.get_attribute('aria-label')
                                        if option_text and option_text not in options:
                                            options.append(option_text)
                                    except:
                                        pass
                                
                                if entry_id:
                                    visible_fields[entry_id] = {
                                        'type': field_type,
                                        'options': options,
                                        'container': container
                                    }
                        except:
                            pass
                    except Exception as e:
                        print(f"  Debug: Lỗi parse data-params: {e}")
                        continue
                except Exception as e:
                    print(f"  Debug: Lỗi xử lý container: {e}")
                    continue
            
            # Nếu vẫn không tìm được, thử tìm bằng hidden inputs (bỏ qua sentinel)
            if not visible_fields:
                hidden_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="hidden"][name^="entry."]:not([name*="_sentinel"])')
                for inp in hidden_inputs:
                    try:
                        entry_id = inp.get_attribute('name')
                        if entry_id and entry_id not in visible_fields and '_sentinel' not in entry_id:
                            # Tìm radio/checkbox tương ứng trong cùng container
                            try:
                                container = inp.find_element(By.XPATH, './ancestor::div[jsmodel="CP1oW"]')
                            except:
                                container = None
                            
                            entry_num = entry_id.replace('entry.', '')
                            radios = self.driver.find_elements(By.CSS_SELECTOR, f'div[role="radio"][data-value*="{entry_num}"], div[jsmodel="CP1oW"][data-params*="{entry_num}"] div[role="radio"]')
                            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, f'div[role="checkbox"][data-value*="{entry_num}"], div[jsmodel="CP1oW"][data-params*="{entry_num}"] div[role="checkbox"]')
                            
                            if container:
                                radios = container.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                                checkboxes = container.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                            
                            if radios or checkboxes:
                                field_type = 'radio' if radios else 'checkbox'
                                options = []
                                
                                for elem in (radios if radios else checkboxes):
                                    try:
                                        option_text = elem.get_attribute('data-value') or elem.get_attribute('aria-label')
                                        if option_text and option_text not in options:
                                            options.append(option_text)
                                    except:
                                        pass
                                
                                visible_fields[entry_id] = {
                                    'type': field_type,
                                    'options': options
                                }
                    except:
                        continue
                        
        except Exception as e:
            print(f"  Debug: Lỗi khi lấy visible fields: {e}")
            import traceback
            traceback.print_exc()
        
        return visible_fields
    
    def _fill_fields_on_current_page(self, data: Dict, field_types: Dict, filled_entry_ids: set, delay: float) -> int:
        """Điền các fields có thể thấy trên trang hiện tại, trả về số lượng fields đã điền"""
        success_count = 0
        
        # Đợi trang load xong
        self._wait_for_page_load()
        
        # Lấy danh sách fields hiển thị trên trang này
        visible_fields = self._get_visible_fields_on_page()
        print(f"  Debug: Tìm thấy {len(visible_fields)} fields hiển thị trên trang này")
        if visible_fields:
            print(f"  Debug: Entry IDs: {list(visible_fields)[:5]}...")
        
        # Chỉ điền các fields có trên trang này
        fields_to_fill = []
        for entry_id, value in data.items():
            # Bỏ qua nếu đã điền
            if entry_id in filled_entry_ids:
                continue
            
            # Chỉ điền nếu field có trên trang này
            if entry_id in visible_fields:
                fields_to_fill.append((entry_id, value, visible_fields[entry_id]))
        
        print(f"  Debug: Sẽ điền {len(fields_to_fill)} fields trên trang này")
        
        # Điền từng field
        for field_info in fields_to_fill:
            if len(field_info) == 3:
                entry_id, value, field_data = field_info
                field_type = field_data.get('type', field_types.get(entry_id, 'text'))
            else:
                entry_id, value = field_info
                field_type = field_types.get(entry_id, 'text')
            
            # Scroll đến field (tìm container hoặc element)
            try:
                # Tìm container của field này
                entry_num = entry_id.replace('entry.', '')
                container = self.driver.find_element(By.CSS_SELECTOR, f'div[jsmodel="CP1oW"][data-params*="{entry_num}"]')
                if container:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
                    time.sleep(0.5)
            except:
                # Fallback: scroll đến đầu trang
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.3)
            
            # Điền theo loại field
            filled = False
            if field_type == 'radio':
                if self._fill_radio(entry_id, str(value), delay):
                    filled = True
            elif field_type == 'checkbox':
                # Xử lý checkbox - đảm bảo values là list
                if isinstance(value, list):
                    checkbox_values = [str(v) for v in value]
                elif isinstance(value, str):
                    # Nếu là string, thử parse nếu có dạng list
                    import ast
                    try:
                        # Thử parse string như list
                        parsed = ast.literal_eval(value)
                        if isinstance(parsed, list):
                            checkbox_values = [str(v) for v in parsed]
                        else:
                            checkbox_values = [str(value)]
                    except:
                        checkbox_values = [str(value)]
                else:
                    checkbox_values = [str(value)]
                
                print(f"  Debug: Checkbox values để chọn: {checkbox_values}")
                if self._fill_checkbox(entry_id, checkbox_values, delay):
                    filled = True
            elif field_type == 'dropdown':
                if self._fill_dropdown(entry_id, str(value), delay):
                    filled = True
            elif field_type == 'linear_scale':
                if self._fill_linear_scale(entry_id, str(value), delay):
                    filled = True
            else:
                # Text, textarea, etc.
                if self._fill_text_field(entry_id, str(value), delay):
                    filled = True
            
            if filled:
                success_count += 1
                filled_entry_ids.add(entry_id)
            else:
                print(f"  Debug: Không điền được {entry_id}")
            
            time.sleep(delay)
        
        return success_count
    
    def submit_form(self, data: Dict, questions: List[Dict] = None, delay: float = 1.0) -> bool:
        """
        Điền và submit form bằng Selenium (hỗ trợ form nhiều trang)
        
        Args:
            data: Dictionary chứa entry IDs và giá trị
            questions: List các câu hỏi (để biết loại field)
            delay: Delay giữa các thao tác (giây)
        """
        try:
            print(f"Đang mở form: {self.form_url}")
            self.driver.get(self.form_url)
            time.sleep(2)  # Đợi form load
            
            # Tạo mapping entry_id -> field_type từ questions
            field_types = {}
            if questions:
                for q in questions:
                    field_types[q['entry_id']] = q.get('type', 'text')
            
            total_count = len(data)
            filled_entry_ids = set()
            total_filled = 0
            page_num = 1
            
            print(f"\nĐang điền {total_count} fields (form nhiều trang)...")
            
            # Điền form theo từng trang
            max_pages = 20  # Giới hạn số trang để tránh vòng lặp vô hạn
            while len(filled_entry_ids) < total_count and page_num <= max_pages:
                print(f"\n--- Trang {page_num} ---")
                
                # Đợi trang load xong trước khi điền
                self._wait_for_page_load()
                
                # Điền các fields trên trang hiện tại
                page_filled = self._fill_fields_on_current_page(data, field_types, filled_entry_ids, delay)
                total_filled += page_filled
                
                print(f"Đã điền {page_filled} fields trên trang này (Tổng: {total_filled}/{total_count})")
                
                # Kiểm tra xem còn fields nào chưa điền không
                remaining = total_count - len(filled_entry_ids)
                if remaining == 0:
                    print("  ✓ Đã điền hết tất cả fields")
                    break
                
                # Tìm nút Next
                print("Đang tìm nút Next...")
                has_next = self._find_and_click_next()
                
                if not has_next:
                    # Không còn Next, đã đến trang cuối
                    print("  ✓ Không còn nút Next, đã đến trang cuối")
                    break
                
                page_num += 1
                # Đợi trang mới load hoàn toàn
                time.sleep(2)
            
            print(f"\nĐã điền tổng cộng {total_filled}/{total_count} fields")
            
            # Sau khi điền hết fields, có thể cần click Next một lần nữa để đến trang Submit
            print("\nKiểm tra xem còn nút Next không...")
            has_next = self._find_and_click_next()
            if has_next:
                print("  ✓ Đã click Next để đến trang Submit")
                time.sleep(2)  # Đợi trang Submit load
            
            # Tìm và click nút Submit
            print("\nĐang tìm nút Submit...")
            time.sleep(1)
            
            # Thử nhiều cách tìm nút Submit
            submit_button = None
            submit_selectors_xpath = [
                '//span[contains(text(), "Gửi")]',
                '//span[contains(text(), "Submit")]',
                '//div[@role="button" and contains(., "Gửi")]',
                '//div[@role="button" and contains(., "Submit")]',
                '//button[contains(., "Gửi")]',
                '//button[contains(., "Submit")]',
            ]
            
            # Thử tìm bằng XPath trước
            for selector in submit_selectors_xpath:
                try:
                    submit_button = self.driver.find_element(By.XPATH, selector)
                    if submit_button and submit_button.is_displayed():
                        break
                except:
                    continue
            
            # Nếu không tìm thấy, thử tìm bằng CSS selector
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                except:
                    pass
            
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
                except:
                    pass
            
            # Nếu không tìm thấy bằng selector, thử tìm bằng text trong tất cả buttons
            if not submit_button:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="button"], button')
                    for btn in buttons:
                        text = btn.text.strip().lower()
                        # Tìm nút có text "Gửi" hoặc "Submit" nhưng không phải "Next", "Back", "Clear"
                        if ('gửi' in text or 'submit' in text) and 'next' not in text and 'tiếp' not in text and 'back' not in text and 'quay' not in text and 'clear' not in text and 'xóa' not in text:
                            if btn.is_displayed() and btn.is_enabled():
                                submit_button = btn
                                print(f"  Debug: Tìm thấy nút Submit bằng text: '{btn.text}'")
                                break
                except:
                    pass
            
            # Nếu vẫn không tìm thấy, thử tìm bằng jsname (Google Forms dùng jsname cho buttons)
            if not submit_button:
                try:
                    # Tìm button với jsname thường dùng cho Submit
                    submit_selectors_jsname = [
                        'div[jsname="M2UYVd"]',  # Submit button jsname
                        'div[role="button"][jsname="M2UYVd"]',
                    ]
                    for selector in submit_selectors_jsname:
                        try:
                            btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if btn.is_displayed() and btn.is_enabled():
                                submit_button = btn
                                print(f"  Debug: Tìm thấy nút Submit bằng jsname")
                                break
                        except:
                            continue
                except:
                    pass
            
            if submit_button:
                print("  ✓ Tìm thấy nút Submit")
                # Scroll đến nút
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(0.5)
                
                # Click nút Submit
                submit_button.click()
                print("  ✓ Đã click Submit")
                time.sleep(3)  # Đợi submit hoàn tất
                
                # Kiểm tra xem có thông báo thành công không
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                success_indicators = [
                    'thankyou' in current_url.lower(),
                    'formresponse' in current_url.lower(),
                    'cảm ơn' in page_source,
                    'thank you' in page_source,
                    'your response has been recorded' in page_source,
                    'phản hồi của bạn đã được ghi lại' in page_source,
                ]
                
                if any(success_indicators):
                    print("\n✓ Submit thành công!")
                    return True
                else:
                    print("\n⚠ Submit có thể thành công, nhưng không chắc chắn")
                    print(f"  URL hiện tại: {current_url[:100]}")
                    return True  # Vẫn return True vì đã click submit
            else:
                print("  ✗ Không tìm thấy nút Submit")
                return False
                
        except Exception as e:
            print(f"\n✗ Lỗi khi submit form: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def auto_fill_and_submit(self, num_submissions: int = 1, custom_data: Optional[Dict] = None, 
                            questions: List[Dict] = None, delay: float = 2.0, 
                            field_config: Optional[Dict] = None):
        """
        Tự động điền và submit form nhiều lần
        
        Args:
            num_submissions: Số lần submit
            custom_data: Dữ liệu tùy chỉnh (nếu None sẽ dùng random - cần import từ google_form_auto_fill)
            questions: List các câu hỏi
            delay: Thời gian delay giữa các lần submit
            field_config: Config cho generate_random_data
        """
        from google_form_auto_fill import GoogleFormAutoFill
        
        # Lấy fields nếu chưa có questions
        if not questions:
            form_filler = GoogleFormAutoFill(self.form_url)
            questions = form_filler.get_questions()
            fields = form_filler.get_form_fields()
        else:
            fields = {q['entry_id']: {'type': q.get('type', 'text'), 'choices': q.get('choices')} 
                     for q in questions}
        
        print(f"Tìm thấy {len(questions)} câu hỏi trong form")
        print("\n" + "="*50)
        
        success_count = 0
        
        for i in range(num_submissions):
            print(f"\n[{i+1}/{num_submissions}] Đang submit...")
            
            # Tạo dữ liệu
            if custom_data:
                data = custom_data.copy()
            else:
                form_filler = GoogleFormAutoFill(self.form_url)
                data = form_filler.generate_random_data(fields, field_config=field_config)
            
            # In ra một số dữ liệu để kiểm tra
            print(f"Dữ liệu mẫu: {list(data.items())[:3]}...")
            
            # Submit
            if self.submit_form(data, questions=questions, delay=0.5):
                success_count += 1
            
            # Delay giữa các lần submit
            if i < num_submissions - 1:
                time.sleep(delay)
        
        print("\n" + "="*50)
        print(f"Hoàn thành! Đã submit thành công {success_count}/{num_submissions} lần")
    
    def close(self):
        """Đóng browser"""
        if self.driver:
            self.driver.quit()
            print("Đã đóng browser")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

