import os
import cv2
import urllib.request
from dbpackages import SqlDB


def rescale(img, scale_percent=10):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    new_dimension = (width, height)
    return new_dimension


def read_file(filename):
    with open(filename, 'rb') as f:
        photo = f.read()
    return photo


def main():
    WIDTH = 1
    HEIGHT = 0

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    IMAGE_DIR = os.path.join(BASE_DIR, 'images/')
    RESIZE_DIR = os.path.join(IMAGE_DIR, 'resized/')

    QUERY_INMATE = "SELECT case_id, img_url, img_file FROM inmates"
    QUERY_PHOTOS = "SELECT id FROM photos  WHERE case_id='{}'"
    QUERY_INSERT = "INSERT INTO photos (case_id, image) VALUES (%s, %s)"

    db = SqlDB()

    scale, counter = 25, 0
    rows = db.retrieve(QUERY_INMATE)
    print(f'{len(rows)} SQL records to process...')
    for row in rows:
        case_id, img_url, img_file = row
        if not db.search(QUERY_PHOTOS.format(case_id)):
            counter += 1
            img_name = IMAGE_DIR + img_file
            img_resized = RESIZE_DIR + img_file
            print(f'Downloading {img_url} ...')
            urllib.request.urlretrieve(img_url, img_name)
            img = cv2.imread(img_name, cv2.IMREAD_UNCHANGED)
            original = (img.shape[WIDTH], img.shape[HEIGHT])
            dimension = rescale(img, scale)
            print(f"{original} resizing to {dimension}")
            resized = cv2.resize(img, dimension)
            cv2.imwrite(img_resized, resized)
            photo_blob = read_file(img_resized)
            print(f"Inserting photo for Case Id: {case_id}")
            args = (case_id, photo_blob)
            db.insert(QUERY_INSERT, args, commit=True)
            os.remove(img_name)
            print(f"Removing file {img_name} for record: {counter:0=4}", end="\n\n")

    print(f"{counter} rows processed out of {len(rows)} total.")

    db.shutdown()


if __name__ == "__main__":
    main()