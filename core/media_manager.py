# Creator : github.com/rajsriv
import asyncio
import threading
from datetime import timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

import winsdk.system
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus
from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions

class MediaManagerCore(QObject):
    metadataChanged = pyqtSignal(dict)                                    
    statusChanged = pyqtSignal(bool)               
    positionChanged = pyqtSignal(int, int)                           

    def __init__(self):
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._trigger_update)
        self._update_timer.start(500) 

    def _trigger_update(self):
        asyncio.run_coroutine_threadsafe(self.update_timeline(), self._loop)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.initialize())
        self._loop.run_forever()

    async def initialize(self):
        try:
            self.manager = await MediaManager.request_async()
            self.manager.add_current_session_changed(self._on_session_changed)
            self._current_session = None
            self._prop_token = None
            self._playback_token = None
            await self._setup_session()
        except Exception as e:
            print(f"Media Init Error: {e}")

    def _on_session_changed(self, sender, args):
        asyncio.run_coroutine_threadsafe(self._setup_session(), self._loop)

    async def _setup_session(self):
        if self._current_session:
            try:
                self._current_session.remove_media_properties_changed(self._prop_token)
                self._current_session.remove_playback_info_changed(self._playback_token)
            except: pass
            self._current_session = None

        session = self.manager.get_current_session()
        if session:
            self._current_session = session
            self._prop_token = session.add_media_properties_changed(self._on_properties_changed)
            self._playback_token = session.add_playback_info_changed(self._on_playback_changed)
        
        await self.update_media_info()

    def _on_properties_changed(self, sender, args):
        asyncio.run_coroutine_threadsafe(self.update_media_info(), self._loop)

    def _on_playback_changed(self, sender, args):
        asyncio.run_coroutine_threadsafe(self.update_media_info(), self._loop)

    async def update_media_info(self):
        session = self.manager.get_current_session()
        if not session:
            self.metadataChanged.emit({})
            self.statusChanged.emit(False)
            return

        try:
            props = await session.try_get_media_properties_async()
            info = {
                'title': props.title,
                'artist': props.artist,
                'album_title': props.album_title,
                'art_bytes': None
            }

            if props.thumbnail:
                try:
                    stream = await props.thumbnail.open_read_async()
                    size = stream.size
                    if size > 0:
                        buffer = Buffer(size)
                        await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
                        reader = DataReader.from_buffer(buffer)
                        
                        array = winsdk.system.Array("B", size)
                        reader.read_bytes(array)
                        info['art_bytes'] = bytes(array)
                except Exception as e:
                    print(f"Thumbnail error: {e}")

            self.metadataChanged.emit(info)
            
            playback_info = session.get_playback_info()
            is_playing = playback_info.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
            self.statusChanged.emit(is_playing)
        except Exception as e:
            print(f"Update Info Error: {e}")

    async def update_timeline(self):
        session = self.manager.get_current_session()
        if not session: return

        try:
            timeline = session.get_timeline_properties()
            pos = timeline.position.total_seconds() * 1000
            dur = timeline.end_time.total_seconds() * 1000
            self.positionChanged.emit(int(pos), int(dur))
            
            playback_info = session.get_playback_info()
            is_playing = playback_info.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
            self.statusChanged.emit(is_playing)
        except: pass

    def play_pause(self):
        asyncio.run_coroutine_threadsafe(self._play_pause_async(), self._loop)

    def next_track(self):
        asyncio.run_coroutine_threadsafe(self._next_async(), self._loop)

    def prev_track(self):
        asyncio.run_coroutine_threadsafe(self._prev_async(), self._loop)

    def seek_to(self, position_ms):
        asyncio.run_coroutine_threadsafe(self._seek_async(position_ms), self._loop)

    async def _seek_async(self, position_ms):
        session = self.manager.get_current_session()
        if session:
            try:
                info = session.get_playback_info()
                if info.controls.is_playback_position_enabled:
                    success = await session.try_change_playback_position_async(timedelta(milliseconds=position_ms))
                    print(f"Seek to {position_ms}ms, Success: {success}")
                else:
                    print("Seeking NOT supported by this app.")
            except Exception as e:
                print(f"Seek error: {e}")

    async def _play_pause_async(self):
        session = self.manager.get_current_session()
        if session:
            try:
                await session.try_toggle_play_pause_async()
                await asyncio.sleep(0.1)
                await self.update_media_info()
            except: pass

    async def _next_async(self):
        session = self.manager.get_current_session()
        if session: 
            await session.try_skip_next_async()
            await asyncio.sleep(0.1)
            await self.update_media_info()

    async def _prev_async(self):
        session = self.manager.get_current_session()
        if session: 
            await session.try_skip_previous_async()
            await asyncio.sleep(0.1)
            await self.update_media_info()
