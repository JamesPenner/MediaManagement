import os
import cv2
import hashlib
import csv
from imagehash import average_hash
from PIL import Image

import sys
sys.path.append(r'C:\Users\Windows\Dropbox\James\Python\01_Media Archive Scripts')
from file_handler import FileHandler
from config import video_files

fh = FileHandler()

folder_path1 = r"D:\0_Media-Archive\01_sort"
folder_path2 = r"D:\0_Media-Archive\03_archive\static-archive\Videos"

video_files1 = fh.retrieve_file_list(folder_path1, recursive=True, filter_extensions=video_files, include_metadata=False, validate_filename=False, filename_validation_report=None)
video_files2 = fh.retrieve_file_list(folder_path2, recursive=True, filter_extensions=video_files, include_metadata=False, validate_filename=False, filename_validation_report=None)

def perceptual_hash_frame(frame):
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Convert OpenCV frame to PIL format
    return average_hash(pil_image)

def calculate_md5(file_path):
    with open(file_path, 'rb') as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(4096):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def extract_frames(video_path, num_frames_to_extract):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_positions = [int(pos * total_frames / num_frames_to_extract) for pos in range(num_frames_to_extract)]
    frames = []

    for pos in frame_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to read frame at position {pos} from video: {video_path}")
            break
        frames.append(frame)

    cap.release()
    return frames

def calculate_video_similarity(video_path1, video_path2, num_frames_to_extract):
    frames1 = extract_frames(video_path1, num_frames_to_extract)
    frames2 = extract_frames(video_path2, num_frames_to_extract)
    
    if not frames1 or not frames2:
        return None

    similarity_sum = 0.0
    for frame1, frame2 in zip(frames1, frames2):
        hash1 = perceptual_hash_frame(frame1)
        hash2 = perceptual_hash_frame(frame2)
        similarity = 1.0 - (hash1 - hash2) / len(hash1.hash) ** 2
        similarity_sum += similarity

    average_similarity = similarity_sum / num_frames_to_extract
    similarity_percentage = average_similarity * 100.0
    return similarity_percentage

