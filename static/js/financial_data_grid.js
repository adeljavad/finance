/**
 * FinancialDataGrid - کامپوننت نمایش داده‌های مالی
 * کامپوننت قابل استفاده مجدد برای نمایش داده‌های مالی در کل پروژه
 */

class FinancialDataGrid {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.data = options.data || [];
        this.columns = options.columns || [];
        this.title = options.title || 'گزارش مالی';
        this.exportEnabled = options.exportEnabled !== false;
        this.filterEnabled = options.filterEnabled !== false;
        this.paginationEnabled = options.paginationEnabled !== false;
        this.pageSize = options.pageSize || 50;
        
        this.currentPage = 1;
        this.filteredData = [];
        this.sortConfig = { field: null, direction: 'asc' };
        this.filterConfig = {};
        
        this.init();
    }

    init() {
        if (!this.container) {
            console.error('Container not found:', this.containerId);
            return;
        }

        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = this.generateHTML();
        this.applyFilters();
        this.renderTable();
    }

    generateHTML() {
        return `
            <div class="financial-data-grid" dir="rtl">
                <div class="grid-header">
                    <div class="header-left">
                        <h3 class="grid-title">${this.title}</h3>
                        <div class="stats">
                            <span class="stat-item">تعداد رکورد: <strong id="record-count">0</strong></span>
                            <span class="stat-item">صفحه: <strong id="page-info">1</strong></span>
                        </div>
                    </div>
                    <div class="header-right">
                        ${this.generateControls()}
                    </div>
                </div>
                
                ${this.filterEnabled ? this.generateFilterPanel() : ''}
                
                <div class="table-container">
                    <table class="financial-table" id="financial-table">
                        <thead>
                            <tr>${this.generateTableHeaders()}</tr>
                        </thead>
                        <tbody id="table-body">
                            <!-- Data will be populated here -->
                        </tbody>
                    </table>
                </div>
                
                ${this.paginationEnabled ? this.generatePagination() : ''}
                
                <div class="grid-footer">
                    ${this.generateExportButtons()}
                </div>
            </div>
        `;
    }

    generateControls() {
        return `
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="global-search" placeholder="جستجو در تمام فیلدها..." class="search-input">
                    <button class="search-btn" id="search-btn">🔍</button>
                </div>
                <button class="btn btn-primary" id="export-excel-btn">
                    📊 خروجی Excel
                </button>
                <button class="btn btn-secondary" id="export-pdf-btn">
                    📄 خروجی PDF
                </button>
                <button class="btn btn-info" id="print-btn">
                    🖨️ چاپ
                </button>
            </div>
        `;
    }

    generateFilterPanel() {
        if (this.columns.length === 0) return '';

        return `
            <div class="filter-panel">
                <div class="filter-header">
                    <h4>فیلترها</h4>
                    <button class="btn btn-sm" onclick="this.toggleFilterPanel()">بستن</button>
                </div>
                <div class="filter-fields">
                    ${this.columns.map(col => this.generateFilterField(col)).join('')}
                </div>
                <div class="filter-actions">
                    <button class="btn btn-primary" onclick="this.applyFilters()">اعمال فیلترها</button>
                    <button class="btn btn-secondary" onclick="this.clearFilters()">پاک کردن فیلترها</button>
                </div>
            </div>
        `;
    }

    generateFilterField(column) {
        if (column.filterable === false) return '';

        return `
            <div class="filter-field">
                <label for="filter-${column.field}">${column.title}</label>
                <input type="text" 
                       id="filter-${column.field}" 
                       class="filter-input" 
                       placeholder="فیلتر ${column.title}"
                       onchange="this.updateFilter('${column.field}', this.value)">
            </div>
        `;
    }

    generateTableHeaders() {
        if (this.columns.length === 0 && this.data.length > 0) {
            // Auto-generate columns from data
            this.autoGenerateColumns();
        }

        return this.columns.map(col => `
            <th data-field="${col.field}" 
                onclick="this.sortTable('${col.field}')"
                class="${this.sortConfig.field === col.field ? `sorted ${this.sortConfig.direction}` : ''}">
                ${col.title}
                ${this.sortConfig.field === col.field ? 
                    (this.sortConfig.direction === 'asc' ? ' ↑' : ' ↓') : ''}
            </th>
        `).join('');
    }

    generatePagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.pageSize);
        
        return `
            <div class="pagination">
                <div class="pagination-info">
                    نمایش ${this.getStartIndex() + 1} تا ${this.getEndIndex()} از ${this.filteredData.length} رکورد
                </div>
                <div class="pagination-controls">
                    <button class="btn btn-sm" 
                            ${this.currentPage === 1 ? 'disabled' : ''}
                            onclick="this.goToPage(1)">اولین</button>
                    <button class="btn btn-sm" 
                            ${this.currentPage === 1 ? 'disabled' : ''}
                            onclick="this.goToPage(${this.currentPage - 1})">قبلی</button>
                    
                    ${this.generatePageNumbers(totalPages)}
                    
                    <button class="btn btn-sm" 
                            ${this.currentPage === totalPages ? 'disabled' : ''}
                            onclick="this.goToPage(${this.currentPage + 1})">بعدی</button>
                    <button class="btn btn-sm" 
                            ${this.currentPage === totalPages ? 'disabled' : ''}
                            onclick="this.goToPage(${totalPages})">آخرین</button>
                </div>
                <div class="page-size-selector">
                    <label>تعداد در صفحه:</label>
                    <select onchange="this.changePageSize(parseInt(this.value))">
                        <option value="10" ${this.pageSize === 10 ? 'selected' : ''}>10</option>
                        <option value="25" ${this.pageSize === 25 ? 'selected' : ''}>25</option>
                        <option value="50" ${this.pageSize === 50 ? 'selected' : ''}>50</option>
                        <option value="100" ${this.pageSize === 100 ? 'selected' : ''}>100</option>
                    </select>
                </div>
            </div>
        `;
    }

    generatePageNumbers(totalPages) {
        let pages = [];
        const maxVisible = 5;
        let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        
        start = Math.max(1, end - maxVisible + 1);
        
        for (let i = start; i <= end; i++) {
            pages.push(`
                <button class="btn btn-sm ${i === this.currentPage ? 'active' : ''}" 
                        onclick="this.goToPage(${i})">${i}</button>
            `);
        }
        
        return pages.join('');
    }

    generateExportButtons() {
        if (!this.exportEnabled) return '';

        return `
            <div class="export-buttons">
                <button class="btn btn-success" onclick="this.exportToExcel()">
                    💾 ذخیره به Excel
                </button>
                <button class="btn btn-warning" onclick="this.exportToPDF()">
                    📋 ذخیره به PDF
                </button>
                <button class="btn btn-info" onclick="this.exportToCSV()">
                    📄 ذخیره به CSV
                </button>
            </div>
        `;
    }

    autoGenerateColumns() {
        if (this.data.length === 0) return;

        const sample = this.data[0];
        this.columns = Object.keys(sample).map(key => ({
            field: key,
            title: this.formatColumnTitle(key),
            filterable: true,
            sortable: true
        }));
    }

    formatColumnTitle(key) {
        // Convert camelCase or snake_case to readable title
        return key
            .replace(/([A-Z])/g, ' $1')
            .replace(/_/g, ' ')
            .replace(/^./, str => str.toUpperCase())
            .trim();
    }

    formatValue(value, column) {
        if (value === null || value === undefined) return '-';
        
        // Handle numbers with currency formatting
        if (typeof value === 'number') {
            if (column && column.field.includes('amount') || column.field.includes('مبلغ')) {
                return this.formatCurrency(value);
            }
            if (column && column.field.includes('percentage') || column.field.includes('درصد')) {
                return value.toFixed(2) + '%';
            }
            return value.toLocaleString('fa-IR');
        }
        
        // Handle dates
        if (value instanceof Date) {
            return value.toLocaleDateString('fa-IR');
        }
        
        return value.toString();
    }

    formatCurrency(amount) {
        // Format as Rial currency
        return new Intl.NumberFormat('fa-IR', {
            style: 'currency',
            currency: 'IRR',
            minimumFractionDigits: 0
        }).format(amount).replace('ریال', 'ریال');
    }

    applyFilters() {
        this.filteredData = [...this.data];
        
        // Apply text filters
        Object.keys(this.filterConfig).forEach(field => {
            const filterValue = this.filterConfig[field].toLowerCase();
            if (filterValue) {
                this.filteredData = this.filteredData.filter(item => {
                    const value = item[field];
                    return value && value.toString().toLowerCase().includes(filterValue);
                });
            }
        });

        // Apply global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch && globalSearch.value) {
            const searchTerm = globalSearch.value.toLowerCase();
            this.filteredData = this.filteredData.filter(item => {
                return Object.values(item).some(value => 
                    value && value.toString().toLowerCase().includes(searchTerm)
                );
            });
        }

        // Apply sorting
        if (this.sortConfig.field) {
            this.filteredData.sort((a, b) => {
                let aVal = a[this.sortConfig.field];
                let bVal = b[this.sortConfig.field];
                
                if (typeof aVal === 'string') aVal = aVal.toLowerCase();
                if (typeof bVal === 'string') bVal = bVal.toLowerCase();
                
                if (aVal < bVal) return this.sortConfig.direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return this.sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }

        this.currentPage = 1;
        this.renderTable();
        this.updateStats();
    }

    renderTable() {
        const tbody = document.getElementById('table-body');
        if (!tbody) return;

        const startIndex = this.getStartIndex();
        const endIndex = this.getEndIndex();
        const pageData = this.filteredData.slice(startIndex, endIndex);

        tbody.innerHTML = pageData.map((row, index) => `
            <tr class="${index % 2 === 0 ? 'even' : 'odd'}">
                ${this.columns.map(col => `
                    <td class="${this.getCellClass(col, row[col.field])}">
                        ${this.formatValue(row[col.field], col)}
                    </td>
                `).join('')}
            </tr>
        `).join('');

        // Update pagination if enabled
        if (this.paginationEnabled) {
            this.updatePagination();
        }
    }

    getCellClass(column, value) {
        let classes = [];
        
        if (typeof value === 'number') {
            if (value < 0) classes.push('negative');
            if (value > 0) classes.push('positive');
            if (column.field.includes('amount')) classes.push('amount-cell');
        }
        
        return classes.join(' ');
    }

    getStartIndex() {
        return (this.currentPage - 1) * this.pageSize;
    }

    getEndIndex() {
        return Math.min(this.currentPage * this.pageSize, this.filteredData.length);
    }

    updateStats() {
        const recordCount = document.getElementById('record-count');
        const pageInfo = document.getElementById('page-info');
        
        if (recordCount) {
            recordCount.textContent = this.filteredData.length.toLocaleString('fa-IR');
        }
        
        if (pageInfo) {
            const totalPages = Math.ceil(this.filteredData.length / this.pageSize);
            pageInfo.textContent = `${this.currentPage.toLocaleString('fa-IR')} از ${totalPages.toLocaleString('fa-IR')}`;
        }
    }

    updatePagination() {
        const pagination = document.querySelector('.pagination');
        if (pagination) {
            pagination.innerHTML = this.generatePagination();
        }
    }

    // Event handlers
    bindEvents() {
        // Global search
        const searchInput = this.container.querySelector('#global-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.applyFilters();
                }, 300);
            });
        }

        // Search button
        const searchBtn = this.container.querySelector('#search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.applyFilters());
        }

        // Export buttons
        const exportExcelBtn = this.container.querySelector('#export-excel-btn');
        if (exportExcelBtn) {
            exportExcelBtn.addEventListener('click', () => this.exportToExcel());
        }

        const exportPdfBtn = this.container.querySelector('#export-pdf-btn');
        if (exportPdfBtn) {
            exportPdfBtn.addEventListener('click', () => this.exportToPDF());
        }

        const printBtn = this.container.querySelector('#print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printTable());
        }

        // Filter inputs
        this.container.querySelectorAll('.filter-input').forEach(input => {
            input.addEventListener('input', (e) => {
                const field = e.target.id.replace('filter-', '');
                this.updateFilter(field, e.target.value);
            });
        });

        // Sort headers
        this.container.querySelectorAll('th[data-field]').forEach(th => {
            th.addEventListener('click', (e) => {
                const field = e.target.getAttribute('data-field');
                this.sortTable(field);
            });
        });
    }

    updateFilter(field, value) {
        this.filterConfig[field] = value;
        this.applyFilters();
    }

    sortTable(field) {
        if (this.sortConfig.field === field) {
            this.sortConfig.direction = this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortConfig.field = field;
            this.sortConfig.direction = 'asc';
        }
        this.applyFilters();
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.pageSize);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderTable();
            this.updateStats();
        }
    }

    changePageSize(size) {
        this.pageSize = size;
        this.currentPage = 1;
        this.applyFilters();
    }

    clearFilters() {
        this.filterConfig = {};
        document.querySelectorAll('.filter-input').forEach(input => {
            input.value = '';
        });
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) globalSearch.value = '';
        this.applyFilters();
    }

    toggleFilterPanel() {
        const panel = document.querySelector('.filter-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }

    // Export methods
    exportToExcel() {
        // Simple Excel export using table data
        const table = document.getElementById('financial-table');
        const html = table.outerHTML;
        const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.title}_${new Date().toISOString().split('T')[0]}.xls`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    exportToPDF() {
        // Simple PDF export using window.print
        window.print();
    }

    exportToCSV() {
        const headers = this.columns.map(col => `"${col.title}"`).join(',');
        const rows = this.filteredData.map(row => 
            this.columns.map(col => `"${row[col.field] || ''}"`).join(',')
        ).join('\n');
        
        const csv = headers + '\n' + rows;
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.title}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    printTable() {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html dir="rtl">
            <head>
                <title>${this.title}</title>
                <style>
                    body { font-family: Tahoma, sans-serif; margin: 20px; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                    th { background-color: #f5f5f5; }
                    .negative { color: red; }
                    .positive { color: green; }
                    @media print {
                        body { margin: 0; }
                        table { font-size: 12px; }
                    }
                </style>
            </head>
            <body>
                <h2>${this.title}</h2>
                <p>تاریخ تولید: ${new Date().toLocaleDateString('fa-IR')}</p>
                ${document.getElementById('financial-table').outerHTML}
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    // Public methods
    updateData(newData) {
        this.data = newData;
        this.applyFilters();
    }

    updateColumns(newColumns) {
        this.columns = newColumns;
        this.render();
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

// Global initialization function
function initFinancialDataGrid(containerId, options) {
    return new FinancialDataGrid(containerId, options);
}

// Auto-initialize grids with data attributes
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-financial-grid]').forEach(element => {
        const containerId = element.id;
        const dataAttr = element.getAttribute('data-financial-data');
        const options = {
            data: dataAttr ? JSON.parse(dataAttr) : [],
            title: element.getAttribute('data-title') || 'گزارش مالی',
            exportEnabled: element.getAttribute('data-export') !== 'false',
            filterEnabled: element.getAttribute('data-filter') !== 'false',
            paginationEnabled: element.getAttribute('data-pagination') !== 'false',
            pageSize: parseInt(element.getAttribute('data-page-size')) || 50
        };
        
        new FinancialDataGrid(containerId, options);
    });
});
