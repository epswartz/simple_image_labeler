from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import argparse
import os
from glob import glob
from tqdm import tqdm



IMG_EXTENSIONS = ["png", "jpg", "jpeg", "gif"]


parser = argparse.ArgumentParser()
parser.add_argument('--dir', required=True, help='Root folder of images, can have subdirs.')
parser.add_argument('--csv', required=False, default="./bboxes.csv", help='csv path to store bounding boxes in. Also used to resume labeling.')

opt = parser.parse_args()


# Resume from csv file if it exists, otherwise create it
if os.path.exists(opt.csv):
    print(f"Resuming from existing csv file: {opt.csv}")
else:
    print(f"Creating new csv file: {opt.csv}")
    with open(opt.csv, "w") as f:
        f.write("image_path,x1,x2,y1,y2\n")
        f.close()

bbox_df = pd.read_csv(opt.csv)


# Read list of files
raw_paths = glob(os.path.join(opt.dir, "**"), recursive=True)
image_paths = []
for rp in tqdm(raw_paths, "Fetching Image Filepaths"):
    if rp.split(".")[-1] in IMG_EXTENSIONS:
        image_paths.append(rp)
print(f"Found {len(image_paths)} image files in directory.")


def store_bbox(imgpath: str, bbox: str):
    print(f"Storing bbox for: {imgpath}")
    x1,y1,x2,y2 = bbox.split(",")

    # Format such that x1 and y1 are lower ones
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    # Add to in memory df for tracking, and also immediately write to file
    bbox_df.loc[-1] = [imgpath, x1, x2, y1, y2]
    with open(opt.csv, "a") as f:
        f.write(f"{imgpath},{x1},{x2},{y1},{y2}\n")
        f.close()


image_idx = 0 # index of the current image, the next one to be annotated.

def next_image():
    """
    Updates the state of the app, changing the idx of the next image.
    """
    global image_idx
    global bbox_df
    # skip past what we've already done.
    # This looks like it's O(n) but under normal execution only the first one will ever run for many iterations.
    while image_idx < len(image_paths) and image_paths[image_idx] in bbox_df['image_path'].values:
        image_idx += 1

next_image() # Call it once to skip past all the images that were already done, resuming labeling if we stopped the server.
print(f"Current Index:{image_idx}/{len(image_paths)}")

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1 # Don't cache the CSS file/the template.

@app.route('/current_img', methods=["GET"])
def current_img():
    """
    Had a little trouble making it serve static content from user-defined directory,
    probably because if this was a true web-based project that would be a terrible idea.

    Ended up just making this route to serve the current img.
    """
    path_split = image_paths[image_idx].split("/")
    filename = path_split[-1]
    subdir = "/".join(path_split[:-1])
    return send_from_directory(subdir, filename, cache_timeout=1)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        if request.form.get('next') == 'Next Image':
            store_bbox(image_paths[image_idx], request.form['bbox'])
            next_image()
        else:
            print("ERROR UNKNOWN POST")
    if image_idx < len(image_paths):
        return render_template("index.html", current_image_index=image_idx, total_images=len(image_paths))
    else:
        return f"All images complete! Check {opt.csv} for bounding boxes."

if __name__ == '__main__':
    app.run(debug=False)
