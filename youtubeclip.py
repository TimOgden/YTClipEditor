import numpy as np
import matplotlib.pyplot as plt
from pytube import YouTube
import os
import subprocess

class YoutubeVideo():
	def __init__(self, *args, **kwargs):
		if 'url' in kwargs:
			self.url = kwargs['url']
		elif 'id' in kwargs:
			self.url = 'https://youtube.com/watch?v=' + kwargs['id']
		else:
			raise ValueError('Please provide a url or id to your video.')

		self.video_path = self.download_video()
		self.audio_path = self.download_audio()
		self.wav_path = self.extract_wav()

	def download_video(self):
		yt = YouTube(self.url)
		video = yt.streams.filter(progressive=False,file_extension='mp4').order_by('resolution').desc().first()
		
		title = yt.title.replace(':','')
		self.title = title
		self.vid_filepath = os.path.join('YTVideos',title+'.mp4')
		if not os.path.exists(self.vid_filepath):
			print('Downloading video of {} with format {}'.format(title, video))
			video.download('./YTVideos')
		else:
			print('Video of {} already downloaded.'.format(title))
		return self.vid_filepath

	def download_audio(self):
		yt = YouTube(self.url)
		audio = yt.streams.filter(only_audio=True).first()
		title = yt.title.replace(':','')
		self.title = title
		self.aud_filepath = os.path.join('YTAudio',title+'.mp4')
		if not os.path.exists(self.aud_filepath):
			print('Downloading audio of {} with format {}'.format(title, audio.mime_type))
			audio.download('./YTAudio')
		else:
			print('Audio of {} already downloaded.'.format(title))
		return self.aud_filepath

	def extract_wav(self):
		print('Creating wav file')
		if not self.audio_path:
			self.audio_path = self.download_audio()
		if not os.path.exists(os.path.join('wavs',self.title+'.wav')):
			command = 'ffmpeg -hide_banner -loglevel error -i "./{}" -ab 160k -ac 2 -ar 44100 -vn "./wavs/{}.wav"'.format(self.audio_path, self.title)
			print(command)
			subprocess.call(command, shell=True)
		else:
			print('WAV File already exists.')
		return os.path.join('wavs',self.title+'.wav')

if __name__ == '__main__':
	yt = YoutubeVideo(url='https://www.youtube.com/watch?v=hk0GS25TRco&list=PLRQGRBgN_Enod4X3kbPgQ9NePHr7SUJfP&index=2')