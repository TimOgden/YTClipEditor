from pytube import Playlist
from youtubeclip import YoutubeVideo
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

class YoutubePlaylist():
	def __init__(self, url):
		self.url = url
		self.video_urls = Playlist(self.url).video_urls
		self.videos = []
		for url in tqdm(self.video_urls):
			self.videos.append(YoutubeVideo(url=url))

	def plot_videos(self, colors, quantile=None):
		offset = 0
		for i,video in enumerate(self.videos):
			video.set_plot_color(colors[i%len(colors)])
			video.plot(offset=offset, quantile=quantile)
			offset += video.length
		plt.gca().set_facecolor((.3,.3,.3))
		plt.show()

	def plot_views(self):
		views = [video.views for video in self.videos]
		plt.plot(views)
		plt.xlabel('Video Index in List')
		plt.ylabel('Total View Count')
		plt.show()

	def quantile(self, decimal):
		ts = np.concatenate([video.timestamps_timeintervals()[0] for video in self.videos],axis=0)
		quantile = np.quantile(ts, decimal)
		return quantile

if __name__ == '__main__':
	url = 'https://www.youtube.com/watch?v=HjShcaf9jOY&list=PLRQGRBgN_Enod4X3kbPgQ9NePHr7SUJfP'
	playlist = YoutubePlaylist(url)
	colors = [[66/255.,135/255.,245/255.],
			  [66/255.,215/255.,245/255.],
			  [66/255.,245/255.,191/255.],
			  [117/255.,245/255.,66/255.],
			  [245/255.,188/255.,66/255.],
			  [245/255.,84/255.,66/255.]]
	#playlist.plot_videos(colors)
	#playlist.plot_views()
	print(playlist.quantile(.6))