import subprocess
import os
import glob

transition_video = 'transition.mp4'
ending_video = 'ending.mp4'


def clean_text(title):
	# parsing on parsing on parsing on parsing
	return title.replace('\'','\\\\\\\\\\\'') # just a ridiculous function but it's correct haha

def create_video_clips(video, audio, time_intervals, output_file, overlay_text='', audio_fade=.5):
	# combine video and audio first
	command = f'ffmpeg -y -i "{video}" -i "{audio}" -c:v copy -c:a aac "./temp_output.mp4"'
	
	print(command)
	subprocess.call(command, shell=True)

	# cut video into a highlight reel
	num = len(time_intervals)
	if num==1:
		t = time_intervals[0]
		command = f'ffmpeg -y -i "./temp_output.mp4" -i "{transition_video}" -vsync 2 -filter_complex ' + \
				f'[1:v]setpts=PTS-STARTPTS,format=yuv420p[tv];[1:a]asetpts=PTS-STARTPTS[ta];' + \
				f'[0:v]trim=start={t[0]}:end={t[1]},setpts=PTS-STARTPTS,format=yuv420p[0v];[0:a]atrim=start={t[0]}:end={t[1]},asetpts=PTS-STARTPTS[0a];' + \
				f'[0v]drawtext=text="{clean_text(overlay_text)}":enable=\'between(t,0,5)\':x=60:y=60:fontsize=42:bordercolor="white":borderw=3:fontfile=Stanberry.ttf[0v_text] ' + \
				f'-map [0v_text] -map [0a] "{output_file}"'
	if num>1:
		command = f'ffmpeg -y -i "./temp_output.mp4" -i "{transition_video}" -vsync 2 -filter_complex ' + \
				f'[0:v]trim=start={time_intervals[0][0]}:end={time_intervals[0][1]},setpts=PTS-STARTPTS,format=yuv420p[0v];[0:a]atrim=start={time_intervals[0][0]}:end={time_intervals[0][1]},asetpts=PTS-STARTPTS[0a];' + \
				f'[0v]drawtext=text="{clean_text(overlay_text)}":enable=\'between(t,0,5)\':x=60:y=60:fontsize=42:bordercolor="white":borderw=3:fontfile=Stanberry.ttf[0v_text];' + \
				''.join([f'[0:v]trim=start={t[0]}:end={t[1]},setpts=PTS-STARTPTS,format=yuv420p[{i+1}v];[0:a]afade=d={audio_fade},areverse,afade=d={audio_fade},areverse,atrim=start={t[0]}:end={t[1]},asetpts=PTS-STARTPTS[{i+1}a];' for i, t in enumerate(time_intervals[1:])]) + \
				'[0v_text][0a][1:v][1:a]'+f'[1:v][1:a]'.join([f'[{i}v][{i}a]' for i in range(1,len(time_intervals))]) + \
				f'concat=n={len(time_intervals)*2-1}:v=1:a=1[outv][outa] -map [outv] -map [outa] "{output_file}"'
	if len(time_intervals)>0:
		print('-'*10)
		print(command)
		print('-'*10)
		subprocess.call(command, shell=True)
	subprocess.call('del /f ./temp_output.mp4',shell=True)

def combine_highlight_reels(output_file):
	search = sorted(glob.glob('clips/*.mp4'), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
	command = f'ffmpeg -y -i {transition_video} ' + ' '.join([f'-i {filename}' for filename in search]) + ' -vsync 2 -filter_complex ' + \
			'[0:v][0:a]'.join([f'[{i+1}:v][{i+1}:a]' for i in range(len(search))]) + f'concat=n={len(search)*2-1}:v=1:a=1[outv][outa] -map [outv] -map [outa] "{output_file}"'
	print(command)
	subprocess.call(command, shell=True)

if __name__ == '__main__':
	combine_highlight_reels('concatenated_output.mp4')
