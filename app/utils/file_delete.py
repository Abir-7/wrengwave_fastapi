import os

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def delete_file(file_url: str) -> bool:
    """
    Delete a file from uploads using its URL path.
    Example input: /uploads/images/abc.jpg
    """
    if not file_url:
        return False

    # remove leading /uploads/
    if file_url.startswith("/uploads/"):
        relative_path = file_url[len("/uploads/"):]
    else:
        relative_path = file_url

    file_path = os.path.join(UPLOAD_ROOT, relative_path)
    file_path = os.path.normpath(file_path)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True

    return False