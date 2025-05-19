# Deployment Guide for Stock Management System

## Local Development Setup

### Prerequisites
- Python 3.9+
- Git
- pip

### Steps to Run Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/Revenage97/rascatv2.git
   cd rascatv2
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Access the application at http://localhost:8000

## GitHub Setup

1. Create a repository on GitHub

2. Push your local repository:
   ```bash
   git remote add origin https://github.com/yourusername/yourrepository.git
   git branch -M main
   git push -u origin main
   ```

## Render.com Deployment

### Prerequisites
- A Render.com account
- Your project on GitHub

### Deployment Steps

1. Log in to your Render.com account

2. Click "New" and select "Web Service"

3. Connect your GitHub repository

4. Configure the service:
   - **Name**: Choose a name (e.g., rascatv3)
   - **Environment**: Python
   - **Region**: Choose the closest to your users
   - **Branch**: main (or your preferred branch)
   - **Build Command**: Will be automatically set from render.yaml
   - **Start Command**: Will be automatically set from render.yaml

5. Add Environment Variables:
   - **DATABASE_URL**: This will be automatically set by Render if you use their PostgreSQL service
   - Other variables will be set from render.yaml

6. Add Disk:
   - This is configured in render.yaml
   - Ensure the disk is mounted at `/opt/render/project/data`
   - Recommended size: 1GB (can be increased later)

7. Click "Create Web Service"

### Using render.yaml (Recommended)

The project includes a `render.yaml` file that automates most of the configuration:

```yaml
services:
  - type: web
    name: rascatv3
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn stock_management.wsgi
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
      - key: RENDER
        value: true
      - key: DEBUG
        value: false
    disk:
      name: data
      mountPath: /opt/render/project/data
      sizeGB: 1
```

With this file, you can use Render's "Blueprint" feature for even easier deployment:

1. Go to Render Dashboard
2. Click "New" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the render.yaml file and configure everything

## Application Usage Guide

### Login
- Use the credentials you created with the superuser command
- Or use the default admin account if provided

### Upload File Excel
1. Navigate to "Upload File" in the sidebar
2. Click "Choose File" and select your Excel file
3. Click "Upload"
4. The system will process the file and update inventory items

### Backup File Excel
1. Navigate to "Backup File" in the sidebar
2. View the history of uploaded files
3. Click "Download" to download any file in the history
4. Click "Download Backup Terbaru" to create and download a new backup

### Kirim ke Telegram
1. On the Dashboard, select items using checkboxes
2. Click "Kirim ke Telegram"
3. The system will send the selected items to Telegram via webhook

### Log Aktivitas
1. Navigate to "Log Aktivitas" in the sidebar
2. View all system activities for the last 7 days

### Edit Webhook
1. Navigate to "Pengaturan Webhook" in the sidebar
2. Enter your Zapier webhook URL
3. Click "Simpan"

## Troubleshooting

### Database Migration Issues
If you encounter database errors like "relation does not exist":

1. Connect to Render Shell:
   - Go to your web service in Render
   - Click on "Shell" tab
   - Run: `python manage.py migrate`

2. If the issue persists, you may need to reset migrations:
   - In the Shell, run:
     ```sql
     python manage.py dbshell
     DELETE FROM django_migrations WHERE app = 'inventory';
     \q
     ```
   - Then run migrations again:
     ```
     python manage.py migrate
     ```

### File Upload/Backup Issues
If files are not being saved or accessed correctly:

1. Ensure the disk is properly mounted:
   - In Render Shell, run: `ls -la /opt/render/project/data`
   - You should see the media directory

2. Check permissions:
   - In Render Shell, run: `chmod -R 755 /opt/render/project/data`

### Other Issues
For any other issues, check the application logs in Render Dashboard under the "Logs" tab.
