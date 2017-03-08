import io
import os
import pickle
import threading

import imagehash
from PIL import Image
import requests


def download_and_phash_url(url, name, dataset_dir, target_size=None):
    """
    Downloads an image from it's `url`, calculates it's unique perceptual hash `phash` and saves it to disk (if it
    doesn't already exist).

    :param url: The complete url of the image resource.
    :param name: The name the image should be saved to disc as (usually it's `uuid` as in `image_details`).
    :param dataset_dir: The directory the image should be downloaded and saved to.
    :param target_size: Optional, if given the image will be re-sized s.t. it's aspect ratio is preserved and it's
                        maximum dimension is no larger than `target_size`.
    :return: The image's `phash` on success, else `None`.
    """
    # only download images with allowed extensions
    image_ext_whitelist = ['bmp', 'jpeg', 'jpg', 'png']
    ext = url.split('.')[-1].lower()
    if ext not in image_ext_whitelist:
        ext = ext.split('?')[0]
        if ext not in image_ext_whitelist:
            raise Exception('Unrecognized extension: {} for url: {}.'.format(ext, url))

    image_name = '{}.{}'.format(name, ext)
    image_path = os.path.join(dataset_dir, image_name)

    # if the image already exists don't return
    if os.path.isfile(image_path):
        raise Exception('{} already exists for url: {}.'.format(image_name, url))

    # download the image
    r = requests.get(url, timeout=4.0)
    with Image.open(io.BytesIO(r.content)) as i:
        if target_size:
            # resize the image preserving it's aspect ratio and using the most accurate sampling algorithm
            i.thumbnail(target_size, Image.LANCZOS)

        phash = '{}'.format(imagehash.phash(i))
        if phash:
            i.save(image_path)
            return phash
        else:
            raise Exception('Error calculating phash for url: {}.'.format(url))


def download_and_phash_urls(image_details, dataset_dir):
    """
    Downloads all images in `image_details` that haven't already been downloaded (don't have their `phash` property
    set and don't already exist in `dataset_dir`). Updates `image_details` with the phashes of all downloaded images.

    :param image_details: Dictionary mapping each scraped image's name (a uuid) to it's relevant meta-data.
    :param dataset_dir: The directory the images should be downloaded and saved to, as well as the updated
                        `image_details.pickle`.
    """
    class FetchResource(threading.Thread):
        def __init__(self):
            super().__init__()
            self.image_uuids = []

        def run(self):
            for uuid in self.image_uuids:
                url = image_details.get(uuid).get('image_url')

                # save the downloaded image to disc, with it's `uuid` as the file name
                try:
                    phash = download_and_phash_url(url, uuid, dataset_dir, target_size=(512, 512))
                    image_details.get(uuid)['phash'] = phash
                except Exception as e:
                    print('Failed to download_and_phash_url(): {}.'.format(e))
                    continue

    if not os.path.isdir(dataset_dir):
        os.makedirs(dataset_dir)

    # speed up with multiple threads
    num_threads = 100
    threads = [FetchResource() for _ in range(num_threads)]

    # list of `image_details`'s keys (unique uuids assigned to each image) to download
    image_uuids = []
    for image_uuid, image_detail in image_details.items():
        # if `phash` property is not set we know we haven't downloaded this image yet
        if not image_detail.get('phash'):
            image_uuids.append(image_uuid)

    # split up work into multiple threads
    while image_uuids:
        for t in threads:
            try:
                t.image_uuids.append(image_uuids.pop())
            except IndexError:
                break

    threads = [t for t in threads if t.image_uuids]

    # do work
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # now that we've updated `image_details` with `phash`, update it
    image_details_file_path = os.path.join(dataset_dir, 'image_details.pickle')
    with open(image_details_file_path, 'wb') as handle:
        pickle.dump(image_details, handle, protocol=pickle.HIGHEST_PROTOCOL)
