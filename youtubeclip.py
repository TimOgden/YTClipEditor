import numpy as np
import matplotlib.pyplot as plt
from pytube import YouTube
import os
import subprocess
from scipy.io import wavfile
import json
import googleapiclient.discovery
import re
import pandas as pd
from timestamps import split_timestamps, convert_timestamp
import csv
from movie_maker import clip_video, clip_video_python

PATTERN = re.compile(r'\d{1,3}(?::\d{1,3}){1,2}(?:\s*-\s*\d{1,3}(?::\d{1,3}){1,2})?')

class YoutubeVideo():
	def __init__(self, *args, **kwargs):
		if 'url' in kwargs:
			self.url = kwargs['url']
			self.id_ = self.url[kwargs['url'].index('.com/watch?v=')+len('.com/watch?v='):]
			self.id_ = self.id_.split('&')[0]
		elif 'id' in kwargs:
			self.url = 'https://youtube.com/watch?v=' + kwargs['id']
			self.id_ = kwargs['id']
		else:
			raise ValueError('Please provide a url or id to your video.')
		if 'plot_color' in kwargs:
			self.plot_color = kwargs['plot_color']
		else:
			self.plot_color = [66/255.,78/255.,245/255.]
		if 'delta_t' in kwargs:
			self.delta_t = kwargs['delta_t']
		else:
			self.delta_t = 10
		print('Getting data now')
		yt = YouTube(self.url)
		self.title = self.clean_title(yt.title)
		self.comments_path = self.download_comments()
		self.video_path = self.download_video(yt)
		self.audio_path = self.download_audio(yt)
		self.wav_path = self.extract_wav()
		self.dbs = self.get_dbs(optional_delta_t=1)
		self.length = yt.length
		self.views = yt.views

		

	def set_plot_color(self, color):
		self.plot_color = color
	def clean_title(self,title):
		return title.replace('<','').replace('>','') \
		.replace(':','').replace('"','').replace('/','') \
		.replace('\\','').replace('|','').replace('?','') \
		.replace('*','').replace('.','').replace(',','') \
		.replace('~','').replace('\'','')
	
	def download_video(self, yt):
		self.length = yt.length
		self.views = yt.views
		video = yt.streams.filter(progressive=False,file_extension='mp4').order_by('resolution').desc().first()
		self.title = self.clean_title(yt.title)
		self.vid_filepath = os.path.join('YTVideos',self.title+'.mp4')
		if not os.path.exists(self.vid_filepath):
			print('Downloading video of {} with format {}'.format(self.title, video))
			video.download('./YTVideos')
		else:
			print('Video of {} already downloaded.'.format(self.title))
		return self.vid_filepath

	def download_audio(self, yt):
		audio = yt.streams.filter(only_audio=True).first()
		self.title = self.clean_title(yt.title)
		self.aud_filepath = os.path.join('YTAudio',self.title+'.mp4')
		if not os.path.exists(self.aud_filepath):
			print('Downloading audio of {} with format {}'.format(self.title, audio.mime_type))
			audio.download('./YTAudio')
		else:
			print('Audio of {} already downloaded.'.format(self.title))
		return self.aud_filepath

	def extract_wav(self):
		if not os.path.exists(os.path.join('wavs',self.title+'.wav')):
			command = 'ffmpeg -hide_banner -loglevel error -i "./{}" -ab 160k -ac 2 -ar 44100 -vn "./wavs/{}.wav"'.format(self.audio_path, self.title)
			subprocess.call(command, shell=True)
			print('Created WAV file.')
		else:
			print('WAV File already exists.')
		return os.path.join('wavs',self.title+'.wav')

	def get_dbs(self, optional_delta_t=None):
		samplerate, data = wavfile.read(self.wav_path)
		self.length = data.shape[0] / samplerate
		if optional_delta_t:
			chunk_size = samplerate * optional_delta_t
		else:
			chunk_size = samplerate*self.delta_t
		self.num_chunks = data.shape[0] // chunk_size

		data_chunks = np.array_split(data, self.num_chunks)
		means = [np.mean(chunk**2) for chunk in data_chunks]
		dbs = [20*np.log10(np.sqrt(mean)) if mean > 0 else 0 for mean in means]
		return dbs

	def set_delta_t(self,delta_t):
		self.delta_t = delta_t

	def get_timestamps(self):
		timestamps = []
		with open(self.comments_path,'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			#print('Num of comments:',sum(1 for row in reader))
			for row in reader:
				try:
					comment = ''.join(row)
					[timestamps.append(ts) for ts in split_timestamps(re.findall(PATTERN, comment))]
				except Exception as e:
					pass
		#print(len(timestamps))
		return timestamps

	def timestamps_timeintervals(self):
		timestamps = self.get_timestamps()
		return [t for t in timestamps if type(t)!=list], [t for t in timestamps if type(t)==list]

	def remove_long_timeintervals(self, ts, max_len):
		ts_new = []
		for t in ts:
			if t[1] - t[0] <= max_len:
				ts_new.append(t)
		return ts_new

	def plot(self, offset=0, quantile=None):
		dbs = self.get_dbs(optional_delta_t=1)
		time = np.linspace(offset,self.length+offset,self.num_chunks)
		max_dbs = np.amax(dbs) # min-max normalization
		min_dbs = np.amin(dbs)
		dbs = (dbs - min_dbs)*20 / (max_dbs - min_dbs)
		plt.plot(time,dbs,c='w',linewidth=.5,alpha=.5)
		plt.hlines(np.mean(dbs),0,len(dbs))
		timestamps, timeintervals = self.timestamps_timeintervals()
		hist = np.histogram([(t+offset) for t in timestamps],bins=np.arange(offset,self.length+offset,self.delta_t))
		hist, bins = hist[0], hist[1]
		#print('Hist:',hist)
		#print('Bins:',bins)
		#if quantile:
			#val = np.quantile(hist, quantile)
			#print(bins[:-1][hist>=val])
		plt.hist([(t+offset) for t in timestamps],bins=np.arange(offset,self.length+offset,self.delta_t),color=self.plot_color)
		for i,interval in enumerate(timeintervals):
			plt.plot([(val+offset) for val in interval],[i+1]*len(interval),marker='o',c=self.plot_color,markersize=2,markeredgecolor='k',alpha=.8)

	def find_good_timeintervals(self, max_len, user_gen_quantile=.8,
								algorithmic_gen_quantile=.9,
								walkback=10,walkforward=5, val=None):
		mean_dbs = np.mean(dbs)
		std_dbs = np.std(dbs)
		timestamps, timeintervals = self.timestamps_timeintervals()
		timeintervals = self.remove_long_timeintervals(timeintervals,max_len)
		hist = np.histogram([t for t in timestamps],bins=np.arange(0,self.length,self.delta_t))
		hist, bins = hist[0], hist[1]
		print('Histogram:', hist)
		print('Convolution:', np.convolve(hist,np.ones(3,dtype=int),'valid'))

		if not val:
			val = np.quantile(hist, user_gen_quantile)

		good_bins = bins[:-1][hist>=val]
		user_gen = []
		for good_bin in good_bins:
			#print('{} is a good bin above the {:.2%} percentile'.format(good_bin,user_gen_quantile))
			ti_start_in_bin = self.fitting_timeintervals(timeintervals,start_range=(good_bin,good_bin+9.999))
			
			if len(ti_start_in_bin)>0:
				user_gen.append([np.amin(ti_start_in_bin),np.amax(ti_start_in_bin)])
		#print(good_bins)
		val = np.quantile(hist, algorithmic_gen_quantile)
		good_bins = bins[:-1][hist>=val]
		algo_gen = []
		for good_bin in good_bins:
			pass
		return user_gen


	def fitting_timeintervals(self,ti,start_range=None,end_range=None):
		if start_range is not None and end_range is not None:
			return [t for t in ti 
					if t[0]>=start_range[0] and t[0]<=start_range[1]
					and t[1]>=end_range[0] and t[1]<=end_range[1]]
		elif start_range is not None:
			return [t for t in ti 
					if t[0]>=start_range[0] and t[0]<=start_range[1]]
		elif start_range is None and end_range is None:
			return None
		else:
			return [t for t in ti 
					if t[1]>=end_range[0] and t[1]<=end_range[1]]

	def download_comments(self, max_pages=100):
		filename = os.path.join('comments',self.title+'.csv')
		if os.path.exists(filename):
			print('Comments already downloaded.')
			return filename
		print('Grabbing comments now...')
		# Disable OAuthlib's HTTPS verification when running locally.
		# *DO NOT* leave this option enabled in production.
		#os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
		comments = []
		api_service_name = "youtube"
		api_version = "v3"
		DEVELOPER_KEY = "AIzaSyAn5ykH3EZSXZ5VPfGJ5ncWJQGIOmmCzVI"

		youtube = googleapiclient.discovery.build(
			api_service_name, api_version, developerKey = DEVELOPER_KEY)
		request = youtube.commentThreads().list(
			part="snippet,replies",
			videoId=self.id_,
			maxResults=100
		)
		response = request.execute()
		for c in response['items']:
			comments.append(c['snippet']['topLevelComment']['snippet']['textOriginal'])
		#print(comments)
		nextToken = response['nextPageToken']
		i = 1
		while nextToken and i<max_pages:
			request = youtube.commentThreads().list(
				part="snippet",
				videoId=self.id_,
				maxResults=100,
				pageToken=nextToken
			)
			response = request.execute()
			for c in response['items']:
				comments.append(''.join(c['snippet']['topLevelComment']['snippet']['textOriginal']))
			try:
				nextToken = response['nextPageToken']
			except:
				break
			print(f'Page {i}/{max_pages}', end='\r')
			i+=1
		with open(filename,'w', encoding='utf-8') as f:
			writer = csv.writer(f)
			for comment in comments:
				#print(comment)
				writer.writerow(comment)
		return filename

if __name__ == '__main__':
	yt = YoutubeVideo(url='https://www.youtube.com/watch?v=HjShcaf9jOY&list=PLRQGRBgN_Enod4X3kbPgQ9NePHr7SUJfP')
	gti = yt.find_good_timeintervals(120)
	#print('Good Time Intervals:', gti)
	#yt.set_plot_color([66/255.,135/255.,245/255.])
	#yt.plot(quantile=.9)
	#plt.gca().set_facecolor((.3,.3,.3))
	#plt.show()

	clip_video(yt.video_path,yt.audio_path,gti,'output.mp4')