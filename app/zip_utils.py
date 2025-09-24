import os
import zipfile
import io

def create_zip_from_directory(directory_path):
    """
    Creates a compressed ZIP file in memory from all the files in a given directory.

    Args:
        directory_path (str): The path to the directory to be zipped.

    Returns:
        bytes: The ZIP file as a bytes object, or None if the directory is empty or doesn't exist.
    """
    if not os.path.isdir(directory_path) or not os.listdir(directory_path):
        return None

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory_path)
                zip_file.write(file_path, arcname=arcname)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()