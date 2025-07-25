# CIHR Projects Tracker (CIHRPT)

A comprehensive web application for tracking and analyzing Canadian Institutes of Health Research (CIHR) funded projects. Part of the XeraDB suite of research transparency tools.

## 🚀 Features

- **Comprehensive Project Database**: 300+ CIHR-funded research projects with detailed metadata
- **Advanced Search & Filtering**: Search by title, investigators, keywords, study type, therapeutic area, institution, and more
- **Beautiful Visualizations**: Interactive charts and statistics dashboards
- **Project Detail Pages**: Shows only relevant research characteristics ("yes" fields)
- **REST API**: Full programmatic access to project data
- **Canadian Theme**: Maple red color scheme representing Canadian excellence in health research
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## 🎯 Key Capabilities

### Research Characteristics Tracking
- Study types (trials, observational, evidence synthesis, other)
- Technology adoption (AI/ML, digital health, telemedicine, big data)
- Implementation science and knowledge translation
- Patient engagement and community-based research
- International and indigenous collaboration
- Health equity and social determinants
- And 80+ other research characteristics

### Data Sources
- **JSON Analysis Files**: AI-generated analysis of project characteristics
- **CSV Metadata**: Original CIHR project information including funding, institutions, investigators

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- Node.js (for Chart.js dependencies)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/choxos/CIHRPT.git
cd CIHRPT
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run database migrations:
```bash
python manage.py migrate
```

4. Import CIHR project data:
```bash
python manage.py import_cihr_data
```

5. Collect static files:
```bash
python manage.py collectstatic
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Visit `http://127.0.0.1:8000` to view the application

## 📊 Data Structure

### JSON Analysis Files (`cihr_projects_jsons/`)
Each project has a corresponding JSON file with AI-analyzed characteristics:
- Study design classification
- Technology and innovation markers
- Implementation science indicators
- Collaboration and engagement metrics
- Health economics features
- Statistical methodology markers

### CSV Metadata (`cihr_projects.csv`)
Original CIHR data including:
- Project identifiers and titles
- Principal investigators and institutions
- Funding amounts and competition details
- Research themes and keywords
- Abstract summaries

## 🔧 Management Commands

### Import Data
```bash
# Import all available projects
python manage.py import_cihr_data

# Import limited number for testing
python manage.py import_cihr_data --limit 50

# Specify custom paths
python manage.py import_cihr_data --json-dir /path/to/jsons --csv-file /path/to/csv
```

## 🌐 API Endpoints

### REST API
- `GET /api/projects/` - List all projects with filtering
- `GET /api/projects/{id}/` - Get specific project details
- `GET /api/projects/{id}/yes_fields/` - Get only "yes" characteristics
- `GET /api/projects/statistics/` - Get summary statistics

### Search Parameters
- `search` - Full-text search across titles, abstracts, keywords
- `broad_study_type` - Filter by study type
- `therapeutic_area` - Filter by therapeutic area
- `primary_institute` - Filter by CIHR institute
- `primary_theme` - Filter by research theme

### Example API Calls
```bash
# Search for AI-related projects
curl "http://localhost:8000/api/projects/?search=artificial+intelligence"

# Get projects by therapeutic area
curl "http://localhost:8000/api/projects/?therapeutic_area=cancer"

# Get projects with patient engagement
curl "http://localhost:8000/api/projects/?patient_engagement=yes"
```

## 🎨 Theme Integration

CIHRPT uses the XeraDB unified theme system with Canadian-specific styling:
- **Primary Color**: Maple Red (#dc2626) 
- **Typography**: Inter font family
- **Icons**: Font Awesome 6
- **Charts**: Chart.js with custom Canadian color palette
- **Responsive**: Bootstrap 5 grid system

## 📁 Project Structure

```
CIHRPT/
├── cihrpt_project/          # Django project settings
├── tracker/                 # Main application
│   ├── models.py           # Database models
│   ├── views.py            # Web views and API viewsets
│   ├── urls.py             # URL routing
│   ├── serializers.py      # REST API serializers
│   └── management/         # Custom management commands
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── xera_base.html     # XeraDB unified base
│   └── tracker/           # App-specific templates
├── static/                # Static files (CSS, JS, images)
├── cihr_projects_jsons/   # Project analysis data
├── cihr_projects.csv      # Project metadata
├── db.sqlite3            # SQLite database
└── requirements.txt      # Python dependencies
```

## 🚀 Deployment

### Production Settings
1. Update `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure proper database (PostgreSQL recommended)
4. Set up static file serving
5. Configure allowed hosts

### Environment Variables
```bash
export DJANGO_SECRET_KEY="your-secret-key"
export DJANGO_DEBUG=False
export DATABASE_URL="postgresql://..."
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📈 Statistics

- **300+ Projects**: Comprehensive coverage of CIHR-funded research
- **80+ Research Characteristics**: Detailed analysis of project features
- **Multiple Study Types**: Trials, observational studies, evidence synthesis, and more
- **10+ CIHR Institutes**: Coverage across all major Canadian health research institutes
- **Interactive Visualizations**: Charts, graphs, and statistical dashboards

## 🔗 Related Projects

Part of the XeraDB suite:
- **OST**: Open Science Tracker
- **PRCT**: Post-Retraction Citation Tracker
- **NIHRPT**: NIHR Projects Tracker (UK)
- **NIHPT**: NIH Projects Tracker (US)
- **NHMRCPT**: NHMRC Projects Tracker (Australia)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Dr. Ahmad Sofi-Mahmudi**
- Email: ahmad.pub@gmail.com
- GitHub: [@choxos](https://github.com/choxos)
- LinkedIn: [asofimahmudi](https://linkedin.com/in/asofimahmudi)
- X: [@ASofiMahmudi](https://x.com/ASofiMahmudi)

Meta-researcher in Open Science and creator of XeraDB research transparency tools.

## 🙏 Acknowledgments

- Canadian Institutes of Health Research (CIHR) for funding transparency
- XeraDB community for theme and framework contributions
- Open science research community for inspiration and feedback

---

**CIHRPT** - Advancing transparency in Canadian health research funding 🇨🇦 