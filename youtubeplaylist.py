from pytube import Playlist
from youtubeclip import YoutubeVideo
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import pickle
from movie_maker import create_video_clips

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
			video.gti = video.find_good_timeintervals(user_gen_quantile=.9)
			video.create_histogram(plot_graph=True, normalize=False, offset=offset, quantile=quantile)
			offset += video.length
		plt.gca().set_facecolor((.3,.3,.3))
		if quantile:
			plt.hlines(q,0,offset)

	def plot_views(self):
		views = [video.views for video in self.videos]
		plt.plot(views)
		plt.xlabel('Video Index in List')
		plt.ylabel('Total View Count')

	def quantile(self, decimal):
		hists = np.concatenate([video.create_histogram(normalize=False)[0] for video in self.videos],axis=-1)
		quantile = np.quantile(hists, decimal)
		return quantile

if __name__ == '__main__':
	url = 'https://www.youtube.com/watch?v=muBkYQg-hSg&list=PL3tRBEVW0hiAl6bH2ywV_IabJvVqBM-vG'
	playlist = YoutubePlaylist(url)
	colors = [[66/255.,135/255.,245/255.],
			  [66/255.,215/255.,245/255.],
			  [66/255.,245/255.,191/255.],
			  [117/255.,245/255.,66/255.],
			  [245/255.,188/255.,66/255.],
			  [245/255.,84/255.,66/255.]]
	q = playlist.quantile(.9)
	print(q)
	playlist.plot_videos(colors, quantile=q)
	#plt.show()
	playlist.plot_views()
	#plt.show()
	for i,video in enumerate(playlist.videos):
		create_video_clips(video.video_path,video.audio_path,video.gti,'./clips/{}.mp4'.format(i))
	