import os, zipfile, datetime
project_dir = r'C:\Users\Shane moin\OneDrive\Desktop\AK PROJECT'
zip_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
zip_path = os.path.join(os.getenv('TEMP'), zip_name)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            # skip the backup script itself if present
            if file == 'backup_script.py':
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            zipf.write(file_path, rel_path)
print('Backup created at', zip_path)
