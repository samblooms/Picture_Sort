import exifread
import os
import imghdr
import shutil
import argparse
import datefinder
from datetime import datetime
from pytesseract import image_to_string
import cv2
import numpy as np

# Exract the exif data from the file
def get_exif_data(path):
    f = open(path, 'rb')
    tags = exifread.process_file(f)
    info = str(tags.get('Image DateTime', '0'))
    return info

# parse the date from the exif data into a date string
def parse_date(date):
    return datetime.strptime(date, '%Y:%m:%d %H:%M:%S').date()

# parse the time from the exif data into a time string
def parse_time(date):
    return datetime.strptime(date, '%Y:%m:%d %H:%M:%S').time()

# Take a directory and recursively find all images compatible with exifread
def get_images(path):
    files = []
    for f in os.listdir(path):
        if imghdr.what(f) is not None:
            files.append(f)
    return files

# Take the starting directory and recursively find all images compatible with exifread
def get_images_recursively(path):
    files = []
    for root, dirs, filenames in os.walk(path):
        for f in filenames:
            if imghdr.what(os.path.join(root, f)) is not None:
                files.append(os.path.join(root, f))
    return files
    

# Take argument (directory) and sort all images in that directory by date
def picture_sort(src_dir, dest_dir, recursive, move, verbose, rename, try_timestamp):
    if not os.path.exists(src_dir):
        raise ValueError('The directory provided does not exist')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    if verbose:
        print('Created directory: ' + dest_dir)

    # Count the total number of images found, and the number of images that are changed or skipped
    totalFiles = 0
    files_changed = []
    files_skipped = []
    files_unsorted = []


    # Move or copy the files from the source directory to the destination directory
    if recursive:
        images = get_images_recursively(src_dir)
    else:
        images = get_images(src_dir)
    for f in images:
        totalFiles += 1
        metadata = get_exif_data(f)

        # If the image has no exif data, skip it
        if metadata == '0':
            date_in_name = check_for_date_in_file_name(f)
            if date_in_name is not None:
                if verbose:
                    print('Found date in file name: ' + date_in_name)
                metadata = str(date_in_name)
            elif try_timestamp:
                date_in_stamp = get_time_stamp(f)
                if date_in_stamp is not None:
                    if verbose:
                        print('Found date in timestamp: ' + date_in_stamp)
                    metadata = (str(date_in_stamp))
                else:
                    files_unsorted.append(f)
                    continue
            else:
                if verbose:
                    print('Could not extract date from file: ' + f)
                files_unsorted.append(f)
                continue

        image_date = str(parse_date(metadata))
        image_year = str(parse_date(metadata).year)
        image_month = str(parse_date(metadata).strftime('%B'))
        image_time = str(parse_time(metadata).strftime('(%H:%M:%S)'))
        if not os.path.exists(dest_dir + '/' + image_year):
            os.makedirs(dest_dir + '/' + image_year)
            if verbose:
                print('Created directory: ' + dest_dir + '/' + image_year)
        if not os.path.exists(dest_dir + '/' + image_year + '/' + image_month):
            os.makedirs(dest_dir + '/' + image_year + '/' + image_month)
            if verbose:
                print('Created directory: ' + dest_dir + '/' + image_year + '/' + image_month)


        # Move or copy the image to the destination directory
        file_name, file_ext = os.path.splitext(os.path.basename(f))
        if rename:
            new_file = dest_dir + '/' + image_year + '/' + image_month + '/' + image_date + '_' + image_time  + file_ext
        else:
            new_file = dest_dir + '/' + image_year + '/' + image_month + '/' + file_name + file_ext
        if not os.path.exists(new_file):
            if move:
                if verbose:
                    print('Moving file: ' + file_name + file_ext + ' to ' + new_file)
                files_changed.append(f)
                shutil.move(f, new_file)
            else:
                if verbose:
                    print('Copying file: ' + file_name + file_ext + ' to ' + new_file)
                files_changed.append(f)
                shutil.copy2(f, new_file)
        else:
            if verbose:
                print('File already exists. Skipping...')
            files_skipped.append(f)

    unsorted_dir = dest_dir + '/unsorted'
    if len(files_unsorted) > 0:
        for f in files_unsorted:
            if not os.path.exists(unsorted_dir):
                os.makedirs(unsorted_dir)
            shutil.copy2(f, unsorted_dir)
            
            

    print('')
    print('Total files: ' + str(totalFiles))
    print('Files copied: ' + str(len(files_changed)))
    print('Files skipped: ' + str(len(files_skipped)))
    print('Files unsorted: ' + str(len(files_unsorted)))


def check_for_date_in_file_name(file_name):
    tempFile = os.path.basename(file_name)
    tempFile = tempFile.replace(';', ':', 2)
    matches = datefinder.find_dates(tempFile, strict=True)
    for match in matches:
        if match.day > 0 and match.month > 0 and match.year > 0:
            return match.strftime('%Y:%m:%d %H:%M:%S')
    return None


def parse_time_stamp(string):
    matches = datefinder.find_dates(string, strict=True)
    for match in matches:
        if match.day > 0 and match.month > 0 and match.year > 0:
            return match.strftime('%Y:%m:%d %H:%M:%S')
    return None

def get_time_stamp(path):
    img = cv2.imread(path)

    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Orange Color Range
    lower_val = np.array([5, 50, 50])
    upper_val = np.array([15, 255, 255])

    # Threshold the HSV image to get only Orange colors
    mask = cv2.inRange(hsv, lower_val, upper_val)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(img,img, mask= mask)
    # invert the mask to get orange letters on white background
    res2 = cv2.bitwise_not(mask)

    image_1_date = None
    image_2_date = None
    count = 0
    while image_1_date is None and image_2_date is None and count < 4:
        image_1_data = image_to_string(res, config="--psm 6")
        image_2_data = image_to_string(res2, config="--psm 6")
        res = cv2.rotate(res, cv2.ROTATE_90_CLOCKWISE)
        res2 = cv2.rotate(res2, cv2.ROTATE_90_CLOCKWISE)
        #print("image_1_data: " + image_1_data)
        #print("image_2_data: " + image_2_data)

        image_1_date=parse_time_stamp(image_1_data)
        image_2_date=parse_time_stamp(image_2_data)

        #print(image_1_date)
        #print(image_2_date)
        count += 1
    
    # Print the text from the image
    
    if image_1_date == image_2_date:
        return image_1_date
    elif image_1_date is None and image_2_date is not None:
        return image_2_date
    elif image_1_date is not None and image_2_date is None:
        return image_1_date
    else:
        return None
    

    # display image

# Run the script
def main():
    # Parse user arguments defining the sorting options
    parser = argparse.ArgumentParser(description='Sort a directory of photos by date')
    parser.add_argument('src_dir', type=str, help='The top directory to search for images')
    parser.add_argument('dest_dir', type=str, help='The destination directory to store sorted images')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search for any images in child directories', default=True)
    parser.add_argument('-m', '--move', action='store_true', help='Modify the original files instead of copying them', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='Print image information', default=False)
    parser.add_argument('-rn', '--rename', action='store_true', help='Rename the files to the date they were taken', default=False)
    parser.add_argument('-ts', '--try_timestamp', action='store_true', help='''Try to extract date from datestamp\n\n
    This option uses cv2 to isolate the timestamp and read the date.\n
    As a result, it is still extremely slow, and extremely experimental.\n\n
    *** It is HIGHLY recommended to sort your images by date first,
    then run this option on the unsorted directory.***''', default=False)
    picture_sort(**vars(parser.parse_args()))


    
# Call the main function
if __name__ == '__main__':
    main()
