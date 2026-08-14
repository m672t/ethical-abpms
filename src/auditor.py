"""
ماژول عامل بازرس - بررسی انطباق اخلاقی فرآیند
"""

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ethics import EthicalRules

class AuditorAgent:
    """
    عامل بازرس اخلاقی - فرآیند را بررسی کرده و موارد نقض را گزارش می‌دهد
    """
    
    def __init__(self):
        self.rules = EthicalRules()
        self.violations = []
        self.ethical_score = 100
        
    def audit(self, log_path, process_model):
        """
        انجام بازرسی اخلاقی بر روی فرآیند
        """
        # بارگذاری داده
        df = pd.read_csv(log_path)
        
        # بررسی تمام قواعد
        self.violations = self.rules.check_all(df, process_model)
        
        # محاسبه امتیاز
        self.ethical_score = self.rules.get_ethical_score(self.violations)
        
        # تولید گزارش
        report = self.generate_report(df)
        
        return {
            'violations': self.violations,
            'score': self.ethical_score,
            'report': report,
            'has_violations': len(self.violations) > 0,
            'severity_summary': self._get_severity_summary()
        }
    
    def generate_report(self, df):
        """
        تولید گزارش بازرسی با دلایل شفاف
        """
        report = []
        report.append("=" * 70)
        report.append("📋 گزارش بازرسی اخلاقی - A-BPMS")
        report.append("=" * 70)
        report.append(f"📅 تاریخ بازرسی: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"📊 تعداد کیس‌ها: {df['case_id'].nunique() if 'case_id' in df.columns else 'نامشخص'}")
        report.append("")
        
        if not self.violations:
            report.append("✅ همه قواعد اخلاقی رعایت شده‌اند.")
            report.append(f"🏆 امتیاز اخلاقی: {self.ethical_score}/100")
        else:
            report.append(f"⚠️ تعداد تخلف‌ها: {len(self.violations)}")
            report.append(f"🏆 امتیاز اخلاقی: {self.ethical_score}/100")
            report.append("")
            report.append("-" * 70)
            report.append("📋 جزئیات تخلف‌های شناسایی‌شده:")
            report.append("-" * 70)
            report.append("")
            
            for i, v in enumerate(self.violations, 1):
                report.append(f"┌── تخلف #{i} ──")
                report.append(f"│ 📌 قاعده: {v['rule']}")
                report.append(f"│ 🔍 نوع: {v['type']}")
                report.append(f"│ 📝 جزئیات: {v['details']}")
                report.append(f"│ 💡 توضیح: {v.get('explanation', 'توضیحی ثبت نشده')}")
                report.append(f"│ ⚡ شدت: {v['severity']}")
                report.append(f"│ 🔧 پیشنهاد: {v['suggestion']}")
                report.append(f"└─────────────────")
                report.append("")
        
        # امتیاز تفکیکی
        report.append("-" * 70)
        report.append("📊 امتیاز اخلاقی تفکیکی:")
        report.append("-" * 70)
        
        # محاسبه امتیاز هر قاعده
        rule_scores = {
            'عدالت': 100,
            'شفافیت': 100,
            'قابلیت اعتراض': 100,
            'حریم خصوصی': 100
        }
        
        for v in self.violations:
            if v['rule'] in rule_scores:
                penalty = {'high': 30, 'medium': 15, 'low': 5}.get(v.get('severity', 'low'), 5)
                rule_scores[v['rule']] = max(0, rule_scores[v['rule']] - penalty)
        
        for rule, score in rule_scores.items():
            status = "✔" if score >= 80 else "⚠" if score >= 50 else "✘"
            report.append(f"   {status} {rule}: {score}/100")
        
        report.append("")
        report.append("-" * 70)
        report.append("📌 توصیه‌ها:")
        report.append("-" * 70)
        
        for v in self.violations:
            report.append(f"   • {v['suggestion']}")
        
        report.append("")
        report.append("=" * 70)
        report.append("🔒 این گزارش به‌صورت خودکار توسط Agentic-BPMS تولید شده است.")
        report.append("👤 نظارت انسانی همچنان ضروری است.")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def _get_severity_summary(self):
        """
        خلاصه شدت تخلف‌ها
        """
        summary = {'high': 0, 'medium': 0, 'low': 0}
        for v in self.violations:
            severity = v.get('severity', 'low')
            if severity in summary:
                summary[severity] += 1
        return summary
    
    def get_correction_suggestions(self):
        """
        دریافت پیشنهادات اصلاحی بر اساس تخلف‌ها
        """
        suggestions = []
        for v in self.violations:
            if 'suggestion' in v and v['suggestion'] not in suggestions:
                suggestions.append(v['suggestion'])
        return suggestions