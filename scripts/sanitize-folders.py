import os
import shutil


if __name__ == '__main__':
    # foreach json file open it and check if files exist
    for dirpath, dirnames, filenames in os.walk("mp3", topdown=False):
        try:
            for dirname in dirnames:
                # Check if the directory name matches the target_name
                if dirname == "entree":
                    full_dir_path = os.path.join(dirpath, dirname)
                    new_full_dir_path = os.path.join(dirpath, "in")
                    # Rename folder to match the norm
                    shutil.move(full_dir_path, new_full_dir_path)
                    print(f"Renamed '{full_dir_path}' to '{new_full_dir_path}'")
                if dirname == "sortie":
                    full_dir_path = os.path.join(dirpath, dirname)
                    new_full_dir_path = os.path.join(dirpath, "out")
                    # Rename folder to match the norm
                    shutil.move(full_dir_path, new_full_dir_path)
                    print(f"Renamed '{full_dir_path}' to '{new_full_dir_path}'")
        except Exception as e:
            print(f"Random Exeption:\n{e}")
