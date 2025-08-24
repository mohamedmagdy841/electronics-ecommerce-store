import hashlib, os, time
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError

@deconstructible
class HashedUploadPath:
    def __init__(self, subdir="uploads"):
        self.subdir = subdir

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1].lower()
        # hash includes time to reduce collisions
        hash_name = hashlib.sha256(f"{filename}{time.time()}".encode()).hexdigest()[:20]
        return os.path.join(self.subdir, f"{hash_name}.{ext}")


def validate_image_extension(file):
    valid_extensions = ["jpg", "jpeg", "png", "webp"]
    ext = file.name.split(".")[-1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension: .{ext}. Allowed: {', '.join(valid_extensions)}")

def validate_image_size(file):
    max_size_mb = 2
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image file too large ( > {max_size_mb}MB )")
