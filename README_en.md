# 🌌 OrrerySQL

**A Database Developer Tool for SQL Analysis and Visual Query Flow Interpretation**

OrrerySQL is a GUI-based SQL development environment that helps you intuitively analyze and understand complex SQL queries. Like an orrery that shows celestial movements, it visually represents the execution flow of SQL queries.

![OrrerySQL](https://img.shields.io/badge/Language-Python-blue)
![PyQt6](https://img.shields.io/badge/GUI-PySide6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Key Features

### 🔍 **SQL Query Analysis**
- **AST-based Parsing**: Accurate SQL parsing using sqlglot
- **Query Flow Visualization**: Display execution order of SELECT, JOIN, WHERE conditions
- **CTE Analysis**: Interpret complex relationships in WITH clauses and subqueries

### 🎨 **User-Friendly Interface**
- **Dark/Light Themes**: Developer-friendly theme selection
- **Multi-language Support**: Dynamic Korean/English switching
- **SQL Syntax Highlighting**: Keywords, table names, and column highlighting
- **Auto-completion**: IntelliSense based on table and column names

### 🗄️ **Multi-Database Support**
- **DuckDB**: High-performance in-memory analytical database
- **SQLite**: Lightweight file-based database
- **Plugin Architecture**: Extensible database engine support

### 📊 **Result Management**
- **Tab-based Multi-Query**: Work on multiple queries simultaneously
- **Excel Export**: Easy data extraction from query results
- **Wide View**: Extended view for results with many columns

## 🚀 Quick Start

### Installation

#### 1. Download Executable (Recommended)
```bash
# Download the latest OrrerySQL.exe from Releases
# Run directly without any installation
```

#### 2. Run from Source Code
```bash
# Clone repository
git clone https://github.com/your-username/OrrerySQL.git
cd OrrerySQL

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Packaging (For Developers)
```bash
# Create executable using PyInstaller
python build.py

# Or run batch file (Windows)
build.bat
```

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.11+ |
| **GUI Framework** | PySide6 (Qt6) |
| **SQL Parser** | sqlglot |
| **Database** | DuckDB, SQLite |
| **Data Processing** | pandas |
| **Export** | openpyxl |
| **Packaging** | PyInstaller |

## 📁 Project Structure

```
OrrerySQL/
├── 📁 SQLCoreProject/
│   ├── 📁 core/              # SQL Analysis Engine
│   │   ├── SQLInterpreterCore.py
│   │   ├── ASTKeywordsAnalyzer.py
│   │   └── CTEkeywords.py
│   ├── 📁 ui/                # UI Components
│   │   ├── SQLgateUI.py
│   │   ├── SQLtoolbar.py
│   │   └── SQLtabsheet.py
│   ├── 📁 data/              # Data Processing
│   ├── 📁 plugin/            # Plugin System
│   └── 📁 resources/         # Themes, Icons
├── 📁 language/              # Multi-language Support
│   ├── lang.py
│   ├── ko.py
│   └── en.py
├── main.py                   # Application Entry Point
├── requirements.txt          # Dependencies
└── README.md
```

## 🎯 Usage Example

### SQL Query Analysis
```sql
WITH sales_summary AS (
    SELECT 
        customer_id,
        SUM(amount) as total_sales
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_date >= '2024-01-01'
    GROUP BY customer_id
)
SELECT 
    c.customer_name,
    s.total_sales
FROM customers c
JOIN sales_summary s ON c.customer_id = s.customer_id
WHERE s.total_sales > 1000
ORDER BY s.total_sales DESC;
```

**OrrerySQL Analysis Result:**
```
1. CTE 'sales_summary' definition ↓
2. JOIN performed: orders ⟷ order_items  
3. WHERE condition applied: order_date >= '2024-01-01'
4. GROUP BY aggregation: customer_id
5. SUM aggregation function: amount
6. JOIN performed: customers ⟷ sales_summary
7. WHERE condition applied: total_sales > 1000
8. ORDER BY sorting: total_sales DESC
```

## 🔧 Development Philosophy

Adopting **RSU (Responsibility Structural Unit)** methodology:
- Clear separation of responsibilities for each module
- Independent and testable minimal units
- Extensible plugin architecture

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is distributed under the MIT License. See `LICENSE` file for more information.

## 👥 Development Team

- **Main Developer**: [Your Name]
- **SQL Analysis Engine**: Advanced AST parsing with sqlglot
- **UI/UX Design**: Modern dark theme with PySide6

## 🙏 Acknowledgments

- [sqlglot](https://github.com/tobymao/sqlglot) - Powerful SQL parser
- [DuckDB](https://duckdb.org/) - High-performance analytical database
- [PySide6](https://www.qt.io/qt-for-python) - Modern GUI framework

---

**⭐ If this project helped you, please give it a star!** 