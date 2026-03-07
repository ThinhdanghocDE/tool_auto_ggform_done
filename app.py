"""
Streamlit Web App cho Google Form Auto Fill
Giao diện đơn giản, dễ sử dụng cho người no-code
"""

import streamlit as st
import json
import time
from google_form_auto_fill import GoogleFormAutoFill
from typing import Dict, Optional

# Cấu hình trang
st.set_page_config(
    page_title="Google Form Auto Fill",
    layout="wide"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Google Form Auto Fill Tool</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Cài đặt")
    
    # Load config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {
            "form_settings": {
                "num_submissions": 10,
                "delay_between_submissions": 2.0
            }
        }
    
    num_submissions = st.number_input(
        "Số lượng submit",
        min_value=1,
        max_value=1000,
        value=config.get("form_settings", {}).get("num_submissions", 10),
        help="Số lượng form sẽ được submit tự động"
    )
    
    delay = st.number_input(
        "Delay giữa các lần submit (giây)",
        min_value=0.5,
        max_value=60.0,
        value=config.get("form_settings", {}).get("delay_between_submissions", 2.0),
        step=0.5,
        help="Thời gian chờ giữa mỗi lần submit"
    )

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trang chủ", "Danh sách câu hỏi", "Cấu hình dữ liệu", "Chạy Submit", "Kết quả"])

# Tab 1: Trang chủ
with tab1:
    st.header("Hướng dẫn sử dụng")
    
    st.markdown("""
    ### Bước 1: Nhập URL Form
    - Vào tab **"Danh sách câu hỏi"**
    - Nhập URL Google Form của bạn
    - Nhấn "Lấy danh sách câu hỏi"
    
    ### Bước 2: Xem và tùy chỉnh
    - Xem danh sách tất cả câu hỏi trong form
    - Tool sẽ tự động tạo dữ liệu phù hợp cho từng câu hỏi
    
    ### Bước 3: Chạy Submit
    - Vào tab **"Chạy Submit"**
    - Điều chỉnh số lượng submit và delay
    - Nhấn "Bắt đầu Submit"
    
    ### Bước 4: Xem kết quả
    - Vào tab **"Kết quả"** để xem thống kê
    """)
    
    st.info("**Lưu ý**: Tool sẽ tự động tạo dữ liệu thực tế dựa trên các lựa chọn có sẵn trong form.")

# Tab 2: Danh sách câu hỏi
with tab2:
    st.header("Danh sách câu hỏi")
    
    form_url = st.text_input(
        "URL Google Form",
        placeholder="https://docs.google.com/forms/d/e/.../viewform",
        help="Dán URL Google Form của bạn vào đây"
    )
    
    if st.button("Lấy danh sách câu hỏi", type="primary"):
        if not form_url:
            st.error("Vui lòng nhập URL form!")
        else:
            with st.spinner("Đang lấy danh sách câu hỏi..."):
                try:
                    form_filler = GoogleFormAutoFill(form_url)
                    questions = form_filler.get_questions()
                    
                    if questions:
                        st.success(f"Tìm thấy {len(questions)} câu hỏi!")
                        
                        # Lưu vào session state
                        st.session_state['form_filler'] = form_filler
                        st.session_state['questions'] = questions
                        st.session_state['form_url'] = form_url
                        
                        # Hiển thị danh sách
                        st.subheader("Danh sách câu hỏi:")
                        for idx, q in enumerate(questions, 1):
                            with st.expander(f"{idx}. {q['question']}"):
                                st.write(f"**Entry ID**: `{q['entry_id']}`")
                                st.write(f"**Loại**: {q['type']}")
                                if q.get('choices'):
                                    st.write(f"**Lựa chọn**: {', '.join(q['choices'])}")
                                if q.get('scale_min') and q.get('scale_max'):
                                    st.write(f"**Scale**: {q['scale_min']} - {q['scale_max']}")
                                st.write(f"**Bắt buộc**: {'Có' if q.get('required') else 'Không'}")
                    else:
                        st.error("Không tìm thấy câu hỏi nào. Vui lòng kiểm tra lại URL.")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
    
    # Preview dữ liệu sẽ submit
    if 'form_filler' in st.session_state and 'questions' in st.session_state:
        st.divider()
        st.subheader("Preview dữ liệu sẽ submit")
        
        if st.button("Tạo dữ liệu mẫu"):
            try:
                fields = st.session_state['form_filler'].get_form_fields()
                field_config = st.session_state.get('field_config', {'fields': {}})
                sample_data = st.session_state['form_filler'].generate_random_data(fields, field_config=field_config)
                
                st.session_state['sample_data'] = sample_data
                
                st.success("Đã tạo dữ liệu mẫu!")
                
                # Hiển thị preview
                questions = st.session_state['questions']
                for entry_id, value in sample_data.items():
                    q_info = next((q for q in questions if q['entry_id'] == entry_id), None)
                    if q_info:
                        if isinstance(value, list):
                            st.write(f"**{q_info['question']}**: {', '.join(map(str, value))}")
                        else:
                            st.write(f"**{q_info['question']}**: {value}")
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")

