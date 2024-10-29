EPOCH=$(date --date="${STARTDATE}" +%s)
https://stackoverflow.com/questions/74291856/ffmpeg-encode-timestamp-on-a-timelapse-video

ffmpeg -i see_cam_12.mjpeg -vf drawtext="fontsize=30:fontcolor=yellow:text='%{pts\:l
ocaltime\:${EPOCH}}':x=(w-text_w) - 10:y=(h-text_h) - 10" -vcodec libx265 -crf 28 time_encode.mjpeg


