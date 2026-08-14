```markdown
# پروژه A-BPMS: سیستم مدیریت فرآیند اخلاق‌محور

این پروژه شامل یک سیستم مدیریت فرآیندهای کسب‌وکار (BPMS) با رویکرد اخلاق‌محور است. هسته اصلی این سیستم از [ProcessMaker](https://github.com/ProcessMaker/processmaker) به عنوان موتور پردازش فرآیند استفاده می‌کند.

## ساختار پروژه

-   `app/`  : کدهای اصلی برنامه (داشبورد Streamlit و ماژول‌های مرتبط)
-   `processmaker/`  : زیرمجموعه (submodule) اشاره‌کننده به موتور ProcessMaker
-   `requirements.txt`  : وابستگی‌های پایتون پروژه

## نحوه دریافت و اجرا

### ۱. کلون کردن مخزن اصلی
```bash
git clone https://github.com/m672t/ethical-abpms.git
cd ethical-abpms
```

### ۲. دریافت زیرمجموعه ProcessMaker
پروژه از مخزن [ProcessMaker](https://github.com/ProcessMaker/processmaker) به عنوان زیرمجموعه استفاده می‌کند. برای دریافت آن:
```bash
# دریافت محتوای زیرمجموعه
git submodule update --init --recursive
```

این دستور، موتور ProcessMaker را در پوشه `processmaker/` قرار می‌دهد. برای اطلاعات بیشتر درباره ProcessMaker، به [مستندات رسمی](https://docs.processmaker.com/) مراجعه کنید.

### ۳. راه‌اندازی محیط پایتون
```bash
# فعال‌سازی محیط مجازی (ویندوز)
venv\Scripts\activate

# نصب کتابخانه‌های مورد نیاز
pip install -r requirements.txt

# اجرای برنامه
streamlit run app/dashboard.py
```

## نکات مهم

-   بدون گیت؟   اگر گیت روی سیستم خود ندارید، می‌توانید مخزن ProcessMaker را به‌صورت دستی از [اینجا](https://github.com/processmaker/processmaker/archive/refs/heads/main.zip) دانلود کرده و محتویات آن را در پوشه `processmaker/` قرار دهید.
- مخزن ProcessMaker تحت لیسانس   AGPL-3.0   منتشر شده است. لطفاً در استفاده تجاری به شرایط آن توجه کنید.

## لینک‌های مفید

- [مخزن اصلی ProcessMaker](https://github.com/processmaker/processmaker)
- [مستندات ProcessMaker](https://docs.processmaker.com/)
- [صفحه انتشارات (Releases) ProcessMaker](https://github.com/ProcessMaker/processmaker/releases)
```

---

  توضیح تغییرات:  

1.    اشاره به ProcessMaker:   در خط اول توضیحات، به استفاده از ProcessMaker به عنوان موتور پردازش اشاره شده است.
2.    ساختار پروژه:   یک بخش جدید برای توضیح ساختار پوشه‌ها اضافه شده تا مشخص شود `processmaker/` یک زیرمجموعه است.
3.    دستورات دریافت:   دستور `git submodule update --init --recursive` به بخش نحوه اجرا اضافه شده تا کاربران بدانند چگونه محتوای آن را دریافت کنند.
4.    راهنمای بدون گیت:   برای کاربرانی که گیت ندارند، راهکار دانلود دستی ZIP اضافه شده است.
5.    مجوز و لینک‌ها:   توجه به مجوز AGPL و لینک‌های مفید برای دسترسی آسان‌تر به مستندات و مخزن اصلی اضافه شده است.
ید.
