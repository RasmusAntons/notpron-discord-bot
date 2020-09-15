from bing_image_downloader import downloader
import glob


async def rv_image(keyword, adult=False):
    downloader.download(keyword, limit=1, output_dir='download', adult_filter_off=not adult, force_replace=True, timeout=10)
    files = glob.glob(f'download/{keyword}/Image_1.*')
    if len(files) > 0:
        return files[0]
    return None