# Tab 3: Cấu hình dữ liệu
with tab3:
    st.header("Cấu hình dữ liệu")
    
    if 'form_filler' not in st.session_state or 'questions' not in st.session_state:
        st.warning("Vui lòng lấy danh sách câu hỏi trước (tab 'Danh sách câu hỏi')")
    else:
        st.info("Chọn **Fixed** để cố định giá trị, **Random** để ngẫu nhiên. Với Random, bạn có thể chọn random từ tất cả options hoặc chỉ một số options cụ thể.")
        
        # Khởi tạo field_config trong session state nếu chưa có
        if 'field_config' not in st.session_state:
            st.session_state['field_config'] = {'fields': {}}
        
        questions = st.session_state['questions']
        field_config = st.session_state['field_config']['fields']
        
        # Hiển thị form cấu hình cho từng câu hỏi
        for idx, q in enumerate(questions):
            entry_id = q['entry_id']
            question_text = q['question']
            field_type = q['type']
            choices = q.get('choices', [])
            
            with st.expander(f"{idx + 1}. {question_text[:80]}..." if len(question_text) > 80 else f"{idx + 1}. {question_text}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Chọn mode
                    current_mode = field_config.get(entry_id, {}).get('mode', 'random')
                    mode = st.radio(
                        "Chế độ",
                        ["random", "fixed"],
                        index=0 if current_mode == 'random' else 1,
                        key=f"mode_{entry_id}",
                        horizontal=True
                    )
                
                with col2:
                    if mode == 'fixed':
                        # Giá trị cố định - dùng radio/checkbox thay vì selectbox
                        if field_type in ['radio', 'dropdown']:
                            if choices:
                                current_value = field_config.get(entry_id, {}).get('value', choices[0])
                                # Dùng radio buttons thay vì selectbox
                                fixed_value = st.radio(
                                    "Giá trị cố định",
                                    choices,
                                    index=choices.index(current_value) if current_value in choices else 0,
                                    key=f"fixed_{entry_id}"
                                )
                                field_config[entry_id] = {'mode': 'fixed', 'value': fixed_value}
                            else:
                                fixed_value = st.text_input("Giá trị cố định", key=f"fixed_{entry_id}")
                                if fixed_value:
                                    field_config[entry_id] = {'mode': 'fixed', 'value': fixed_value}
                        elif field_type == 'checkbox':
                            if choices:
                                current_values = field_config.get(entry_id, {}).get('value', [])
                                if not isinstance(current_values, list):
                                    current_values = [current_values] if current_values else []
                                
                                st.write("**Giá trị cố định (chọn nhiều):**")
                                # Dùng checkbox thay vì multiselect để tránh lag
                                # Hiển thị theo cột để dễ nhìn
                                num_cols = min(3, len(choices))
                                cols = st.columns(num_cols)
                                
                                # Khởi tạo state cho checkbox nếu chưa có
                                checkbox_key = f"checkbox_state_{entry_id}"
                                if checkbox_key not in st.session_state:
                                    st.session_state[checkbox_key] = {choice: choice in current_values for choice in choices}
                                
                                # Hiển thị checkbox và cập nhật state
                                for idx, choice in enumerate(choices):
                                    col_idx = idx % num_cols
                                    with cols[col_idx]:
                                        checked = st.checkbox(
                                            choice,
                                            value=st.session_state[checkbox_key].get(choice, False),
                                            key=f"fixed_check_{entry_id}_{idx}"
                                        )
                                        st.session_state[checkbox_key][choice] = checked
                                
                                # Lấy giá trị đã chọn từ state
                                fixed_values = [choice for choice, checked in st.session_state[checkbox_key].items() if checked]
                                
                                # Lưu giá trị đã chọn
                                if fixed_values:
                                    field_config[entry_id] = {'mode': 'fixed', 'value': fixed_values}
                                elif entry_id in field_config:
                                    # Xóa config nếu không chọn gì
                                    del field_config[entry_id]
                        elif field_type == 'linear_scale':
                            scale_min = q.get('scale_min', 1)
                            scale_max = q.get('scale_max', 5)
                            scale_options = [str(i) for i in range(scale_min, scale_max + 1)]
                            current_value = field_config.get(entry_id, {}).get('value', str(scale_min))
                            # Dùng radio buttons thay vì selectbox
                            fixed_value = st.radio(
                                "Giá trị cố định",
                                scale_options,
                                index=int(current_value) - scale_min if current_value.isdigit() and scale_min <= int(current_value) <= scale_max else 0,
                                key=f"fixed_{entry_id}",
                                horizontal=True
                            )
                            field_config[entry_id] = {'mode': 'fixed', 'value': fixed_value}
                        else:
                            current_value = field_config.get(entry_id, {}).get('value', '')
                            fixed_value = st.text_input("Giá trị cố định", value=current_value, key=f"fixed_{entry_id}")
                            if fixed_value:
                                field_config[entry_id] = {'mode': 'fixed', 'value': fixed_value}
                    
                    else:  # mode == 'random'
                        # Random từ danh sách chỉ định - dùng checkbox thay vì multiselect
                        if choices:
                            current_random_from = field_config.get(entry_id, {}).get('random_from', [])
                            if not isinstance(current_random_from, list):
                                current_random_from = []
                            
                            st.write("**Random từ (chọn các options sẽ random, để trống = random từ tất cả):**")
                            # Dùng checkbox thay vì multiselect để tránh lag
                            # Hiển thị theo cột để dễ nhìn
                            num_cols = min(3, len(choices))
                            cols = st.columns(num_cols)
                            
                            # Khởi tạo state cho checkbox nếu chưa có
                            checkbox_key = f"random_checkbox_state_{entry_id}"
                            if checkbox_key not in st.session_state:
                                st.session_state[checkbox_key] = {choice: choice in current_random_from for choice in choices}
                            
                            # Hiển thị checkbox và cập nhật state
                            for idx, choice in enumerate(choices):
                                col_idx = idx % num_cols
                                with cols[col_idx]:
                                    checked = st.checkbox(
                                        choice,
                                        value=st.session_state[checkbox_key].get(choice, False),
                                        key=f"random_check_{entry_id}_{idx}"
                                    )
                                    st.session_state[checkbox_key][choice] = checked
                            
                            # Lấy giá trị đã chọn từ state
                            random_from = [choice for choice, checked in st.session_state[checkbox_key].items() if checked]
                            
                            if random_from:
                                field_config[entry_id] = {'mode': 'random', 'random_from': random_from}
                            else:
                                # Xóa config để random từ tất cả
                                if entry_id in field_config:
                                    del field_config[entry_id]
                        elif field_type == 'linear_scale':
                            # Linear scale: chọn từ scale range
                            scale_min = q.get('scale_min', 1)
                            scale_max = q.get('scale_max', 5)
                            scale_options = [str(i) for i in range(scale_min, scale_max + 1)]
                            
                            current_random_from = field_config.get(entry_id, {}).get('random_from', [])
                            if not isinstance(current_random_from, list):
                                current_random_from = []
                            
                            st.write("**Random từ (chọn các giá trị sẽ random, để trống = random từ tất cả):**")
                            # Dùng checkbox thay vì multiselect để tránh lag
                            # Hiển thị theo cột để dễ nhìn
                            num_cols = min(5, len(scale_options))
                            cols = st.columns(num_cols)
                            
                            # Khởi tạo state cho checkbox nếu chưa có
                            checkbox_key = f"random_scale_state_{entry_id}"
                            if checkbox_key not in st.session_state:
                                st.session_state[checkbox_key] = {scale_val: scale_val in current_random_from for scale_val in scale_options}
                            
                            # Hiển thị checkbox và cập nhật state
                            for idx, scale_val in enumerate(scale_options):
                                col_idx = idx % num_cols
                                with cols[col_idx]:
                                    checked = st.checkbox(
                                        scale_val,
                                        value=st.session_state[checkbox_key].get(scale_val, False),
                                        key=f"random_scale_{entry_id}_{idx}"
                                    )
                                    st.session_state[checkbox_key][scale_val] = checked
                            
                            # Lấy giá trị đã chọn từ state
                            random_from = [scale_val for scale_val, checked in st.session_state[checkbox_key].items() if checked]
                            
                            if random_from:
                                field_config[entry_id] = {'mode': 'random', 'random_from': random_from}
                            else:
                                # Xóa config để random từ tất cả
                                if entry_id in field_config:
                                    del field_config[entry_id]
                        else:
                            st.info("Không có options để chọn. Sẽ random từ tất cả giá trị có thể.")
                            if entry_id in field_config:
                                del field_config[entry_id]
        
        # Lưu config
        st.session_state['field_config'] = {'fields': field_config}
        
        # Nút lưu và preview
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Lưu cấu hình", type="primary"):
                try:
                    # Lưu vào config.json
                    import json
                    with open('config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    config['field_config']['fields'] = field_config
                    with open('config.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    st.success("Đã lưu cấu hình!")
                except Exception as e:
                    st.error(f"Lỗi khi lưu: {e}")
        
        with col2:
            preview_count = st.number_input("Số lần preview", min_value=1, max_value=10, value=3, key="preview_count")
            
            if st.button("Preview dữ liệu"):
                try:
                    fields = st.session_state['form_filler'].get_form_fields()
                    
                    st.subheader(f"Preview {preview_count} bộ dữ liệu với cấu hình hiện tại:")
                    
                    # Tạo nhiều bộ dữ liệu để xem sự khác biệt
                    for preview_idx in range(preview_count):
                        sample_data = st.session_state['form_filler'].generate_random_data(
                            fields, 
                            field_config=st.session_state['field_config']
                        )
                        
                        with st.expander(f"Preview #{preview_idx + 1}"):
                            # Chỉ hiển thị các câu có config để dễ thấy sự khác biệt
                            config_fields = st.session_state['field_config'].get('fields', {})
                            for entry_id, value in sample_data.items():
                                if entry_id in config_fields:
                                    q_info = next((q for q in questions if q['entry_id'] == entry_id), None)
                                    if q_info:
                                        mode = config_fields[entry_id].get('mode', 'random')
                                        mode_badge = "Fixed" if mode == 'fixed' else "Random"
                                        if isinstance(value, list):
                                            st.write(f"{mode_badge} **{q_info['question']}**: {', '.join(map(str, value))}")
                                        else:
                                            st.write(f"{mode_badge} **{q_info['question']}**: {value}")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

# Tab 4: Chạy Submit
with tab4:
    st.header("Chạy Submit")
    
    if 'form_filler' not in st.session_state:
        st.warning("Vui lòng lấy danh sách câu hỏi trước (tab 'Danh sách câu hỏi')")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Số lượng submit", num_submissions)
        with col2:
            st.metric("Delay", f"{delay}s")
        
        if st.button("Bắt đầu Submit", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            
            for i in range(num_submissions):
                try:
                    # Tạo dữ liệu mới cho mỗi lần submit
                    fields = st.session_state['form_filler'].get_form_fields()
                    field_config = st.session_state.get('field_config', {'fields': {}})
                    data = st.session_state['form_filler'].generate_random_data(fields, field_config=field_config)
                    
                    # Submit
                    success = st.session_state['form_filler'].submit_form(data, delay=delay)
                    
                    results.append({
                        'submission': i + 1,
                        'success': success,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Update progress
                    progress = (i + 1) / num_submissions
                    progress_bar.progress(progress)
                    status_text.text(f"Đã submit: {i + 1}/{num_submissions} - {'Thành công' if success else 'Thất bại'}")
                    
                except Exception as e:
                    results.append({
                        'submission': i + 1,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Lưu kết quả
            st.session_state['submit_results'] = results
            
            # Hiển thị kết quả
            success_count = sum(1 for r in results if r.get('success'))
            st.success(f"Hoàn thành! Thành công: {success_count}/{num_submissions}")

# Tab 5: Kết quả
with tab5:
    st.header("Kết quả Submit")
    
    if 'submit_results' not in st.session_state:
        st.info("Chưa có kết quả. Hãy chạy submit ở tab 'Chạy Submit'.")
    else:
        results = st.session_state['submit_results']
        
        # Thống kê
        success_count = sum(1 for r in results if r.get('success'))
        fail_count = len(results) - success_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng số", len(results))
        with col2:
            st.metric("Thành công", success_count, delta=f"{success_count/len(results)*100:.1f}%")
        with col3:
            st.metric("Thất bại", fail_count)
        
        # Chi tiết
        st.subheader("Chi tiết")
        for result in results:
            if result.get('success'):
                st.success(f"#{result['submission']} - {result['timestamp']} - Thành công")
            else:
                st.error(f"#{result['submission']} - {result['timestamp']} - Thất bại: {result.get('error', 'Unknown error')}")

