# python-vimeo

> This is a wrapper to work with Vimeo's API to extend PyVimeo

## Setup: Make sure you have:
1. A Vimeo app
2. Your Vimeo access token should have all the permissions you need (see the Vimeo API reference for information on which permissions you need)
3. An `access_token` for most API calls
4. A `client_id` and `client_secret` for uploading images/videos to Vimeo
5. A `user_id` for creating new Vimeo Folders (ignorable if you aren't working with Folders)

## Installation

```bash
pip install python-vimeo
```

## Using this package

```python
from python_vimeo.client import Vimeo

vimeo = Vimeo(
    access_token=PERSONAL_ACCESS_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_id=123456789,  # Used for creating folders
)

video = cimeo.get_video("/videos/166593614")
print(video['uri'])  # This is the video_uri you'll want to store
```

Technically, for this package, all you _need_ is an `access_token`.

The `client_id` and `client_secret` are used for the PyVimeo methods for uploading a picture or a video.

## Making API calls

```python
from python_vimeo.client import Vimeo

vimeo = Vimeo(
    access_token=PERSONAL_ACCESS_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

# Upload a video. You'll want to store the video_uri.
video_uri = vimeo.upload_video('testvideo.mp4', 'My test video')

# Upload a picture
vimeo.upload_picture(video_uri, 'test-picture.png')

# Get a large JSON object with all the information about a video
video_details = vimeo.get_video(video_uri)

# Get just the common information from the get_video() method
details_dict = vimeo.get_common_video_information(video_uri)

# Change the content rating to 'violence', 'drugs', 'language', 'nudity', 'advertisement', 'safe', or 'unrated'
status = vimeo.change_video_content_rating(video_uri, rating='language')  # Returns < 300 for healthy responses

# Pull a video from URL and let Vimeo download and transcode it.
video_uri = vimeo.pull_video_from_url('https://website.com/test.mp4', 'My test video')

# Delete a video
status = vimeo.delete_video(video_uri)  # Returns 204 if deleted.

# Create a folder
folder_uri = vimeo.create_folder("Hello, folder!")

# Update the folder name
folder_uri = vimeo.update_folder_name(folder_uri, "Updated folder name")

# Add a video to a folder
status = vimeo.add_video_to_folder(folder_uri, ideo_uri)  # Returns an int less than 300 as a "positive" response.

# Delete a folder but keep the videos that are in it
folder_uri = vimeo.delete_folder(folder_uri)

# Delete a folder and delete all the videos in it
folder_uri = vimeo.delete_folder(folder_uri, delete_all_videos_in_folder=True)

# Remove a video from a folder
folder_uri = vimeo.remove_video_from_folder(folder_uri, video_uri)

# Tag a video
status = vimeo.tag_video(video_uri, "Testing tag")  # Returns an int less than 300 as a positive response

# Remove a tag from a video
status = vimeo.remove_tag_from_video(video_uri, "Testing tag")  # Returns an int less than 300 as a positive response

# Add a domain to your video
status = vimeo.domain_whitelist_video(video_uri, 'arbington.com')  # Returns an int less than 300 as a positive response
```

