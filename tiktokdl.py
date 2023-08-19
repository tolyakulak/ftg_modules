from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video
import asyncio
import os
import io
from .. import loader, utils
import telethon
import urllib.request
import aiohttp

@loader.tds
class TikTokdlMod(loader.Module):
    """Download tiktok videos"""
    
    strings = {"name": "TikTokdl",
               "downloading": "<b>Downloading from TikTok...</b>",
               "uploading": "<b>Uploading file...</b>",
               "args_err": "<b>Type URL or reply to a message with only url in it</b>"}
    
    async def client_ready(self, client, db):
        self.client = client
    
    @loader.unrestricted
    @loader.ratelimit
    async def ttdlcmd(self, message):
        """.ttdl <url> or <reply> - download tiktok video from url"""
        
        text = utils.get_args_raw(message)
        if not text:
            if message.is_reply:
                text = (await message.get_reply_message()).message
            else:
                await utils.answer(message, self.strings("args_err", message))
                return
        
        # notify user we are here ♥
        await utils.answer(message, self.strings("downloading", message))
        
        async with AsyncTikTokAPI() as api:
            video = await api.video(text)
            if video.image_post:
                downloaded = await save_slideshow(video)
            else:
                downloaded = await save_video(video, api)
        
        #let user know we are done downloading
        await utils.answer(message, self.strings("uploading", message))
        #upload to telegram chat
        await self.client.send_file(message.to_id, downloaded)
        
        #delete original message
        await message.delete()

async def save_video(video: Video, api: AsyncTikTokAPI):
    # Carrying over this cookie tricks TikTok into thinking this ClientSession was the Playwright instance
    # used by the AsyncTikTokAPI instance
    async with aiohttp.ClientSession(cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}) as session:
        # Creating this header tricks TikTok into thinking it made the request itself
        async with session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
            o = io.BytesIO(await resp.read())
            o.name = "video.mp4"
            return o

async def save_slideshow(video: Video):
    ret = []
    for i, image_data in enumerate(video.image_post.images):
        url = image_data.image_url.url_list[-1]
        
        # previous way of downloading, saving as file
        #urllib.request.urlretrieve(url, os.path.join("tiktok_cache", f"temp_{video.id}_{i:02}.jpg"))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"referer": "https://www.tiktok.com/"}) as resp:
                o = io.BytesIO(await resp.read())
                o.name = f"{video.id}_{i:02}.jpg"
                ret.append(o)
    
    return ret