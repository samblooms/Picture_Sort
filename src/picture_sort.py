import exifread
import os
import imghdr
import shutil
import argparse
import datefinder
from datetime import datetime

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
def picture_sort(src_dir, dest_dir, recursive, move, verbose, rename):
    if not os.path.exists(src_dir):
        raise ValueError('The directory provided does not exist')

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
            name_in_date = check_for_date_in_file_name(f)
            if name_in_date is not None:
                metadata = str(name_in_date)
            else:
                files_unsorted.append(f)
                continue

        image_date = str(parse_date(metadata))
        image_year = str(parse_date(metadata).year)
        image_month = str(parse_date(metadata).strftime('%B'))
        image_time = str(parse_time(metadata).strftime('(%H:%M:%S)'))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            if verbose:
                print('Created directory: ' + dest_dir)
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
                shutil.move(f, new_file)
                files_changed.append(f)
            else:
                if verbose:
                    print('Copying file: ' + file_name + file_ext + ' to ' + new_file)
                shutil.copy2(f, new_file)
                files_changed.append(f)
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
    #replace any ';' between two two digit numbers with a ':'
    tempFile = tempFile.replace(';', ':', 2)
    matches = datefinder.find_dates(tempFile, strict=True)
    for match in matches:
        if match.day > 0 and match.month > 0 and match.year > 0:
            return match.strftime('%Y:%m:%d %H:%M:%S')
    return None

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
    picture_sort(**vars(parser.parse_args()))


    
# Call the main function
if __name__ == '__main__':
    main()
