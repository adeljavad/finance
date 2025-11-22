# ساختار خروجی JSON برای دستیار مالی

## 🎯 هدف
تبدیل خروجی‌های زشت و بی‌نظم به ساختار JSON استاندارد و زیبا با قابلیت نمایش در دیتا گرید

## 📊 ساختار کلی

### ساختار پایه
```json
{
  "success": true,
  "report_type": "balance_sheet",
  "company_id": 1,
  "period_id": 1,
  "data": {
    "metadata": {...},
    "sections": [...],
    "summary": {...}
  },
  "visualization": {...}
}
```

## 🔧 فرمت‌ترهای پیاده‌سازی شده

### 1. ترازنامه (Balance Sheet)
**فایل:** `financial_system/tools/json_formatter.py`
**متد:** `format_balance_sheet()`

```json
{
  "success": true,
  "report_type": "balance_sheet",
  "company_id": 1,
  "period_id": 1,
  "data": {
    "metadata": {
      "report_title": "ترازنامه",
      "company_name": "شرکت 1",
      "period_name": "دوره 1",
      "generation_date": "2025-10-31",
      "currency": "ریال",
      "language": "fa"
    },
    "sections": [
      {
        "title": "دارایی‌ها",
        "items": [
          {
            "account_group": "دارایی‌های جاری",
            "amount": -1634266413436,
            "formatted_amount": "-1,634,266,413,436 ریال",
            "percentage": 100.0
          }
        ],
        "total": -1634266413436,
        "formatted_total": "-1,634,266,413,436 ریال"
      },
      {
        "title": "بدهی‌ها و حقوق صاحبان سهام",
        "items": [...],
        "total": 2727405288,
        "formatted_total": "2,727,405,288 ریال"
      }
    ],
    "summary": {
      "total_assets": -1634266413436,
      "formatted_total_assets": "-1,634,266,413,436 ریال",
      "total_liabilities": 0,
      "formatted_total_liabilities": "0 ریال",
      "total_equity": -2085307665173,
      "formatted_total_equity": "-2,085,307,665,173 ریال",
      "balance_status": "نامتعادل",
      "balance_check": false,
      "difference": 451041251737,
      "formatted_difference": "451,041,251,737 ریال"
    }
  },
  "visualization": {
    "chart_type": "balance_sheet",
    "data_points": [...]
  }
}
```

### 2. نسبت‌های مالی (Financial Ratios)
**متد:** `format_financial_ratios()`

```json
{
  "success": true,
  "report_type": "financial_ratios",
  "company_id": 1,
  "period_id": 1,
  "data": {
    "metadata": {...},
    "ratios": {
      "liquidity_ratios": {
        "current_ratio": {
          "value": 2.1,
          "status": "مطلوب",
          "description": "نسبت جاری"
        },
        "quick_ratio": {...}
      },
      "profitability_ratios": {
        "return_on_assets": {
          "value": 8.5,
          "status": "مطلوب",
          "description": "بازده دارایی‌ها",
          "unit": "%"
        },
        "return_on_equity": {...},
        "profit_margin": {...}
      }
    },
    "analysis": {
      "overall_status": "مطلوب",
      "liquidity_status": "مطلوب",
      "profitability_status": "مطلوب",
      "recommendations": [
        "بررسی منظم نسبت‌های مالی",
        "ادامه روند فعلی",
        "حفظ سطح سودآوری"
      ],
      "risk_level": "کم"
    }
  },
  "visualization": {...}
}
```

### 3. صورت سود و زیان (Income Statement)
**متد:** `format_income_statement()`

```json
{
  "success": true,
  "report_type": "income_statement",
  "company_id": 1,
  "period_id": 1,
  "data": {
    "metadata": {...},
    "sections": [
      {
        "title": "درآمدها",
        "items": [
          {
            "account_group": "فروش کالا",
            "amount": 4000000000,
            "formatted_amount": "4,000,000,000 ریال",
            "percentage": 80.0
          }
        ],
        "total": 5000000000,
        "formatted_total": "5,000,000,000 ریال"
      },
      {
        "title": "هزینه‌ها",
        "items": [...],
        "total": 4200000000,
        "formatted_total": "4,200,000,000 ریال"
      }
    ],
    "summary": {
      "total_revenue": 5000000000,
      "formatted_total_revenue": "5,000,000,000 ریال",
      "total_expenses": 4200000000,
      "formatted_total_expenses": "4,200,000,000 ریال",
      "net_income": 800000000,
      "formatted_net_income": "800,000,000 ریال",
      "profit_margin": 16.0,
      "profit_status": "سود",
      "is_profitable": true
    }
  },
  "visualization": {...}
}
```

### 4. تراز چهارستونی (Four Column Balance)
**متد:** `format_four_column_balance()`

