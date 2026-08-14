"""
ماژول عامل اصلاح‌کننده - اصلاح فرآیند بر اساس بازخورد اخلاقی
"""

import pandas as pd
import os
import json
from src.auditor import AuditorAgent

class CorrectorAgent:
    """
    عامل اصلاح‌کننده اخلاقی - فرآیند را بر اساس بازخورد بازرس اصلاح می‌کند
    """
    
    def __init__(self):
        self.auditor = AuditorAgent()
        self.corrections_applied = []
        
    def correct(self, log_path, process_model, forms):
        """
        اصلاح فرآیند بر اساس تخلف‌های شناسایی‌شده
        """
        audit_result = self.auditor.audit(log_path, process_model)
        
        corrections = {
            'audit_result': audit_result,
            'model_corrections': [],
            'form_corrections': [],
            'new_activities': [],
            'removed_activities': []
        }
        
        for violation in audit_result['violations']:
            correction = self._apply_correction(violation, process_model, forms)
            corrections['model_corrections'].append(correction)
            
            if correction.get('new_activity'):
                corrections['new_activities'].append(correction['new_activity'])
            if correction.get('removed_activity'):
                corrections['removed_activities'].append(correction['removed_activity'])
        
        self.corrections_applied = corrections
        
        return corrections
    
    def _apply_correction(self, violation, process_model, forms):
        """
        اعمال اصلاح برای یک تخلف خاص
        """
        correction = {
            'rule': violation['rule'],
            'type': violation['type'],
            'description': violation['suggestion'],
            'applied': False
        }
        
        if violation['rule'] == 'عدالت':
            if 'تبعیض جنسیتی' in violation['type']:
                correction['new_activity'] = {
                    'name': 'بررسی تبعیض',
                    'description': 'بررسی اینکه آیا تصمیم‌گیری بر اساس جنسیت بوده است',
                    'position': 'قبل از تصمیم‌گیری'
                }
                correction['applied'] = True
                
        elif violation['rule'] == 'شفافیت':
            correction['form_correction'] = {
                'add_field': 'decision_explanation',
                'field_label': 'توضیح دلیل تصمیم',
                'field_type': 'textarea'
            }
            correction['applied'] = True
            
        elif violation['rule'] == 'قابلیت اعتراض':
            correction['new_activity'] = {
                'name': 'بازبینی درخواست',
                'description': 'کاربر می‌تواند درخواست بازبینی دهد',
                'position': 'بعد از تصمیم‌گیری'
            }
            correction['applied'] = True
            
        elif violation['rule'] == 'حریم خصوصی':
            correction['form_correction'] = {
                'hide_fields': ['national_id', 'gender'],
                'field_label': 'فیلدهای حساس پنهان شدند'
            }
            correction['applied'] = True
        
        return correction
    
    def generate_corrected_model(self, original_model, corrections):
        """
        تولید مدل اصلاح‌شده بر اساس اصلاحات اعمال‌شده
        """
        corrected_info = {
            'original_activities': original_model.get_activities() if original_model else [],
            'added_activities': [],
            'removed_activities': [],
            'modified_activities': []
        }
        
        for correction in corrections.get('model_corrections', []):
            if correction.get('new_activity'):
                corrected_info['added_activities'].append(correction['new_activity']['name'])
            if correction.get('removed_activity'):
                corrected_info['removed_activities'].append(correction['removed_activity'])
        
        return corrected_info
    
    # ============================================================
    # 🔹 متد جدید برای استقرار در BPMS
    # ============================================================
    def deploy_to_bpms(self, bpmn_path):
        """
        استقرار فرآیند اصلاح‌شده در BPMS (ProcessMaker)
        """
        from src.bpms_integration import BPMSEngine
        
        engine = BPMSEngine()
        
        # بررسی نصب
        check = engine.check_installation()
        if not check['installed']:
            return {
                'success': False,
                'message': check['message'],
                'suggestion': 'لطفاً ProcessMaker را از https://github.com/ProcessMaker/processmaker دانلود کرده و در پوشه‌ی پروژه قرار دهید.'
            }
        
        # وارد کردن BPMN
        import_result = engine.import_bpmn(bpmn_path)
        if not import_result['success']:
            return import_result
        
        # تولید گزارش
        report = engine.generate_integration_report(bpmn_path)
        
        return {
            'success': True,
            'message': '✅ فرآیند با موفقیت در BPMS (ProcessMaker) مستقر شد!',
            'report': report,
            'import_result': import_result
        }