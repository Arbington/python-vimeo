import bs4
import os
import requests
import urllib.request
from urllib.parse import urlparse, parse_qs

from vimeo import VimeoClient


class Vimeo:

    def __init__(self, access_token: str=None, client_id: str=None, client_secret: str=None, user_id: int=None):
        # Access token, client ID and secrets can be created in the Vimeo Developer Dashboard
        # When you create a new Vimeo App.
        self.ACCESS_TOKEN = access_token
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.USER_ID = user_id

        # Used for PyVimeo's Python SDK Client
        self.py_vimeo_client = None

        # Status code for detecting bad API calls
        self.response_code = None

        self.REQUEST_HEADERS = {
            "Authorization": f"bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.vimeo.*+json;version=3.4"
        }

    def _get_or_set_py_vimeo_client(self):
        """
        Get or set (and return) the PyVimeo client
        """
        if not self.CLIENT_ID or not self.CLIENT_SECRET:
            raise NotImplementedError

        if self.py_vimeo_client:
            return self.py_vimeo_client

        # PyVimeo Client
        self.py_vimeo_client = VimeoClient(
            token=self.ACCESS_TOKEN,
            key=self.CLIENT_ID,
            secret=self.CLIENT_SECRET
        )

        return self.py_vimeo_client

    def _set_response_code(self, status_code=None):
        """
        Set the internal "status code" of each request.
        If nothing is provided, reset the status code to None after each request
        """
        if not status_code:
            self.response_code = None
        else:
            self.response_code = status_code

    def upload_video(self, file_path: str, video_name: str=None, video_description: str=None, settings: dict={}) -> str:
        """
        Upload a video using PyVimeo with pre-set settings if the `settings` kwarg isn't provided.
            :file_path              str             Local file path to the video
            :video_name             str             Name of the video in Vimeo.com
            :video_description      str             Description of the video in Vimeo.com
            :settings               dict            A dictionary of settings from https://developer.vimeo.com/api/reference/videos?version=3.4#upload_video
        """

        client = self._get_or_set_py_vimeo_client()
        video_uri = client.upload(
            file_path,
            data={
                'name': video_name,
                'description': video_description,
                'content_rating': ['safe'],
                'privacy': {
                    'download': False,
                    'embed': 'whitelist',
                    'comments': 'nobody',
                    'view': 'disable',
                },
                'review_page': {
                    'active': False,
                }
            } if not settings else settings
        )
        self._set_response_code(200 if video_uri else None)
        return video_uri

    def upload_picture(self, video_uri: str, file_path: str) -> dict:
        """
        Upload a video cover image (aka: picture) to an existing video.
        This is NOT an animated picture. And this uses the PyVimeo client.
            :video_uri              str             The video URI provided by vimeo's API, such as /videos/123456789
            :file_path              str             The path to the locale file that should be uploaded. ie. 'test.png'
                                                    If a URL is given, download the file, upload it, then delete it.

        Returns a dictionary like this:
        {
            'uri': '/videos/658371443/pictures/1329492536',
            'link': 'https://kaiju.cloud.vimeo.com/video/1329492536?expires=1639941754&sig=4c66f8accf778d4bb0a06852e8d301ab145f6139',
            'active': True
        }
        """

        local_file = None
        if file_path.startswith("http"):
            # Download the file, upload it to vimeo, delete file from local
            local_file = os.path.basename(file_path)
            file_path, _ = urllib.request.urlretrieve(file_path, local_file)

        client = self._get_or_set_py_vimeo_client()
        upload_response = client.upload_picture(video_uri, file_path, activate=True)

        if local_file and os.path.exists(local_file):
            os.remove(local_file)

        return upload_response

    def get_video(self, video_uri: str) -> dict:
        """
        Get a video from the video_uri.
            :video_uri              str             The video URI provided by vimeo's API, such as /videos/123456789
        """
        video_id = video_uri.split("/").pop()
        response = requests.get(
            f"https://api.vimeo.com/videos/{video_id}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.json()


    def get_common_video_information(self, video_uri: str) -> dict:
        """
            :video_uri      str         The Vimeo video URI. ie. /videos/123456789
            :returns        dict        Returns the status, if video is playable,
                                        link to videos URL, duration, width and height
        """
        video = self.get_video(video_uri)
        return {
            "status": video['transcode']['status'],  # 'complete' or 'in_progress'
            "is_playable": video['is_playable'],  # Boolean
            "link": video['link'],  # ie. https://vimeo.com/123456789
            "duration": video['duration'],  # Int for video length duration in seconds. Ex: 180 (3 minutes)
            "width": video['width'],  # Int for video width. Ex 1920
            "height": video['height'],  # Int for video height. Ex: 1080
        }

    def change_video_content_rating(self, video_uri: str, rating: str='safe') -> int: # IE. 200 response
        """
        Rating should be `violence`, `drugs`, `language`, `nudity`, `advertisement`, `safe` or `unrated`
            :video_uri      str         The Vimeo video URI. ie. /videos/123456789
        """
        if rating not in ['violence', 'drugs', 'language', 'nudity', 'advertisement', 'safe', 'unrated']:
            raise NotImplementedError

        video_id = video_uri.split("/").pop()
        data = {
            "content_rating": [rating],
        }

        response = requests.patch(
            f"https://api.vimeo.com/videos/{video_id}",
            headers=self.REQUEST_HEADERS,
            json=data,
        )
        self._set_response_code(response.status_code)
        return response.json()


    def pull_video_from_url(self, download_url: str, video_name: str, folder_uri: str=None, file_size=None, settings: dict={}, logo_link: str='') -> str:
        """
        Pull a video from a URL and let Vimeo download it.

            :download_url       string      The video file to try and download
            :video_name         string      The name of the video (used in Vimeo's Dashboard)
            :folder_uri         str         The Vimeo folder URI. ie. /users/123456789/projects/90210
            :fize_size          int         Optional. If None then try to detect
                                            the file size for Vimeo.
            :settings           dict        A dictionary of settings to apply to this video.

            Returns the video_uri. ie. /videos/123456789
        """
        if not file_size:
            response = requests.head(download_url, allow_redirects=True)
            file_size = response.headers['Content-Length'] if 'Content-Length' in response.headers else 0

        data = {
            'name': video_name,
            'description': '',
            "upload": {
                "approach": "pull",
                "size": file_size,
                "link": download_url,
            },
            'content_rating': ['safe'],
            'privacy': {
                'download': False,
                'embed': 'whitelist',
                'comments': 'nobody',
                'view': 'disable',
            },
            'review_page': {
                'active': False,
            },
            'embed': {
                'buttons': {
                    'embed': False,
                    'fullscreen': True,
                    'hd': True,
                    'share': False,
                    'watchlater': False,
                },
                'color': '#feeff0',
                'logos': {
                    'custom': {
                        'active': True,
                        'link': logo_link if logo_link else None,
                        'sticky': True,
                    },
                    'vimeo': False,
                },
                'playbar': True,
                'title': {
                    'name': 'hide',
                    'owner': 'hide',
                    'portrait': 'hide',
                },
                'volume': True,
            },
            'folder_uri': folder_uri if folder_uri else None,
        } if not settings else settings

        response = requests.post(
            f"https://api.vimeo.com/me/videos",
            headers=self.REQUEST_HEADERS,
            json=data,
        )

        self._set_response_code(response.status_code)

        response = response.json()
        video_uri = response['uri']

        return video_uri

    def update_video_title(self, video_uri: str, title: str) -> int:
        """
        Update a video title in the Vimeo Dashboard
            :video_uri      str         The Vimeo video URI. ie. /videos/123456789
            :title          str         The new title of the video in the Vimeo
            :returns        int         Returns the request status code. 204 is good, anything else is bad.

        """
        data = {
            "name": title,
        }

        response = requests.patch(
            f"https://api.vimeo.com{video_uri}",
            headers=self.REQUEST_HEADERS,
            json=data,
        )
        self._set_response_code(response.status_code)
        return response.status_code

    def delete_video(self, video_uri: str) -> int:
        """
        Delete a video from your Vimeo account.
            :video_uri      str         The Vimeo video URI. ie. /videos/123456789
            :returns        int         Returns the request status code. 204 is good, anything else is bad.
        """
        response = requests.delete(
            f"https://api.vimeo.com{video_uri}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.status_code

    def create_folder(self, folder_name: str) -> str:
        """
        Create a new folder on Vimeo. This has no bearing on your videos, it's just a way to organize them on Vimeo.com
        to group videos together for later API access (like accessing all videos in a certain folder)

            :folder_name            str                 The name of the folder you want to create.
            :returns                str                 Returns the folder_uri. You'll want to store this for later access.

        NOTE: This NEEDS the USER_ID to be set in order to create a new Vimeo Folder.
        """
        data = {
            "name": folder_name,
        }
        response = requests.post(
            f"https://api.vimeo.com/users/{self.USER_ID}/projects",
            headers=self.REQUEST_HEADERS,
            json=data,
        )

        self._set_response_code(response.status_code)
        response = response.json()
        folder_uri = response['uri']
        return folder_uri

    def update_folder_name(self, folder_uri: str, new_folder_name: str) -> str:
        """
        Updates a foler name in Vimeo.
            :folder_uri             str                 The Vimeo folder_uri. ie. /users/123456789/projects/90210
            :new_folder_name        str                 The NEW name of the folder
            :returns                str                 Returns the folder_uri. You'll want to store this for later access.
        """
        data = {
            "name": new_folder_name,
        }
        response = requests.patch(
            f"https://api.vimeo.com{folder_uri}",
            headers=self.REQUEST_HEADERS,
            json=data,
        )
        self._set_response_code(response.status_code)
        response = response.json()
        return folder_uri

    def delete_folder(self, folder_uri: str, delete_all_videos_in_folder: bool=False) -> str:
        """
        Deletes a foler name in Vimeo.
            :folder_uri                     str                 The Vimeo folder_uri. ie. /users/123456789/projects/90210
            :delete_all_videos_in_folder    bool                The NEW name of the folder
            :returns                        str                 Returns the folder_uri. You'll want to store this for later access.
        """
        data = {
            "should_delete_clips": delete_all_videos_in_folder
        }
        response = requests.delete(
            f"https://api.vimeo.com{folder_uri}",
            headers=self.REQUEST_HEADERS,
            json=data,
        )
        self._set_response_code(response.status_code)
        return folder_uri

    def remove_video_from_folder(self, folder_uri: str, video_uri: str) -> str:
        """
        Removes a video from a folder, but does NOT delete the video.
            :folder_uri                     str                 The Vimeo folder_uri. ie. /users/123456789/projects/90210
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :returns                        str                 Returns the folder_uri. You'll want to store this for later access.
        """

        video_id = video_uri.split("/").pop()
        response = requests.delete(
            f"https://api.vimeo.com{folder_uri}/videos/{video_id}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return folder_uri

    def add_video_to_folder(self, folder_uri: str, video_uri: str) -> int:
        """
        Adds a video to a folder.
            :folder_uri                     str                 The Vimeo folder_uri. ie. /users/123456789/projects/90210
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :returns                        int                 Returns an int based on the response status code.
                                                                Anything under 300 is good. 300 or over is bad.
        """
        video_id = video_uri.split("/").pop()
        response = requests.put(
            f"https://api.vimeo.com{folder_uri}/videos/{video_id}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.status_code

    def tag_video(self, video_uri: str, tag: str) -> int: # ie 200 OK
        """
        Adds a video to a folder.
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :tag                            str                 A string to tag the video with.
            :returns                        int                 Returns an int based on the response status code.
                                                                Anything under 300 is good. 300 or over is bad.
        """
        video_id = video_uri.split("/").pop()

        response = requests.put(
            f"https://api.vimeo.com/videos/{video_id}/tags/{tag}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.status_code

    def remove_tag_from_video(self, video_uri: str, tag: str) -> int: # ie 204 No Content
        """
        Adds a video to a folder.
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :tag                            str                 A string to tag the video with.
            :returns                        int                 Returns an int based on the response status code.
                                                                Anything under 300 is good. 300 or over is bad.
        """
        video_id = video_uri.split("/").pop()
        response = requests.delete(
            f"https://api.vimeo.com/videos/{video_id}/tags/{tag}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.status_code


    def domain_whitelist_video(self, video_uri: str, domain: str) -> int: # ie 204 OK
        """
        Adds a video to a folder.
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :domain                         str                 A string, like "arbington.com" or "localhost:8000"
            :returns                        int                 Returns an int based on the response status code.
                                                                Anything under 300 is good. 300 or over is bad.
        """
        video_id = video_uri.split("/").pop()

        response = requests.put(
            f"https://api.vimeo.com/videos/{video_id}/privacy/domains/{domain}",
            headers=self.REQUEST_HEADERS,
        )
        self._set_response_code(response.status_code)
        return response.status_code

    def get_video_hash(self, video_uri: str) -> str:
        """
        The video hash is the ?h= query param used for securing videos with
        privacy settings with Unlisted videos (Plus subscription or higher is needed)
            :video_uri                      str                 The Vimeo video URI. ie. /videos/123456789
            :returns                        str                 Returns the video hash if there is one.
                                                                If no hash found, then an empty str is returned.
        """
        vimeo_video = self.get_video(video_uri)

        # Get the video Hash ID for embeded videos
        try:
            iframe = vimeo_video['embed']['html']
            soup = bs4.BeautifulSoup(iframe, "html.parser")
            src = soup.find("iframe").get("src").replace("&amp;", "&")
            parsed_url = urlparse(src)
            hash = parse_qs(parsed_url.query)['h'][0]
        except Exception:
            hash = ''
        # End hash extraction

        return hash
