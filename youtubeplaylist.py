from pytube import Playlist
from youtubeclip import YoutubeVideo
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import pickle
import movie_maker as mm
import time
import sys
import os

class YoutubePlaylist():
	def __init__(self, url, playlist_folder, *kwargs):
		self.playlist_folder = playlist_folder
		self.url = url
		self.video_urls = Playlist(self.url).video_urls
		self.videos = []
		for url in tqdm(self.video_urls):
			self.videos.append(YoutubeVideo(url=url, playlist_folder=self.playlist_folder))

	def plot_videos(self, colors, quantile=None):
		offset = 0
		for i,video in enumerate(self.videos):
			video.set_plot_color(colors[i%len(colors)])
			if not video.gti:
				video.gti = video.find_good_timeintervals(fix_discrepancies=True)
			video.create_histogram(plot_graph=True, normalize=False, offset=offset, quantile=quantile)
			offset += video.length
		plt.gca().set_facecolor((.3,.3,.3))
		if quantile:
			plt.hlines(quantile,0,offset)

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
	url = sys.argv[1]
	try:
		playlist_folder = sys.argv[2]
	except:
		playlist_folder = 'separateVideos'
	if not os.path.exists(f'./playlists/{playlist_folder}/'):
		os.mkdir(f'./playlists/{playlist_folder}/')
	[os.mkdir(f'./playlists/{playlist_folder}/{val}') 
		for val in ['comments','videos','audio','wavs','clips'] if not os.path.exists(f'./playlists/{playlist_folder}/{val}')]
	print(url)
	playlist = YoutubePlaylist(url, playlist_folder)
	for video in playlist.videos:
		video.gti = video.find_good_timeintervals(fix_discrepancies=True)
	colors = [[66/255.,135/255.,245/255.],
			  [66/255.,215/255.,245/255.],
			  [66/255.,245/255.,191/255.],
			  [117/255.,245/255.,66/255.],
			  [245/255.,188/255.,66/255.],
			  [245/255.,84/255.,66/255.]]
	q = playlist.quantile(.9)
	print([video.gti for video in playlist.videos])
	playlist.plot_videos(colors, quantile=q)
	plt.show()
	playlist.plot_views()
	plt.show()

	start_time = time.time()
	for i,video in enumerate(tqdm(playlist.videos)):
		mm.create_video_clips(video.video_path,video.audio_path,video.gti,f'./playlists/{playlist_folder}/clips/{i}.mp4',overlay_text=video.original_title)
	print(f'Creating {len(playlist.videos)} episode reels took {time.time()-start_time:.3f} seconds.')

	#mm.clean_folder(playlist,'clips')

	start_time = time.time()
	mm.combine_highlight_reels(f'./playlists/{playlist_folder}/clips/',f'./playlists/{playlist_folder}/concatenated_output.mp4', delete_clips=True)
	print(f'Merging {len(playlist.videos)} episodes took {time.time()-start_time:.3f} seconds.')
	description = 'Hey guys, here is a highlight reel I made of the Game Grumps playing Wind Waker HD!\nI really love this series and wanted to cut it down for anyone who doesn\'t have time to watch it or just wants to recap all the hightlights!' + \
					'\nMake sure to check out the official Game Grumps channel if you like their content. If you enjoy these highlight reels, make sure to subscribe because there are plenty more to come! Thanks for watching!'
	#mm.upload_video('concatenated_output.mp4','FUNNIEST Moments of Wind Waker HD - Game Grumps Clips',description)