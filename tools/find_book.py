import os
import glob

book_dir = r"C:\Users\gai\Downloads\书"
epub_files = glob.glob(os.path.join(book_dir, "*.epub"))

for f in epub_files:
    if "穷查理" in f:
        print(f"PATH: {f}")
        print(f"EXISTS: {os.path.exists(f)}")
