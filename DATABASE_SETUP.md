# Database Setup Guide for GeoSurveyPro

## 🚀 Quick Setup Options

### Option 1: Automated Setup (Recommended)
Run the automated setup script:
```bash
python setup_database.py
```

### Option 2: Manual Setup

## 📋 Prerequisites

### For MySQL:
1. Install MySQL Server
2. Install MySQL dependencies:
```bash
pip install mysqlclient PyMySQL
```

### For PostgreSQL:
1. Install PostgreSQL Server
2. Install PostgreSQL dependencies:
```bash
pip install psycopg2-binary
```

## 🔧 Configuration

### 1. Environment Variables
Create a `.env` file in your project root:

```env
# Database Configuration
DATABASE_TYPE=mysql  # or postgresql or sqlite

# MySQL Configuration
DB_NAME=geosurvey_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# PostgreSQL Configuration
# DB_NAME=geosurvey_db
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
```

### 2. Database Creation

#### MySQL:
```sql
CREATE DATABASE geosurvey_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### PostgreSQL:
```sql
CREATE DATABASE geosurvey_db;
```

## 🚀 Migration Steps

### 1. Backup Current Data (if using SQLite)
```bash
cp db.sqlite3 db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Test the Setup
```bash
python manage.py runserver
```

## 🔍 Troubleshooting

### Common Issues:

1. **MySQL Connection Error**:
   - Check if MySQL service is running
   - Verify username/password
   - Ensure database exists

2. **PostgreSQL Connection Error**:
   - Check if PostgreSQL service is running
   - Verify username/password
   - Ensure database exists

3. **Migration Errors**:
   - Delete all migration files (except __init__.py)
   - Run `python manage.py makemigrations` again
   - Run `python manage.py migrate`

## 📊 Database Comparison

| Feature | SQLite | MySQL | PostgreSQL |
|---------|--------|-------|------------|
| Performance | Good | Excellent | Excellent |
| Geospatial Support | Limited | Good | Excellent |
| Scalability | Limited | Good | Excellent |
| Setup Complexity | Easy | Medium | Medium |
| Production Ready | No | Yes | Yes |

## 🎯 Recommendations

- **Development**: Use SQLite (current setup)
- **Production**: Use PostgreSQL (best for geospatial data)
- **Alternative**: Use MySQL (good balance)

## 🔄 Switching Between Databases

To switch databases:

1. Update environment variables
2. Run migrations
3. Restart the server

```bash
# Example: Switch to MySQL
export DATABASE_TYPE=mysql
export DB_NAME=geosurvey_db
export DB_USER=root
export DB_PASSWORD=your_password
python manage.py migrate
python manage.py runserver
``` 