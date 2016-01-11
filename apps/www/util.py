import glob
import os
import random


class ImageManager(object):

    _image_names = None

    def __init__(self):
        self._image_names = []

    def add_image(self, nm):
        self._image_names.append(nm)

    def get_random_image(self):
        if self._image_names is None or len(self._image_names) == 0:
            return None
        n = len(self._image_names)
        i = random.randint(0, 50000) % n
        return self._image_names[i]

    @property
    def image_count(self):
        if self._image_names is None:
            return 0
        return len(self._image_names)


class FileBasedImageManager(ImageManager):

    def __init__(self, src_path, mask):
        super(FileBasedImageManager, self).__init__()
        self.load_from(src_path, mask)

    def load_from(self, src_path, mask):
        s = os.path.join(src_path, mask)
        lst = glob.glob(s)
        for f in lst:
            self.add_image(os.path.basename(f))