```json
{
  "success": true,
  "report_type": "four_column_balance",
  "company_id": 1,
  "period_id": 1,
  "data": {
    "metadata": {...},
    "accounts": [
      {
        "account_name": "صندوق",
        "beginning_balance": 100000000,
        "formatted_beginning_balance": "100,000,000 ریال",
        "debit_turnover": 50000000,
        "formatted_debit_turnover": "50,000,000 ریال",
        "credit_turnover": 30000000,
        "formatted_credit_turnover": "30,000,000 ریال",
        "ending_balance": 120000000,
        "formatted_ending_balance": "120,000,000 ریال"
      }
    ],
    "totals": {
      "total_beginning_balance": 600000000,
      "formatted_total_beginning_balance": "600,000,000 ریال",
      "total_debit_turnover": 250000000,
      "formatted_total_debit_turnover": "250,000,000 ریال",
      "total_credit_turnover": 180000000,
      "formatted_total_credit_turnover": "180,000,000 ریال",
      "total_ending_balance": 670000000,
      "formatted_total_ending_balance": "670,000,000 ریال"
    }
  },
  "visualization": {...}
}
```

## 🎨 بخش Visualization

### داده‌های نمودار
```json
"visualization": {
  "chart_type": "balance_sheet",
  "data_points": [
    {
      "name": "دارایی‌ها",
      "value": 1634266413436,
      "color": "#4CAF50"
    },
    {
      "name": "بدهی‌ها",
      "value": 0,
      "color": "#F44336"
    },
    {
      "name": "حقوق صاحبان سهام",
      "value": 2085307665173,
      "color": "#2196F3"
    }
  ]
}
```

## 🔄 ابزارهای به‌روز شده

### فایل‌های اصلاح شده:
1. **`financial_system/tools/financial_analysis_tools.py`**
   - `analyze_financial_ratios_tool()`
   - `generate_real_balance_sheet()`

2. **`financial_system/agents/financial_agent.py`**
   - استفاده از فرمت‌ترهای JSON در خروجی

## 🧪 تست و اعتبارسنجی

### فایل‌های تست:
1. **`test_json_formatter.py`** - تست فرمت‌ترها
2. **`test_json_output_demo.py`** - نمایش نمونه‌ها

### اجرای تست:
```bash
python test_json_output_demo.py
```

## 📈 مزایای ساختار جدید

### 1. ساختار استاندارد
- ✅ JSON قابل پردازش توسط سیستم‌های مختلف
- ✅ ساختار سلسله‌مراتبی و سازمان‌یافته
- ✅ پشتیبانی از زبان فارسی

### 2. قابلیت نمایش
- ✅ نمایش در دیتا گرید و جدول
- ✅ داده‌های فرمت‌بندی شده
- ✅ قابلیت‌های بصری و نمودار

### 3. متادیتای کامل
- ✅ اطلاعات شرکت و دوره
- ✅ تاریخ تولید
- ✅ واحد پول و زبان

### 4. قابلیت توسعه
- ✅ ساختار قابل توسعه برای گزارش‌های جدید
- ✅ پشتیبانی از انواع مختلف نمودار
- ✅ قابلیت افزودن بخش‌های جدید

## 🚀 نحوه استفاده

### در ابزارهای مالی:
```python
from financial_system.tools.json_formatter import FinancialJSONFormatter

formatter = FinancialJSONFormatter(company_id=1, period_id=1)
result = formatter.format_balance_sheet(balance_data)
```

### در فرانت‌اند:
```javascript
// نمایش در دیتا گرید
const dataGrid = new DataGrid('#grid', {
  dataSource: response.data.sections,
  columns: [
    { field: 'account_group', title: 'گروه حساب' },
    { field: 'formatted_amount', title: 'مبلغ' },
    { field: 'percentage', title: 'درصد' }
  ]
});

// نمایش نمودار
const chart = new Chart('#chart', {
  type: 'pie',
  data: response.visualization.data_points
});
```

## 📋 مقایسه با ساختار قبلی

### ساختار قبلی (متن ساده):
```
گزارش ترازنامه - شرکت 1 - دوره 1
دارایی‌ها:
- مجموع دارایی‌ها: -1,634,266,413,436 ریال
بدهی‌ها و حقوق صاحبان سهام:
- مجموع بدهی‌ها: 0 ریال
- حقوق صاحبان سهام: 2,727,405,288 ریال
- سود/زیان دوره: -2,088,035,070,461 ریال
- حقوق صاحبان سهام نهایی: -2,085,307,665,173 ریال
```

### ساختار جدید (JSON):
```json
{
  "success": true,
  "report_type": "balance_sheet",
  "data": {
    "metadata": {...},
    "sections": [...],
    "summary": {...}
  },
  "visualization": {...}
}
```

## 🎯 نتیجه‌گیری

ساختار جدید JSON:
- **زیبا و سازمان‌یافته** است
- **قابل پردازش** توسط سیستم‌های مختلف
- **قابل نمایش** در دیتا گرید و نمودار
- **قابل توسعه** برای نیازهای آینده
- **پشتیبانی کامل** از زبان فارسی

این ساختار مشکل خروجی‌های زشت و بی‌نظم را به طور کامل حل کرده و امکان نمایش حرفه‌ای گزارش‌های مالی را فراهم می‌کند.
