import shutil
import os
import datetime

SOURCE_DB = 'canteen.db'
BACKUP_DIR = 'backups'

def create_backup():
    if not os.path.exists(SOURCE_DB):
        print(f"Error: Database file '{SOURCE_DB}' not found.")
        return

    # Create backups directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Generate timestamped filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"canteen_backup_{timestamp}.db"
    destination = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copy2(SOURCE_DB, destination)
        print(f"✅ Database backed up successfully!")
        print(f"📍 Location: {os.path.abspath(destination)}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")

if __name__ == "__main__":
    create_backup()
