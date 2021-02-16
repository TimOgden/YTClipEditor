from pytube import Playlist
from youtubeclip import YoutubeVideo
from tqdm import tqdm
import matplotlib.pyplot as plt
class YoutubePlaylist():
	def __init__(self, url):
		self.url = url
		self.video_urls = Playlist(self.url).video_urls
		self.videos = []
		for url in tqdm(self.video_urls):
			self.videos.append(YoutubeVideo(url=url))
if __name__ == '__main__':
	url = 'https://www.youtube.com/watch?v=muBkYQg-hSg&list=PL3tRBEVW0hiAl6bH2ywV_IabJvVqBM-vG'
	playlist = YoutubePlaylist(url)
	colors = [[66/255.,135/255.,245/255.],
			  [66/255.,215/255.,245/255.],
			  [66/255.,245/255.,191/255.],
			  [117/255.,245/255.,66/255.],
			  [245/255.,188/255.,66/255.],
			  [245/255.,84/255.,66/255.]]
	offset = 0
	for color,video in zip(colors,playlist.videos):
		video.set_plot_color(color)
		video.plot(offset=offset)
		offset += video.length
	plt.gca().set_facecolor((.3,.3,.3))
	plt.show()