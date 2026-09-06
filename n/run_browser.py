import sys
import os
import subprocess

def main():
    python_exe = sys.executable
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    print("Launching MediCart Pharmacy UI in your browser using Python & SQLite...")
    print(f"Using Python: {python_exe}")
    
    try:
        subprocess.run([python_exe, app_path])
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
