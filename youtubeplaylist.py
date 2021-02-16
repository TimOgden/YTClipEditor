from pytube import Playlist

class YoutubePlaylist():
	def __init__(self, url):
		self.url = url
		self.video_urls = Playlist(self.url).video_urls
if __name__ == '__main__':
	url = 'https://www.youtube.com/watch?v=hk0GS25TRco&list=PLRQGRBgN_Enod4X3kbPgQ9NePHr7SUJfP&index=2'
	playlist = YoutubePlaylist(url)