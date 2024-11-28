import asyncio
import ffmpeg
from telethon.tl.types import Message
from .. import loader

@loader.tds
class StreamerMod(loader.Module):
    """Модуль для трансляції відео через RTMPS"""

    strings = {
        "name": "Streamer",
        "start_stream": "Запущено трансляцію...",
        "stop_stream": "Трансляцію зупинено.",
        "no_process": "Немає активної трансляції.",
        "config_missing": "Налаштування неповні. Перевірте конфіг.",
        "invalid_reply": "Будь ласка, відповідайте на відеофайл або надайте підпис.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "TG_KEY", 
                None, 
                lambda: "Ключ RTMPS",
                validator=loader.validators.Hidden()
            ),
            loader.ConfigValue(
                "TG_URL", 
                'rtmps://dc4-1.rtmp.t.me/s/', 
                lambda: "Посилання на RTMPS"
            ),
            loader.ConfigValue(
                "PROFILE", 
                "veryfast", 
                lambda: "FFmpeg профіль (за замовчуванням veryfast)"
            ),
            loader.ConfigValue(
                "B:A", 
                "192k", 
                lambda: "Бітрейт аудіо (за замовчуванням 192k)"
            ),
            loader.ConfigValue(
                "B:V", 
                "5M", 
                lambda: "Бітрейт відео (за замовчуванням 5M)"
            ),
            loader.ConfigValue(
                "C:A", 
                "aac", 
                lambda: "Кодек аудіо (за замовчуванням aac)"
            ),
            loader.ConfigValue(
                "C:V", 
                "libx264", 
                lambda: "Кодек відео (за замовчуванням libx264)"
            ),
        )
        self.stream_process = None

    async def _start_stream(self, input_file: str, message: Message):
        """Запускає трансляцію через FFmpeg"""
        try:
            cmd = (
                ffmpeg
                .input(input_file)
                .output(
                    self.config["TG_URL"],
                    vcodec=self.config["C:V"],
                    acodec=self.config["C:A"],
                    b_v=self.config["B:V"],
                    b_a=self.config["B:A"],
                    preset=self.config["PROFILE"],
                    format="flv"
                )
                .global_args('-re')
                .compile()
            )
            self.stream_process = await asyncio.create_subprocess_exec(*cmd)
            await message.respond(self.strings["start_stream"])
        except Exception as e:
            await message.respond(f"Помилка запуску трансляції: {str(e)}")

    async def _stop_stream(self, message: Message):
        """Зупиняє активну трансляцію"""
        if self.stream_process and self.stream_process.returncode is None:
            self.stream_process.terminate()
            await self.stream_process.wait()
            self.stream_process = None
            await message.respond(self.strings["stop_stream"])
        else:
            await message.respond(self.strings["no_process"])

    @loader.command()
    async def sstartcmd(self, message: Message):
        """sstart <реплей/підпис> - Запускає трансляцію"""
        reply = await message.get_reply_message()
        if not (self.config["TG_KEY"] and self.config["TG_URL"]):
            await message.respond(self.strings["config_missing"])
            return

        if reply and reply.file and reply.file.mime_type.startswith("video"):
            input_file = await reply.download_media()
        elif message.text.split(maxsplit=1)[1:]:
            input_file = message.text.split(maxsplit=1)[1]
        else:
            await message.respond(self.strings["invalid_reply"])
            return

        await self._start_stream(input_file, message)

    @loader.command()
    async def sstopcmd(self, message: Message):
        """sstop - Зупиняє трансляцію"""
        await self._stop_stream(message)