"""
Backup existing model checkpoints before retraining.
This script moves all checkpoint files to a backup directory with timestamp.
"""
import os
import shutil
from datetime import datetime

def backup_checkpoints():
    """Backup existing checkpoints to a timestamped directory."""
    checkpoints_dir = os.path.join(os.path.dirname(__file__), "checkpoints")
    
    if not os.path.exists(checkpoints_dir):
        print("No checkpoints directory found. Nothing to backup.")
        return
    
    # Count files to backup
    files = [f for f in os.listdir(checkpoints_dir) if f.endswith('.zip') or f.endswith('.pkl')]
    if not files:
        print("No checkpoint files found. Nothing to backup.")
        return
    
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(__file__), f"checkpoints_backup_{timestamp}")
    
    print(f"Creating backup directory: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Move all checkpoint files
    print(f"Backing up {len(files)} files...")
    for filename in files:
        src = os.path.join(checkpoints_dir, filename)
        dst = os.path.join(backup_dir, filename)
        shutil.move(src, dst)
        print(f"  Moved: {filename}")
    
    print(f"\n✅ Backup complete! Files moved to: {backup_dir}")
    print(f"   You can now start fresh training.")
    print(f"\n   To restore: move files from backup directory back to checkpoints/")

if __name__ == "__main__":
    backup_checkpoints()
