import json
import os

class FormGenerator:
    def __init__(self, activities, attributes):
        self.activities = activities
        self.attributes = attributes
        
    def generate_form_html(self, activity_name):
        """تولید فرم HTML برای یک فعالیت خاص"""
        
        fields = self._suggest_fields(activity_name)
        
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>فرم {activity_name}</title>
            <style>
                body {{ font-family: 'Vazir', sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; font-weight: bold; margin-bottom: 5px; color: #34495e; }}
                input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }}
                input:focus, select:focus, textarea:focus {{ border-color: #3498db; outline: none; }}
                .btn {{ background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
                .btn:hover {{ background: #2980b9; }}
                .sensitive {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 15px; }}
                .sensitive label {{ color: #856404; }}
                .ethical-note {{ background: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .ethical-note h4 {{ margin: 0 0 10px 0; color: #155724; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📋 فرم {activity_name}</h2>
                <div class="ethical-note">
                    <h4>⚖️ رعایت اصول اخلاقی</h4>
                    <p>🔹 فیلدهای حساس (با 🔒 مشخص شده‌اند) در خروجی نمایش داده نمی‌شوند</p>
                    <p>🔹 تمام تصمیم‌گیری‌ها با شفافیت کامل انجام می‌شود</p>
                </div>
        """
        
        for field in fields:
            field_type = field.get('type', 'text')
            field_name = field.get('name', '')
            field_label = field.get('label', field_name)
            is_sensitive = field.get('sensitive', False)
            
            sensitive_class = "sensitive" if is_sensitive else "form-group"
            sensitive_note = " (🔒 اطلاعات حساس)" if is_sensitive else ""
            
            html += f"""
                <div class="{sensitive_class}">
                    <label for="{field_name}">{field_label}{sensitive_note}</label>
            """
            
            if field_type == 'select':
                html += f'<select id="{field_name}" name="{field_name}">'
                for option in field.get('options', []):
                    html += f'<option value="{option}">{option}</option>'
                html += '</select>'
            elif field_type == 'textarea':
                html += f'<textarea id="{field_name}" name="{field_name}" rows="3"></textarea>'
            else:
                html += f'<input type="{field_type}" id="{field_name}" name="{field_name}" placeholder="لطفاً وارد کنید...">'
            
            html += '</div>'
        
        # افزودن بخش تصمیم‌گیری اخلاقی
        if any(k in activity_name for k in ['تأیید', 'رد', 'تصمیم', 'ارزیابی']):
            html += """
                <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; border-right: 4px solid #3498db; margin: 20px 0;">
                    <h4>📝 شفافیت در تصمیم‌گیری</h4>
                    <div class="form-group">
                        <label>توضیح دلیل تصمیم (برای شفافیت کامل):</label>
                        <textarea name="decision_explanation" rows="3" placeholder="لطفاً دلیل این تصمیم را به‌صورت شفاف توضیح دهید..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>🔄 درخواست بازبینی (قابلیت اعتراض):</label>
                        <input type="checkbox" name="appeal_request" value="yes"> درخواست بازبینی دارم
                    </div>
                </div>
            """
        
        if 'تأیید' in activity_name or 'رد' in activity_name:
            html += """
                <div style="background: #e6f3ff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #0066cc;">
                    <h4>🔄 درخواست بازبینی (Appeal)</h4>
                    <div class="form-group">
                        <label>آیا به این تصمیم اعتراض دارید؟</label>
                        <select name="appeal_request">
                            <option value="no">خیر</option>
                            <option value="yes">بله، درخواست بازبینی دارم</option>
                        </select>
                    </div>
                <div class="form-group" id="appeal_reason_group" style="display:none;">
                    <label>دلیل درخواست بازبینی:</label>
                    <textarea name="appeal_reason" rows="3" placeholder="لطفاً دلیل خود را به‌صورت دقیق بیان کنید..."></textarea>
                </div>
                <script>
                    document.querySelector('select[name="appeal_request"]').addEventListener('change', function() {
                        var group = document.getElementById('appeal_reason_group');
                        if (this.value === 'yes') {
                            group.style.display = 'block';
                        } else {
                            group.style.display = 'none';
                        }
                    });
                </script>
            </div>
        """
        
        html += """
                <button type="submit" class="btn">ثبت و ارسال</button>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _suggest_fields(self, activity_name):
        """پیشنهاد فیلدهای مناسب بر اساس نام فعالیت"""
        
        base_fields = [
            {'name': 'case_id', 'label': 'شماره پرونده', 'type': 'text'},
            {'name': 'applicant_name', 'label': 'نام متقاضی', 'type': 'text'},
            {'name': 'national_id', 'label': 'کد ملی', 'type': 'text', 'sensitive': True},
        ]
        
        activity_fields = {
            'ثبت درخواست': [
                {'name': 'request_type', 'label': 'نوع درخواست', 'type': 'select', 
                 'options': ['کمک مالی', 'وام تحصیلی', 'تخفیف شهریه']},
                {'name': 'amount', 'label': 'مبلغ درخواستی (تومان)', 'type': 'number'},
                {'name': 'description', 'label': 'توضیحات درخواست', 'type': 'textarea'},
            ],
            'بررسی مدارک': [
                {'name': 'documents_status', 'label': 'وضعیت مدارک', 'type': 'select',
                 'options': ['کامل', 'ناقص', 'نیاز به بررسی بیشتر']},
                {'name': 'documents_notes', 'label': 'یادداشت‌ها', 'type': 'textarea'},
            ],
            'ارزیابی نیاز مالی': [
                {'name': 'monthly_income', 'label': 'درآمد ماهانه (تومان)', 'type': 'number'},
                {'name': 'family_size', 'label': 'تعداد اعضای خانواده', 'type': 'number'},
                {'name': 'gpa', 'label': 'معدل', 'type': 'number', 'step': '0.01'},
                {'name': 'region', 'label': 'منطقه', 'type': 'select', 'options': ['شهر', 'روستا']},
            ],
            'تأیید': [
                {'name': 'approval_reason', 'label': 'دلیل تأیید', 'type': 'textarea'},
            ],
            'رد': [
                {'name': 'rejection_reason', 'label': 'دلیل رد', 'type': 'textarea'},
            ],
            'ابلاغ نتیجه': [
                {'name': 'result', 'label': 'نتیجه نهایی', 'type': 'select', 'options': ['تأیید', 'رد', 'مشروط']},
                {'name': 'notification_message', 'label': 'پیام ابلاغ', 'type': 'textarea'},
            ],
        }
        
        for key, fields in activity_fields.items():
            if key in activity_name:
                return base_fields + fields
        
        return base_fields + [{'name': 'notes', 'label': 'یادداشت‌ها', 'type': 'textarea'}]
    
    def generate_all_forms(self, output_dir="output/forms"):
        """تولید فرم برای تمام فعالیت‌ها"""
        os.makedirs(output_dir, exist_ok=True)
        
        forms = {}
        for activity in self.activities:
            html = self.generate_form_html(activity)
            filename = f"{activity.replace(' ', '_')}.html"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            forms[activity] = filepath
            
        return forms