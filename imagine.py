from bing_image_downloader import downloader
import glob
import random


async def rv_image(keyword, adult=False):
    downloader.download(keyword, limit=10, output_dir='download', adult_filter_off=adult, force_replace=True, timeout=10)
    files = glob.glob(f'download/{keyword}/Image_*')
    if len(files) > 0:
        return random.choice(files)
    return None
