import os
from pathlib import Path
from shutil import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CATEGORIES_DIR = os.path.join(BASE_DIR, 'LCIA method', 'categories')


def dummy_copy_categories():
    """
    Copy the categories csv file from the folder LCIA method/categories, into each right method folder
    No matter if the file already exist
    """
    categories_files = os.listdir(CATEGORIES_DIR)
    for filename in categories_files:
        try:
            split_tab = filename.split(" + ")
            if (len(split_tab) < 2):
                raise SyntaxError(
                    filename + " does not contains an impact method.\n" +
                    "It should have an impact category and an impact method separated by a +")
            split_tab.pop(0)  # We remove the category name
            # We get the impact method name
            method_folder_name = " + ".join(split_tab).removesuffix(".csv").rstrip(' ')
            source_path = os.path.join(CATEGORIES_DIR, filename)
            destination_path = os.path.join(BASE_DIR, 'LCIA method', method_folder_name)
            if (not Path(destination_path).is_dir()):
                # We create the method folder if it does not already exist
                os.mkdir(destination_path)
            copy(source_path, destination_path)
        except SyntaxError:
            pass  # The file has a wrong filename
        except Exception as e:
            print(e.with_traceback())


if __name__ == "__main__":
    dummy_copy_categories()
