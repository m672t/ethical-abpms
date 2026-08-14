# پروژه A-BPMS: سیستم مدیریت فرآیند اخلاق‌محور

این پروژه شامل یک سیستم مدیریت فرآیندهای کسب‌وکار (BPMS) با رویکرد اخلاق‌محور است. هسته اصلی این سیستم از [ProcessMaker](https://github.com/ProcessMaker/processmaker) به عنوان موتور پردازش فرآیند استفاده می‌کند.

## ساختار پروژه

- **`app/`**: کدهای اصلی برنامه (داشبورد Streamlit و ماژول‌های مرتبط)
- **`processmaker/`**: زیرمجموعه (submodule) اشاره‌کننده به موتور ProcessMaker
- **`requirements.txt`**: وابستگی‌های پایتون پروژه

## نحوه دریافت و اجرا

### ۱. کلون کردن مخزن اصلی
```bash
git clone https://github.com/m672t/ethical-abpms.git
cd ethical-abpms
