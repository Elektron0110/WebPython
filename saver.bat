visual -1920x1080 -f --highlight-all-users --multi-sampling --hide mouse --user-image-dir Users --output-ppm-stream visual.ppm -c 4
ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i visual.ppm -vcodec libx264 -preset slow -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 visual.mp4
