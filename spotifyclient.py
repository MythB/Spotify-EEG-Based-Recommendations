import json
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import base64
import webbrowser
import datetime
import os
import personaldata as perD


class RequestHandler(BaseHTTPRequestHandler):
    """Start http server for user login"""

    def do_GET(self):
        request_path = self.path
        cond = 'error=access_denied'
        if cond in request_path:
            print('ACCES DENIED')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes("<body><h1>ACCES DENIED</h1><h3>PLEASE ACCEPT REQUEST.</h3></body>", "utf-8"))
            os._exit(1)
        else:
            token = request_path.replace('/?code=', '')
            spotify_client = SpotifyClient()
            spotify_client.get_decoded_token(token)
            # self.send_response(200)
            self.send_response(301)
            self.send_header('Location','https://open.spotify.com/')
            self.end_headers()
            # self.wfile.write(bytes("<body><h1>LOGIN SUCCESSFULL</h1><h3>YOU CAN CLOSE THIS TAB.</h3></body>", "utf-8"))

    def log_message(self, format, *args):
        return


class SpotifyClient:
    """Spotify API"""

    def __init__(self):
        self.client_id = perD.client_id  # set your clien id id here
        self.client_secret = perD.client_secret  # set your client secret here
        client_creds = f"{self.client_id}:{self.client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        self.aut = client_creds_b64.decode()

    def token_checker(self):
        now = datetime.datetime.now()
        if self.when_will_expire is not None:
            if self.when_will_expire < now:
                url = 'https://accounts.spotify.com/api/token'
                aut = self.aut
                code = SpotifyClient._refresh_token
                response = self._refresh_token_post_api_request(url, code, aut)
                response_json = response.json()
                access_token = response_json['access_token']
                expires_in = response_json['expires_in']
                SpotifyClient._authorization_token = access_token
                SpotifyClient.when_will_expire = now + datetime.timedelta(seconds=expires_in)
                return True
            return False

    def get_decoded_token(self, code):
        url = 'https://accounts.spotify.com/api/token'
        redirect_uri = 'http://localhost:8888'
        aut = self.aut
        response = self._token_post_api_request(url, code, redirect_uri, aut)
        response_json = response.json()
        access_token = response_json['access_token']
        refresh_token = response_json['refresh_token']

        # when expired get new one
        now = datetime.datetime.now()
        expires_in = response_json['expires_in']
        SpotifyClient.when_will_expire = now + datetime.timedelta(seconds=expires_in)  # when will it expire
        # print(f"Token will expire at {SpotifyClient.when_will_expire}")

        SpotifyClient._authorization_token = access_token  #WE HAVE ACCES TOKEN
        SpotifyClient._refresh_token = refresh_token  #WE HAVE REFRESH TOKEN
        url_me = 'https://api.spotify.com/v1/me'
        response_id = self._id_get_api_request(url_me, access_token)
        respose_id_json = response_id.json()
        response_user_id = respose_id_json['id']  # WE HAVE USER ID
        SpotifyClient._user_id = response_user_id

    def get_encoded_token(self):

        redirect_uri = 'http://localhost:8888'
        response_type = 'code'
        scope = 'user-read-playback-state ' \
                'user-read-currently-playing ' \
                'playlist-modify-private ' \
                'playlist-modify-public ' \
                'playlist-read-private ' \
                'user-read-private'
        url = f"https://accounts.spotify.com/authorize?" \
              f"client_id={self.client_id}&" \
              f"redirect_uri={redirect_uri}&" \
              f"scope={scope}&" \
              f"response_type={response_type}"
        webbrowser.open(url, autoraise=True)
        server = HTTPServer(('', 8888), RequestHandler)
        server.handle_request()
        return True

    def get_currently_playing_track(self):
        """Get the currently playing track"""

        url = f"https://api.spotify.com/v1/me/player/currently-playing"
        response = self._get_api_request(url)
        if response.status_code not in range(200, 205):  # OR NOR 200
            print(response.status_code)
            print('NO DOTA FROM SPOTIFY SERVER - CONNECTION PROBLEM')
            os._exit(1)
        if response.status_code == 204:
            response = {
                'track': {'id': 'NOT FOUND', 'track_name': 'NOT FOUND', 'artists': '', 'start_time': 0, 'duration': 0,
                          'progress_time': 0, 'is_playing': True}}
            return response
        response_json = response.json()
        try:
            progress_time = response_json['progress_ms']
            start_time = response_json['timestamp']
            duration = response_json['item']['duration_ms']
            track_id = response_json['item']['id']
            track_name = response_json['item']['name']
            artists = [artist for artist in response_json['item']['artists']]
            is_playing = response_json['is_playing']
            link = response_json['item']['external_urls']['spotify']

            artist_names = ', '.join([artist['name'] for artist in artists])
            current_track_info = {
                'track': {'id': track_id, 'track_name': track_name, 'artists': artist_names, 'start_time': start_time,
                          'duration': duration, 'progress_time': progress_time, 'is_playing': is_playing}}
        except:
            current_track_info = {
                'track': {'id': 'NOT FOUND', 'track_name': 'NOT FOUND', 'artists': '', 'start_time': 0, 'duration': 0,
                          'progress_time': 0, 'is_playing': True}}

        return current_track_info

    def get_track_recommendations(self, seed_tracks_url, limit=20):
        """Get recommended tracks from seed tracks."""
        track_ids = [f"{track}" for track in seed_tracks_url]
        track_ids = ",".join(track_ids)
        url = f"https://api.spotify.com/v1/recommendations?seed_tracks={track_ids}&limit={limit}"
        response = self._get_api_request(url)
        response_json = response.json()

        tracks = [track["id"] for track in response_json["tracks"]]
        return tracks

    def playlist_engine(self, name, desc, tracks):
        """create playlist"""

        url = f"https://api.spotify.com/v1/me/playlists"
        response = self._get_api_request(url)
        response_json = response.json()
        playlist_name = name
        playlist_desc = desc
        index_id = next(
            (item for item in response_json['items'] if item['name'] == playlist_name), None)
        if not index_id:
            playlist_id = None
        else:
            playlist_id = index_id['id']
        if not playlist_id:
            data = json.dumps({
                "name": playlist_name,
                "description": playlist_desc,
                "public": True
            })
            url = f"https://api.spotify.com/v1/users/{self._user_id}/playlists"
            response = self._post_api_request(url, data)
            response_json = response.json()
            playlist_id = response_json["id"]
            track_uris = [f"spotify:track:{track}" for track in tracks]
            track_uris = ",".join(track_uris)
            params = {"uris": "tracks"}
            params["uris"] = track_uris
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            data = json.dumps({
                "range_start": 1,
                "insert_before": 2,
                "range_length": 5
            })
            response = self._put_api_request(url, params, data)
        else:
            track_uris = [f"spotify:track:{track}" for track in tracks]
            track_uris = ",".join(track_uris)
            params = {"uris": "tracks"}
            params["uris"] = track_uris
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            data = json.dumps({
                "range_start": 1,
                "insert_before": 2,
                "range_length": 5
            })
            response = self._put_api_request(url, params, data)

    def _id_get_api_request(self, url, token):
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        return response

    def _get_api_request(self, url):
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._authorization_token}"
            }
        )
        return response

    def _refresh_token_post_api_request(self, url, refresh_token, aut):
        response = requests.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": f"{refresh_token}"
            },
            headers={
                "Authorization": f"Basic {aut}"
            }
        )
        return response

    def _token_post_api_request(self, url, code, redirect_uri, aut):
        response = requests.post(
            url,
            data={
                "grant_type": "authorization_code",
                "code": f"{code}",
                "redirect_uri": f"{redirect_uri}"
            },
            headers={
                "Authorization": f"Basic {aut}"
            }
        )
        return response

    def _post_api_request(self, url, data):
        response = requests.post(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._authorization_token}"
            }
        )
        return response

    def _put_api_request(self, url, params, data):
        response = requests.put(
            url,
            params=params,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._authorization_token}"
            }
        )
        # print (response.status_code)
        return response
