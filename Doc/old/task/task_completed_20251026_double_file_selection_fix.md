# Task Completed: رفع مشکل انتخاب دو دفعه فایل در صفحه آپلود

**تاریخ:** 2025-10-26  
**وضعیت:** ✅ تکمیل شده

## شرح مشکل
در آدرس `http://127.0.0.1:8000/data-importer/upload/` کاربر مجبور بود دو دفعه فایل اکسل را انتخاب کند.

## علت مشکل
- تداخل بین عملکرد drag-and-drop و کلیک در کد JavaScript
- وقتی کاربر روی ناحیه آپلود کلیک می‌کرد، هم دکمه انتخاب فایل فعال می‌شد و هم کلیک روی ناحیه آپلود
- این باعث می‌شد دیالوگ انتخاب فایل دو بار ظاهر شود


ترتیب	شناسه قلم سند	شماره ردیف	شماره سند	شماره عطف	تاریخ سند	بدهکار	بستانکار	توضیحات	شرح به زبان انگلیسی	شماره روزانه	شماره پیگیری	تاریخ پیگیری	شناسه سند	معین	AccountGroupRef	GLRef	DLLevel4	مانده بدهکار	مانده بستانکار	مانده	Title1	Code1	Title_En1	Title2	Code2	Title_En2	Title3	Code3	Title_En3	Title4	Code4	Title_En4
418	52413	11	229	229	1400/06/01	1,000,000,000	0	بابت پاس شدن چک شماره ی 211/852 _ بانک توسعه صادرات		2	211/852	1400/05/25	1333	121	14	19		752,044,791,803	858,345,753,036	-106,300,961,233	بدهیهای جاری	04		اسناد پرداختنی	0428		چکهای پرداختنی	0428001				
419	52414	12	229	229	1400/06/01	3,200,000,000	0	بابت پاس شدن چک شماره ی 946179 _ بانک پاسارگاد		2	946179	1400/05/26	1333	121	14	19		755,244,791,803	858,345,753,036	-103,100,961,233	بدهیهای جاری	04		اسناد پرداختنی	0428		چکهای پرداختنی	0428001				
420	52530	1	231	231	1400/06/02	15,245,179	0	بابت پاس شدن چک شماره ی 07-9932/683734 _ بانک ملی		2	07-9932/683734	1400/05/23	1335	121	14	19		755,260,036,982	858,345,753,036	-103,085,716,054	بدهیهای جاری	04		اسناد پرداختنی	0428		چکهای پرداختنی	0428001				

## راه‌حل پیاده‌سازی شده

### 1. رفع تداخل کلیک در JavaScript
```javascript
// کلیک روی ناحیه آپلود - فقط روی قسمت‌های خالی کلیک کند
let isClicking = false;
uploadArea.addEventListener('click', function(e) {
    // جلوگیری از کلیک روی دکمه انتخاب فایل و جلوگیری از کلیک‌های متوالی
    if (!e.target.closest('.file-label') && !isClicking) {
        isClicking = true;
        document.getElementById('excel_file').click();
        
        // بازنشانی فلگ پس از مدت کوتاه
        setTimeout(() => {
            isClicking = false;
        }, 300);
    }
});
```

### 2. رفع خطای JSON Serialization
افزودن تابع `convert_numpy_types` برای تبدیل انواع numpy به انواع استاندارد پایتون:

```python
def convert_numpy_types(obj):
    """تبدیل انواع numpy به انواع استاندارد پایتون برای JSON"""
    import numpy as np
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj
```

## فایل‌های تغییر یافته
1. `data_importer/templates/data_importer/upload.html` - رفع تداخل کلیک
2. `data_importer/views.py` - رفع خطای JSON serialization

## نتیجه
- مشکل انتخاب دو دفعه فایل برطرف شد
- خطای `Object of type int64 is not JSON serializable` برطرف شد
- عملکرد آپلود فایل بهبود یافت
- کاربران می‌توانند فایل را فقط با یک کلیک انتخاب کنند

## تست
- آپلود فایل اکسل باید بدون مشکل انجام شود
- فایل فقط یک بار انتخاب می‌شود
- تحلیل فایل و ذخیره در دیتابیس بدون خطا انجام می‌شود
