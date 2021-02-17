import ffmpeg
import subprocess
import cv2
def clip_video(video, audio, time_intervals, output_file):
	#command = 'ffmpeg -i "{}" -i "{}" -c:v copy -c:a aac "{}"'.format(video, audio, output_file)
	command = f'ffmpeg -y -i "{video}" -i "{audio}" -vf "select=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
				+ f'\', setpts=N/FRAME_RATE/TB " ' \
				+ f'-af "aselect=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
				+ f'\',asetpts=N/SR/TB" "{output_file}"' 
	print(command)
	subprocess.call(command, shell=True)
	#for i,t in enumerate(time_intervals):
	#	h = (t[0]//60**2, t[1]//60**2)
	#	m = (t[0]//60, t[1]//60)
	#	s = (t[0]%60, t[1]%60)
	#	command = 'ffmpeg -i "{}" -ss {:02d}:{:02d}:{:02d} -to {:02d}:{:02d}:{:02d} -c copy "{}"' \
	#				.format(output_file, h[0],m[0],s[0], h[1],m[1],s[1], f'./clips/clip_{i}.mp4')
	#	
	#	subprocess.call(command,shell=True)

def clip_video_python(video, audio, time_intervals, output_file):
	video_input = ffmpeg.input(video)
	audio_input = ffmpeg.input(audio)
	ffmpeg.concat(
		*[video_input.trim(start=t[0],end=t[1]) for t in time_intervals],
	).output(output_file).run()
	#audio_result = ffmpeg.concat(
	#	*[audio_input.trim(start=t[0],end=t[1]) for t in time_intervals],
	#)
	#ffmpeg.concat(video_result, audio_result, v=1, a=1).output(output_file).run()