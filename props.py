import os


def get_files_from_folder(folder, verbose=False):
    """Retrieve all file paths (relative to the folder) by walking through the folder recursively."""
    files = set()
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            relative_path = os.path.join(root, filename)
            files.add(relative_path)
            if verbose: 
                print('Checking for:', relative_path)
    if verbose:
        print()
    return files

def get_file_info(file_path):
    """Get additional info for the file: symlink target or size."""
    if os.path.islink(file_path):
        # If it's a symlink, show where it points to
        target = os.readlink(file_path)
        return f"symlink -> {target}"
    return ""
    # elif os.path.isfile(file_path):
    #     # If it's a regular file, show its size
    #     size = os.path.getsize(file_path)
    #     return f"regular file, size: {size} bytes"
    # else:
    #     return "unknown type"

def get_files_from_txt(device_folders, duplicate=False):
    """Retrieve all file names listed in the specified text files."""
    files = set()
    for txt_file in device_folders:
        with open(os.path.join(txt_file, "proprietary-files.txt"), 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and commented out lines
                    for word in line.split(";"):
                        w = word.strip()
                        if w.startswith("-"):
                            w = w[1:]
                        if w.startswith("SYMLINK="):
                            w = w[len("SYMLINK="):]
                        
                        if duplicate and w in files:
                            print("Duplicate:", w)

                        files.add(w)
    return files