def process_video_files_within_list(video_files, csv_filename, num_frames_to_extract, similarity_threshold=80):
    if not video_files:
        print("No video files provided.")
        return

    duplicate_groups = {}
    group_id = 0
    processed_pairs = set()

    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['FullFilePath', 'Filename', 'FileExtension', 'PerceptualHash', 'MD5Hash', 'FileSize', 'CreationDate', 'SimilarityPercentage', 'DuplicateGroup']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, video_path1 in enumerate(video_files):
            if any(video_path1 in group for group in duplicate_groups.values()):
                continue

            file_data = {
                'FullFilePath': video_path1,
                'Filename': os.path.basename(video_path1),
                'FileExtension': os.path.splitext(video_path1)[1],
                'MD5Hash': calculate_md5(video_path1),
                'FileSize': os.path.getsize(video_path1),
                'CreationDate': os.path.getctime(video_path1),
                'DuplicateGroup': None
            }
            frames1 = extract_frames(video_path1, num_frames_to_extract)
            if not frames1:
                continue
            file_data['PerceptualHash'] = str([str(perceptual_hash_frame(frame)) for frame in frames1])
            similar_videos = []

            for j, video_path2 in enumerate(video_files):
                if i >= j:
                    continue
                pair = tuple(sorted([video_path1, video_path2]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                similarity_percentage = calculate_video_similarity(video_path1, video_path2, num_frames_to_extract)
                if similarity_percentage is not None and similarity_percentage >= similarity_threshold:
                    similar_videos.append((video_path2, similarity_percentage))
                    print(f"Similarity between {video_path1} and {video_path2}: {similarity_percentage:.2f}%")

            if similar_videos:
                if file_data['DuplicateGroup'] is None:
                    group_id += 1
                    file_data['DuplicateGroup'] = group_id
                    duplicate_groups[group_id] = [video_path1]
                else:
                    group_id = file_data['DuplicateGroup']
                writer.writerow(file_data)

                for similar_video, similarity_percentage in similar_videos:
                    similar_file_data = {
                        'FullFilePath': similar_video,
                        'Filename': os.path.basename(similar_video),
                        'FileExtension': os.path.splitext(similar_video)[1],
                        'MD5Hash': calculate_md5(similar_video),
                        'FileSize': os.path.getsize(similar_video),
                        'CreationDate': os.path.getctime(similar_video),
                        'PerceptualHash': str([str(perceptual_hash_frame(frame)) for frame in extract_frames(similar_video, num_frames_to_extract)]),
                        'SimilarityPercentage': similarity_percentage,
                        'DuplicateGroup': file_data['DuplicateGroup']
                    }
                    duplicate_groups[group_id].append(similar_video)
                    writer.writerow(similar_file_data)
            else:
                file_data['SimilarityPercentage'] = 0.0
                writer.writerow(file_data)

    print("CSV file generation completed.")


def process_video_files_between_lists(video_files1, video_files2, csv_filename, num_frames_to_extract, similarity_threshold=80):
    if not video_files1 or not video_files2:
        print("One or more video file lists are empty.")
        return

    print(f"Processing {len(video_files1)} video files from list 1 and {len(video_files2)} video files from list 2...")

    duplicate_groups = {}
    group_id = 1  # Starting group ID

    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['FullFilePath', 'Filename', 'FileExtension', 'PerceptualHash', 'MD5Hash', 'FileSize', 'CreationDate', 'SimilarityPercentage', 'DuplicateGroup']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Process video files from list 1
        for video_path1 in video_files1:
            print(f"Processing video file: {video_path1}")
            file_data = {
                'FullFilePath': video_path1,
                'Filename': os.path.basename(video_path1),
                'FileExtension': os.path.splitext(video_path1)[1],
                'MD5Hash': calculate_md5(video_path1),
                'FileSize': os.path.getsize(video_path1),
                'CreationDate': os.path.getctime(video_path1),
                'DuplicateGroup': group_id
            }
            frames1 = extract_frames(video_path1, num_frames_to_extract)
            if not frames1:
                print(f"Skipping {video_path1} due to extraction error.")
                continue
            file_data['PerceptualHash'] = str([str(perceptual_hash_frame(frame)) for frame in frames1])

            # Write data for video_path1
            writer.writerow(file_data)
            duplicate_groups[video_path1] = group_id
            print(f"Processed video file: {video_path1}")

        # Process video files from list 2
        for video_path2 in video_files2:
            if video_path2 in duplicate_groups:
                print(f"Skipping {video_path2} as it's already processed.")
                continue  # Skip if video_path2 is already processed and grouped

            print(f"Processing video file: {video_path2}")
            file_data = {
                'FullFilePath': video_path2,
                'Filename': os.path.basename(video_path2),
                'FileExtension': os.path.splitext(video_path2)[1],
                'MD5Hash': calculate_md5(video_path2),
                'FileSize': os.path.getsize(video_path2),
                'CreationDate': os.path.getctime(video_path2),
                'DuplicateGroup': group_id
            }
            frames2 = extract_frames(video_path2, num_frames_to_extract)
            if not frames2:
                print(f"Skipping {video_path2} due to extraction error.")
                continue
            file_data['PerceptualHash'] = str([str(perceptual_hash_frame(frame)) for frame in frames2])

            # Write data for video_path2
            writer.writerow(file_data)
            duplicate_groups[video_path2] = group_id
            print(f"Processed video file: {video_path2}")

    print("CSV file generation completed.")



num_frames_to_extract = 10
csv_filename = r"d:\all_files_attributes.csv"

# process_video_files(video_files, csv_filename, num_frames_to_extract, similarity_threshold=80)

process_video_files_between_lists(video_files1, video_files2, csv_filename, num_frames_to_extract, similarity_threshold=80)







































# import os
# import cv2
# import hashlib
# import csv
# from imagehash import average_hash
# from PIL import Image

# def perceptual_hash_frame(frame):
#     # Convert the frame (numpy array) to PIL Image
#     pil_image = Image.fromarray(frame)
    
#     # Compute perceptual hash using average hash method
#     hash_value = average_hash(pil_image)
    
#     return str(hash_value)

# def perceptual_hash_similarity(hash1, hash2):
#     # Convert hash strings to integers (considering they are hex strings)
#     int_hash1 = int(hash1, 16)
#     int_hash2 = int(hash2, 16)

#     # Calculate similarity as a percentage
#     similarity = 1.0 - (bin(int_hash1 ^ int_hash2).count('1') / 64)  # Assuming average hash size is 64 bits (8 bytes)

#     return similarity


# def calculate_video_similarity(video_path1, video_path2, num_frames_to_extract):
#     cap1 = cv2.VideoCapture(video_path1)
#     cap2 = cv2.VideoCapture(video_path2)

#     similarity_sum = 0.0
#     frame_count = 0

#     fps1 = cap1.get(cv2.CAP_PROP_FPS)
#     fps2 = cap2.get(cv2.CAP_PROP_FPS)

#     # Calculate total number of frames in each video
#     total_frames1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
#     total_frames2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))

#     # Calculate positions to extract frames
#     frame_positions1 = [int(pos * total_frames1 / num_frames_to_extract) for pos in range(num_frames_to_extract)]
#     frame_positions2 = [int(pos * total_frames2 / num_frames_to_extract) for pos in range(num_frames_to_extract)]

#     for pos1, pos2 in zip(frame_positions1, frame_positions2):
#         # Set frame position and read frame
#         cap1.set(cv2.CAP_PROP_POS_FRAMES, pos1)
#         cap2.set(cv2.CAP_PROP_POS_FRAMES, pos2)

#         ret1, frame1 = cap1.read()
#         ret2, frame2 = cap2.read()

#         if not ret1 or not ret2:
#             break

#         hash1 = perceptual_hash_frame(frame1)
#         hash2 = perceptual_hash_frame(frame2)

#         similarity = perceptual_hash_similarity(hash1, hash2)
#         similarity_sum += similarity

#         frame_count += 1

#         # Debug output
#         print(f"Frame positions: {pos1}, {pos2}")
#         print(f"Similarity between frames: {similarity}")

#     cap1.release()
#     cap2.release()

#     if frame_count > 0:
#         average_similarity = similarity_sum / frame_count
#         similarity_percentage = average_similarity * 100.0
#     else:
#         similarity_percentage = 0.0

#     print(f"Average similarity percentage: {similarity_percentage}")

#     return similarity_percentage

# def process_videos_within_folder(directory, output_csv, search_subfolders=False, similarity_threshold=80):
#     with open(output_csv, 'w', newline='') as csvfile:
#         fieldnames = ['Video1', 'Video2', 'SimilarityPercentage']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()

#         total_videos = 0
#         for root, _, files in os.walk(directory):
#             total_videos += len(files)

#         processed_videos = 0

#         for root, _, files in os.walk(directory):
#             for i, video_file1 in enumerate(files):
#                 video_path1 = os.path.join(root, video_file1)
                
#                 for j, video_file2 in enumerate(files):
#                     if i >= j:
#                         continue  # Avoid duplicate comparisons and self-comparison
                    
#                     video_path2 = os.path.join(root, video_file2)
#                     similarity_percentage = calculate_video_similarity(video_path1, video_path2, 3)
                    
#                     if similarity_percentage >= similarity_threshold:
#                         writer.writerow({
#                             'Video1': video_path1,
#                             'Video2': video_path2,
#                             'SimilarityPercentage': similarity_percentage
#                         })

#                 processed_videos += 1
#                 print(f"Progress: {processed_videos}/{total_videos} videos processed", end='\r')

#         print(f"\nVideo similarity results saved to '{output_csv}'.")

# def process_videos_between_folders(directory1, directory2, output_csv):
#     with open(output_csv, 'w', newline='') as csvfile:
#         fieldnames = ['Video1', 'Video2', 'SimilarityPercentage']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()

#         for root1, _, files1 in os.walk(directory1):
#             for video_file1 in files1:
#                 video_path1 = os.path.join(root1, video_file1)
                
#                 for root2, _, files2 in os.walk(directory2):
#                     for video_file2 in files2:
#                         video_path2 = os.path.join(root2, video_file2)
#                         similarity_percentage = calculate_video_similarity(video_path1, video_path2, 3)
                        
#                         if similarity_percentage >= similarity_threshold:
#                             writer.writerow({
#                                 'Video1': video_path1,
#                                 'Video2': video_path2,
#                                 'SimilarityPercentage': similarity_percentage
#                             })

# def perceptual_hash(image_path):
#     image = cv2.imread(image_path)
#     if image is None:
#         print(f"Failed to read image: {image_path}")
#         return None
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     pil_image = Image.fromarray(image)
#     image_hash = average_hash(pil_image)
#     return image_hash

# def perceptual_hash_video(video_path):
#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         print(f"Failed to open video: {video_path}")
#         return None
#     success, frame = cap.read()
#     if not success:
#         print(f"Failed to read frame from video: {video_path}")
#         return None
#     cap.release()
#     image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     pil_image = Image.fromarray(image)
#     image_hash = average_hash(pil_image)
#     return image_hash

# def calculate_md5(file_path):
#     try:
#         with open(file_path, 'rb') as f:
#             md5_hash = hashlib.md5()
#             while chunk := f.read(4096):
#                 md5_hash.update(chunk)
#         return md5_hash.hexdigest()
#     except Exception as e:
#         print(f"Error calculating MD5 for {file_path}: {e}")
#         return None

# def calculate_similarity(hash1, hash2):
#     if hash1 is None or hash2 is None:
#         return 0.0
#     max_distance = len(hash1.hash) ** 2
#     hamming_distance = (hash1 - hash2)
#     similarity_percentage = (1 - (hamming_distance / max_distance)) * 100
#     return similarity_percentage

# def get_file_type(file_extension):
#     image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
#     video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
#     if file_extension in image_extensions:
#         return 'Image'
#     elif file_extension in video_extensions:
#         return 'Video'
#     else:
#         return 'Other'

# def generate_csv(directory, csv_filename, include_subfolders=False):
#     hash_dict = {}
#     duplicate_files = []
#     group_counter = 1
#     file_to_group = {}

#     if include_subfolders:
#         total_files = sum(len(files) for _, _, files in os.walk(directory))
#     else:
#         total_files = len(next(os.walk(directory))[2])
#     processed_files = 0

#     with open(csv_filename, 'w', newline='') as csvfile:
#         fieldnames = ['Filename', 'FileExtension', 'FileType', 'PerceptualHash', 'MD5Hash', 'FileSize', 'CreationDate', 'SimilarityPercentage', 'DuplicateGroup']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()

#         if include_subfolders:
#             file_generator = os.walk(directory)
#         else:
#             file_generator = [(directory, [], next(os.walk(directory))[2])]

#         for root, _, files in file_generator:
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 file_extension = os.path.splitext(file)[1].lower()
#                 file_type = get_file_type(file_extension)
#                 try:
#                     if file_type == 'Image':
#                         perceptual_hash_value = perceptual_hash(file_path)
#                     elif file_type == 'Video':
#                         perceptual_hash_value = perceptual_hash_video(file_path)
#                     else:
#                         print(f"Unsupported file type: {file_path}")
#                         continue

#                     if perceptual_hash_value is None:
#                         print(f"Skipping file due to perceptual hash error: {file_path}")
#                         continue
                    
#                     md5_hash = calculate_md5(file_path)
#                     if md5_hash is None:
#                         print(f"Skipping file due to MD5 error: {file_path}")
#                         continue
                    
#                     file_size = os.path.getsize(file_path)
#                     creation_date = os.path.getctime(file_path)
#                     similarity_percentage = None
#                     duplicate_group = None

#                     # Check for duplicates and calculate similarity
#                     for stored_key, (stored_hash, stored_group) in hash_dict.items():
#                         current_similarity = calculate_similarity(perceptual_hash_value, stored_hash)
#                         if current_similarity > 90:  # Adjust the threshold as needed
#                             if similarity_percentage is None or current_similarity > similarity_percentage:
#                                 similarity_percentage = current_similarity
#                                 duplicate_group = stored_group

#                     if duplicate_group is None:
#                         duplicate_group = group_counter
#                         group_counter += 1

#                     file_to_group[file_path] = duplicate_group

#                     hash_dict[(str(perceptual_hash_value), md5_hash)] = (perceptual_hash_value, duplicate_group)

#                     writer.writerow({
#                         'Filename': file,
#                         'FileExtension': file_extension,
#                         'FileType': file_type,
#                         'PerceptualHash': str(perceptual_hash_value),
#                         'MD5Hash': md5_hash,
#                         'FileSize': file_size,
#                         'CreationDate': creation_date,
#                         'SimilarityPercentage': f"{similarity_percentage:.2f}" if similarity_percentage is not None else "",
#                         'DuplicateGroup': duplicate_group
#                     })
#                     print(f"Processed file: {file_path}")

#                     processed_files += 1
#                     progress = (processed_files / total_files) * 100
#                     print(f"Progress: {progress:.2f}% (Processed {processed_files}/{total_files} files)", end='\r')
#                 except Exception as e:
#                     print(f"Error processing {file_path}: {e}")

#     # Log duplicates to a separate CSV file
#     with open('duplicates.csv', 'w', newline='') as dup_csvfile:
#         dup_writer = csv.writer(dup_csvfile)
#         dup_writer.writerow(['DuplicateFiles'])
#         for dup_file in duplicate_files:
#             dup_writer.writerow([dup_file])

#     print("\nCSV file generation completed.")
#     print(f"Duplicate files logged in 'duplicates.csv'.")

# def main_menu():
#     print("Select an option:")
#     print("1. Compare videos within a single folder")
#     print("2. Compare videos between two different folders")
#     choice = input("Enter your choice (1/2): ").strip()
#     return choice

# # # Example usage
# directory = r"D:\0_Media-Archive\01_sort\Files to Sort\Delete"
# csv_filename = r"d:\all_files_attributes.csv"
# # generate_csv(directory, csv_filename, include_subfolders=True)
# # print(f"CSV file '{csv_filename}' generated successfully.")



# if __name__ == "__main__":
#     choice = main_menu()
    
#     if choice == '1':
#         # directory = input("Enter the directory path to compare videos within: ").strip()
#         process_videos_within_folder(directory, csv_filename,search_subfolders=True, similarity_threshold=80)
        
#     elif choice == '2':
#         directory1 = input("Enter the first directory path to compare videos from: ").strip()
#         directory2 = input("Enter the second directory path to compare videos to: ").strip()
#         process_videos_between_folders(directory1, directory2, csv_filename)
#     else:
#         print("Invalid choice. Please enter either '1' or '2'.")