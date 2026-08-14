"""
ماژول قواعد اخلاقی - تعریف قواعد و بررسی انطباق
"""

import json
import os
import pandas as pd

class EthicalRules:
    """تعریف قواعد اخلاقی برای فرآیند"""
    
    def __init__(self, config_path=None):
        # اگر مسیر داده نشده، از مسیر پیش‌فرض استفاده کن
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'ethical_rules.json'
            )
        
        # بارگذاری از فایل JSON
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.rules = self.config.get('rules', {})
        except FileNotFoundError:
            # اگر فایل وجود نداشت، از قواعد پیش‌فرض استفاده کن
            self.rules = {
                'fairness': {
                    'name': 'عدالت',
                    'description': 'عدم تبعیض بر اساس متغیرهای حساس',
                    'sensitive_attributes': ['gender', 'ethnicity', 'race', 'جنسیت', 'قومیت']
                },
                'transparency': {
                    'name': 'شفافیت',
                    'description': 'دلایل تصمیم‌گیری باید قابل توضیح باشد'
                },
                'appealability': {
                    'name': 'قابلیت اعتراض',
                    'description': 'کاربر باید بتواند درخواست بازبینی دهد'
                },
                'privacy': {
                    'name': 'حریم خصوصی',
                    'description': 'داده‌های حساس نباید نمایش داده شوند'
                }
            }
        
        # متغیرهای حساس
        self.sensitive_attributes = self.rules.get('fairness', {}).get('sensitive_attributes', 
            ['gender', 'ethnicity', 'race', 'جنسیت', 'قومیت'])
    
    def check_fairness(self, log_data, model):
     """
      بررسی عدالت - تحلیل آماری تصمیم‌ها بر اساس Case (نه Event)
     """
     violations = []
     df = log_data
    
    # ============================================================
    # ۱. تبعیض جنسیتی - تحلیل آماری بر اساس Case
    # ============================================================
     if 'gender' in df.columns and 'decision' in df.columns:
        
        # ========================================================
        # مرحله ۱: استخراج تصمیم نهایی هر Case
        # ========================================================
        # پیدا کردن آخرین تصمیم برای هر case_id
        case_decisions = df[df['decision'] != '-'].groupby('case_id').last().reset_index()
        
        # اگر ستون gender در case_decisions نیست، از df اصلی بگیر
        if 'gender' not in case_decisions.columns:
            case_genders = df[['case_id', 'gender']].drop_duplicates(subset=['case_id'])
            case_decisions = case_decisions.merge(case_genders, on='case_id', how='left')
        
        # ========================================================
        # مرحله ۲: محاسبه آمار بر اساس Case
        # ========================================================
        # مردان
        male_cases = case_decisions[case_decisions['gender'] == 'مرد']
        male_total = len(male_cases)
        male_approved = len(male_cases[male_cases['decision'] == 'تأیید'])
        male_rejected = len(male_cases[male_cases['decision'] == 'رد'])
        
        # زنان
        female_cases = case_decisions[case_decisions['gender'] == 'زن']
        female_total = len(female_cases)
        female_approved = len(female_cases[female_cases['decision'] == 'تأیید'])
        female_rejected = len(female_cases[female_cases['decision'] == 'رد'])
        
        # ========================================================
        # مرحله ۳: محاسبه نرخ‌ها
        # ========================================================
        male_approval_rate = male_approved / male_total if male_total > 0 else 0
        male_rejection_rate = male_rejected / male_total if male_total > 0 else 0
        
        female_approval_rate = female_approved / female_total if female_total > 0 else 0
        female_rejection_rate = female_rejected / female_total if female_total > 0 else 0
        
        # اختلاف نرخ‌ها
        approval_gap = abs(male_approval_rate - female_approval_rate)
        rejection_gap = abs(male_rejection_rate - female_rejection_rate)
        
        # ========================================================
        # مرحله ۴: تشخیص تبعیض
        # ========================================================
        threshold = 0.2  # آستانه ۲۰٪
        
        if approval_gap > threshold or rejection_gap > threshold:
            # تشخیص گروه تبعیض‌دیده
            if female_approval_rate < male_approval_rate and female_rejection_rate > male_rejection_rate:
                discriminated_group = "زنان"
                privileged_group = "مردان"
            elif male_approval_rate < female_approval_rate and male_rejection_rate > female_rejection_rate:
                discriminated_group = "مردان"
                privileged_group = "زنان"
            else:
                discriminated_group = "گروهی از متقاضیان"
                privileged_group = "گروه دیگر"
            
            violations.append({
                'rule': 'عدالت',
                'type': 'تبعیض جنسیتی',
                'details': f'نرخ تأیید مردان: {male_approval_rate:.1%} ({male_approved}/{male_total})، زنان: {female_approval_rate:.1%} ({female_approved}/{female_total}) | نرخ رد مردان: {male_rejection_rate:.1%} ({male_rejected}/{male_total})، زنان: {female_rejection_rate:.1%} ({female_rejected}/{female_total})',
                'severity': 'high',
                'suggestion': 'متغیر جنسیت را از معیارهای تصمیم‌گیری حذف کنید و فرآیند را بازطراحی کنید',
                'explanation': f'بر اساس تحلیل {male_total + female_total} پرونده، از مجموع {male_total} پرونده مردان، {male_approved} مورد تأیید (نرخ {male_approval_rate:.1%}) و {male_rejected} مورد رد (نرخ {male_rejection_rate:.1%}) شده است. از مجموع {female_total} پرونده زنان، {female_approved} مورد تأیید (نرخ {female_approval_rate:.1%}) و {female_rejected} مورد رد (نرخ {female_rejection_rate:.1%}) شده است. اختلاف {max(approval_gap, rejection_gap)*100:.1f} درصدی در نرخ‌های تصمیم‌گیری نشان‌دهنده تبعیض سیستماتیک علیه گروه {discriminated_group} است.'
            })
    
    # ============================================================
    # ۲. تبعیض منطقه‌ای - تحلیل بر اساس Case
    # ============================================================
     if 'region' in df.columns and 'decision' in df.columns:
        
        # استخراج تصمیم نهایی هر Case
        case_decisions = df[df['decision'] != '-'].groupby('case_id').last().reset_index()
        
        if 'region' not in case_decisions.columns:
            case_regions = df[['case_id', 'region']].drop_duplicates(subset=['case_id'])
            case_decisions = case_decisions.merge(case_regions, on='case_id', how='left')
        
        # شهری
        city_cases = case_decisions[case_decisions['region'] == 'شهر']
        city_total = len(city_cases)
        city_approved = len(city_cases[city_cases['decision'] == 'تأیید'])
        
        # روستایی
        rural_cases = case_decisions[case_decisions['region'] == 'روستا']
        rural_total = len(rural_cases)
        rural_approved = len(rural_cases[rural_cases['decision'] == 'تأیید'])
        
        city_approval_rate = city_approved / city_total if city_total > 0 else 0
        rural_approval_rate = rural_approved / rural_total if rural_total > 0 else 0
        
        regional_gap = abs(city_approval_rate - rural_approval_rate)
        
        if regional_gap > 0.25:
            discriminated = "روستایی" if rural_approval_rate < city_approval_rate else "شهری"
            violations.append({
                'rule': 'عدالت',
                'type': 'تبعیض منطقه‌ای (غیرمستقیم)',
                'details': f'نرخ تأیید شهری: {city_approval_rate:.1%} ({city_approved}/{city_total})، روستایی: {rural_approval_rate:.1%} ({rural_approved}/{rural_total})',
                'severity': 'medium',
                'suggestion': 'معیار منطقه را بازبینی کنید یا وزن آن را در تصمیم‌گیری کاهش دهید',
                'explanation': f'اختلاف {regional_gap*100:.1f} درصدی در نرخ تأیید بین مناطق شهری و روستایی می‌تواند نشان‌دهنده تبعیض غیرمستقیم علیه گروه‌های {discriminated} باشد.'
            })
    
     return violations
 
    def check_transparency(self, log_data, model):
        """
        بررسی شفافیت - آیا دلایل تصمیم‌گیری ثبت شده است؟
        """
        violations = []
        df = log_data
        
        # ============================================================
        # ۱. بررسی وجود توضیح برای تصمیم‌گیری‌ها
        # ============================================================
        if 'decision' in df.columns:
            # پیدا کردن فعالیت‌های تصمیم‌گیری
            decision_activities = df[df['decision'] != '-']['decision'].unique()
            
            for decision in decision_activities:
                decision_rows = df[df['decision'] == decision]
                
                # بررسی وجود ستون explanation
                if 'explanation' not in df.columns:
                    violations.append({
                        'rule': 'شفافیت',
                        'type': f'عدم شفافیت در تصمیم‌گیری {decision}',
                        'details': f'برای تصمیم‌گیری {decision} هیچ ستون توضیحی وجود ندارد',
                        'severity': 'high',
                        'suggestion': f'برای هر تصمیم {decision}، یک فیلد توضیح (explanation) اضافه کنید',
                        'explanation': f'برای {len(decision_rows)} مورد تصمیم {decision}، هیچ توضیحی ثبت نشده است. این موضوع شفافیت فرآیند را به شدت کاهش می‌دهد.'
                    })
                    break
                
                # بررسی اینکه آیا توضیح پر شده است
                empty_explanations = decision_rows[decision_rows['explanation'].isna() | (decision_rows['explanation'] == '')]
                if len(empty_explanations) > 0:
                    violations.append({
                        'rule': 'شفافیت',
                        'type': f'توضیح تصمیم {decision} ناقص است',
                        'details': f'{len(empty_explanations)} مورد از {len(decision_rows)} تصمیم {decision} بدون توضیح هستند',
                        'severity': 'high',
                        'suggestion': f'برای تمام موارد تصمیم {decision}، توضیح کامل ثبت کنید',
                        'explanation': f'{len(empty_explanations)} مورد تصمیم {decision} فاقد توضیح هستند. این موضوع شفافیت فرآیند را کاهش می‌دهد.'
                    })
        
        return violations
    
    def check_appealability(self, log_data, model):
        """
        بررسی قابلیت اعتراض - آیا مسیر بازبینی وجود دارد؟
        """
        violations = []
        
        if model:
            # دریافت فعالیت‌ها
            if hasattr(model, 'get_activities'):
                activities = model.get_activities()
            else:
                activities = []
            
            # کلمات کلیدی برای تشخیص فعالیت بازبینی
            appeal_keywords = ['بازبینی', 'اعتراض', 'تجدید نظر', 'appeal', 'review', 'بازنگری']
            
            has_appeal = any(
                any(keyword in act for keyword in appeal_keywords) 
                for act in activities
            )
            
            if not has_appeal:
                violations.append({
                    'rule': 'قابلیت اعتراض',
                    'type': 'عدم وجود مسیر بازبینی',
                    'details': 'هیچ فعالیت بازبینی یا اعتراضی در فرآیند وجود ندارد',
                    'severity': 'medium',
                    'suggestion': 'یک فعالیت "بازبینی درخواست" به فرآیند اضافه کنید',
                    'explanation': 'وجود مسیر بازبینی به کاربران امکان می‌دهد در صورت نارضایتی از تصمیم، درخواست تجدید نظر دهند. عدم وجود این مسیر، قابلیت اعتراض فرآیند را نقض می‌کند.'
                })
        
        return violations
    
    def check_privacy(self, log_data, model):
        """
        بررسی حریم خصوصی - داده‌های حساس محافظت می‌شوند؟
        """
        violations = []
        df = log_data
        
        sensitive_cols = [col for col in df.columns if col in self.sensitive_attributes]
        
        if sensitive_cols:
            violations.append({
                'rule': 'حریم خصوصی',
                'type': 'وجود داده‌های حساس',
                'details': f'داده‌های حساس در خروجی وجود دارند: {", ".join(sensitive_cols)}',
                'severity': 'high',
                'suggestion': 'فیلدهای حساس را در فرم‌ها پنهان یا رمزگذاری کنید',
                'explanation': f'داده‌های حساس مانند {", ".join(sensitive_cols)} نباید در خروجی نمایش داده شوند تا حریم خصوصی کاربران حفظ شود. این داده‌ها باید قبل از نمایش حذف یا رمزگذاری شوند.'
            })
        
        return violations
    
    def check_all(self, log_data, model):
        """
        بررسی تمام قواعد اخلاقی
        """
        all_violations = []
        
        checks = [
            self.check_fairness,
            self.check_transparency,
            self.check_appealability,
            self.check_privacy
        ]
        
        for check_func in checks:
            try:
                violations = check_func(log_data, model)
                if violations:
                    all_violations.extend(violations)
            except Exception as e:
                # اگر خطایی در بررسی رخ داد، آن را نادیده بگیر
                pass
        
        return all_violations
    
    def get_ethical_score(self, violations):
        """
        محاسبه امتیاز اخلاقی بر اساس تعداد و شدت تخلف‌ها
        """
        if not violations:
            return 100
        
        # وزن هر تخلف بر اساس شدت
        severity_weights = {
            'high': 20,
            'medium': 10,
            'low': 5
        }
        
        # محاسبه مجموع جریمه‌ها
        total_penalty = sum(severity_weights.get(v.get('severity', 'low'), 5) for v in violations)
        
        # حداکثر جریمه ۹۰ (حداقل امتیاز ۱۰)
        max_penalty = 90
        penalty = min(total_penalty, max_penalty)
        
        score = max(10, 100 - penalty)
        
        return score