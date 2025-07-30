# 🗺️ GeoSurvey - Advanced File Upload & Conversion System

A fully functional Django-based system for uploading, previewing, and converting geospatial files (KML, CSV, Shapefiles) with beautiful UI and comprehensive backend processing.

## ✨ Features

### 🔹 File Upload Module
- **Beautiful Drag & Drop UI** with Tailwind CSS styling
- **Multiple File Type Support**: KML, CSV, Shapefiles (.shp, .shx, .dbf, .prj)
- **Real-time File Validation** with progress indicators
- **File Type Detection** based on extension and content
- **Size and Format Validation** with user-friendly error messages

### 🔹 KML File Processing
- **Interactive Map Preview** using Leaflet.js
- **Dynamic HTML Table** showing selected fields (Name, Description, Coordinates)
- **Full KML Data Preservation** in memory
- **Export Options**:
  - Export to CSV (all fields including hidden)
  - Export to Shapefile (full conversion)

### 🔹 CSV File Processing
- **Complete Data Preview** with pagination
- **Coordinate Validation** (lat/lon or UTM)
- **Interactive Map Display** using detected coordinates
- **Export Options**:
  - Export to KML
  - Export to Shapefile

### 🔹 Shapefile Processing
- **ZIP File Support** containing .shp, .shx, .dbf, .prj
- **Geometry Preview** on interactive map
- **Attribute Table Display** with selected fields
- **Export Options**:
  - Export to CSV (full data)
  - Export to KML

### 🔹 Technical Features
- **Django REST Framework** backend API
- **Beautiful Tailwind CSS** frontend (no React required)
- **Leaflet.js** for interactive map displays
- **Advanced File Processing** using geopandas, shapely, pyshp
- **File Conversion Tracking** and history
- **User Authentication** and file ownership
- **File Sharing** with public/private links
- **Download Statistics** and analytics

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 5.2+
- Required packages (see requirements.txt)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd final
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create superuser**
```bash
python manage.py createsuperuser
```

5. **Start the development server**
```bash
python manage.py runserver
```

6. **Access the application**
- Main application: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
final/
├── account/                 # User authentication app
├── admindashboard/         # Admin dashboard
├── userdashboard/          # Main user dashboard
│   ├── models.py          # Database models
│   ├── views.py           # Main views
│   ├── file_views.py      # File processing views
│   ├── kml_views.py       # KML-specific views
│   ├── file_utils.py      # File processing utilities
│   ├── kml_utils.py       # KML processing utilities
│   └── templates/         # HTML templates
├── geosurvey/             # Main project settings
├── media/                 # Uploaded files
└── requirements.txt       # Python dependencies
```

## 🔧 Core Components

### Models
- **FileUpload**: Main file upload tracking
- **KMLData**: Parsed KML data storage
- **CSVData**: Parsed CSV data storage
- **ShapefileData**: Parsed shapefile data storage
- **FileConversion**: Conversion history tracking
- **FileShare**: File sharing functionality

### Views
- **FileUploadView**: Main file upload interface
- **KMLPreviewView**: KML file preview and export
- **CSVPreviewView**: CSV file preview and export
- **ShapefilePreviewView**: Shapefile preview and export
- **FileListView**: File management interface

### Utilities
- **FileValidator**: Comprehensive file validation
- **FileProcessor**: File processing and parsing
- **FileConverter**: Format conversion utilities

## 🎯 Usage Examples

### Uploading a KML File
1. Navigate to `/dashboard/files/upload/`
2. Drag and drop or select a KML file
3. System validates and processes the file
4. Redirected to KML preview page with interactive map
5. View data in table format
6. Export to CSV or Shapefile

### Uploading a CSV File
1. Upload CSV file with coordinate columns
2. System validates coordinate presence
3. Preview data in paginated table
4. View points on interactive map
5. Export to KML or Shapefile

### Uploading a Shapefile
1. Upload ZIP file containing shapefile components
2. System extracts and processes geometries
3. Preview features on map
4. View attributes in table
5. Export to CSV or KML

## 🛠️ API Endpoints

### File Upload
- `POST /dashboard/files/upload/` - Upload new file
- `GET /dashboard/files/list/` - List user files
- `GET /dashboard/files/<id>/` - File details

### File Preview
- `GET /dashboard/kml/preview/<id>/` - KML preview
- `GET /dashboard/csv-preview/<id>/` - CSV preview
- `GET /dashboard/shapefile-preview/<id>/` - Shapefile preview

### File Export
- `GET /dashboard/files/<id>/export/csv/` - Export to CSV
- `GET /dashboard/files/<id>/export/kml/` - Export to KML
- `GET /dashboard/files/<id>/export/shapefile/` - Export to Shapefile

### File Management
- `POST /dashboard/files/<id>/delete/` - Delete file
- `POST /dashboard/files/<id>/share/` - Create share link
- `GET /dashboard/shared/<token>/` - Access shared file

## 🎨 UI Features

### Beautiful Design
- **Modern Gradient Backgrounds** with animated effects
- **Glass Morphism** design elements
- **Responsive Layout** for all devices
- **Smooth Animations** and transitions
- **Interactive Elements** with hover effects

### User Experience
- **Drag & Drop** file upload
- **Real-time Progress** indicators
- **Loading Spinners** for large files
- **Toast Notifications** for user feedback
- **Intuitive Navigation** between sections

## 🔒 Security Features

- **User Authentication** required for all operations
- **File Ownership** validation
- **Secure File Storage** with proper permissions
- **Input Validation** and sanitization
- **CSRF Protection** on all forms
- **File Type Validation** to prevent malicious uploads

## 📊 File Processing Capabilities

### KML Processing
- Parse complex KML structures
- Extract ExtendedData fields
- Handle multiple geometry types
- Preserve styling information
- Support for time and address data

### CSV Processing
- Automatic coordinate detection
- Support for multiple coordinate systems
- Data type inference
- Missing value handling
- Large file optimization

### Shapefile Processing
- ZIP archive extraction
- Multiple geometry type support
- Attribute field preservation
- Coordinate system detection
- Projection information handling

## 🚀 Performance Optimizations

- **Pagination** for large datasets
- **Lazy Loading** of map features
- **Background Processing** for large files
- **Caching** of processed data
- **Optimized Database Queries**

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions, please open an issue in the repository.

---

**Built with ❤️ using Django, Tailwind CSS, and Leaflet.js** 