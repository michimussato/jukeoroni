import glob
import os
import logging
import random
import tempfile
import threading
import time

from player.models import Track as DjangoTrack
from player.jukeoroni.box_track import JukeboxTrack
from player.jukeoroni.create_update_track_list import create_update_track_list
from player.jukeoroni.settings import Settings
from player.models import Album
from player.jukeoroni.track_loader import _track_loader_task


class BaseBox(object):

    # box_type = None
    # album_type = ALBUM_TYPE_MUSIC
    # audio_dir = MUSIC_DIR


    """
from player.jukeoroni.juke_box import Jukebox
box = Jukebox()
box.turn_on()

box.set_auto_update_tracklist_on()


box.turn_off()
    """
    def __init__(self, jukeoroni=None):

        # Needs class assignment, otherwise
        # all classes inherited from BaseBox
        # log as [player.jukeoroni.base_box]
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)

        # self.box_type = None

        # LOG.info(f'Initializing {self.box_type} box.')

        self.on = False
        self.loader_mode = 'random'

        self.jukeoroni = jukeoroni
        if self.jukeoroni is None:
            self.LOG.warning('No jukeoroni specified. Functionality is limited.')

        self.layout = None
        self._loading_display = False

        self.playing_track = None
        self.is_on_air = None

        self.requested_album_id = None
        self._need_first_album_track = False
        self._auto_update_tracklist = False

        self.tracks = []
        # self.loading_process = None
        self.loading_track = None

        self.run_tracklist_generator_flag = False
        self.track_list_updater_running = False

        self._track_list_generator_thread = None
        self._track_loader_watcher_thread = None
        self._track_loader_thread = None

    @property
    def file_filter(self):
        raise NotImplementedError('Needs to be reimplemented')

    @property
    def box_type(self):
        raise NotImplementedError('Needs to be reimplemented')

    @property
    def album_type(self):
        raise NotImplementedError('Needs to be reimplemented')

    @property
    def audio_dir(self):
        raise NotImplementedError('Needs to be reimplemented')

    def temp_cleanup(self):
        temp_dir = tempfile.gettempdir()
        self.LOG.info(f'cleaning up {temp_dir}...')
        for filename in glob.glob(os.path.join(temp_dir, 'tmp*')):
            os.remove(filename)
        self.LOG.info('cleanup done.')

    @property
    def next_track(self):
        if not bool(self.tracks):
            return None
        return self.tracks.pop(0)

    def turn_on(self, disable_track_loader=False):
        assert not self.on, f'{self.box_type} is already on.'

        self.temp_cleanup()

        self.on = True

        self.track_list_generator_thread()
        if not disable_track_loader:
            self.track_loader_thread()
        # self.track_loader_watcher_thread()

    def turn_off(self):
        assert self.on, f'{self.box_type} is already off.'
        self.on = False
        if self._track_list_generator_thread is not None:
            self._track_list_generator_thread.join()
            self._track_list_generator_thread = None

        self.temp_cleanup()

    ############################################
    # set modes
    def set_loader_mode_random(self):
        self.kill_loading_process()
        self.loader_mode = 'random'

    def set_loader_mode_album(self):
        self.kill_loading_process()
        self.loader_mode = 'album'
        self._need_first_album_track = True

    def play_album(self, album_id):
        self.requested_album_id = album_id
        self.loader_mode = 'album'
        self.kill_loading_process()

    def play_track(self, track_id):
        self.kill_loading_process()
        return DjangoTrack.objects.get(id=track_id)
    ############################################

    def set_auto_update_tracklist_on(self):
        self._auto_update_tracklist = True

    def set_auto_update_tracklist_off(self):
        self._auto_update_tracklist = False

    @property
    def playback_proc(self):
        return self.playing_track.playback_proc

    ############################################
    # track list generator
    # only start this thread if auto_update_tracklist
    # is required. otherwise simply call create_update_track_list
    # once.
    # this is not returning non picklable objects
    # so hopefully ideal for multiprocessing
    # can't use multiprocessing because the main thread is
    # altering self.on

    def track_list_generator_thread(self):
        assert self.on, f'Turn {self.box_type} on first'
        assert self._track_list_generator_thread is None, '_track_list_generator_thread already running.'
        self._track_list_generator_thread = threading.Thread(target=self.track_list_generator_task)
        self._track_list_generator_thread.name = f'Track List Generator Thread ({self.box_type})'
        self._track_list_generator_thread.daemon = False
        self._track_list_generator_thread.start()

    def track_list_generator_task(self):

        _waited = None

        while self.on:
            if not self._auto_update_tracklist:
                _waited = None

            else:
                if _waited is None \
                        or _waited % Settings.DEFAULT_TRACKLIST_REGEN_INTERVAL == 0\
                        or self.run_tracklist_generator_flag:
                    _waited = 0
                    if self._auto_update_tracklist:
                        self.track_list_updater_running = True
                        create_update_track_list(box=self, directory=self.audio_dir, album_type=self.album_type, file_filter=self.file_filter)
                    self.run_tracklist_generator_flag = False
                    self.track_list_updater_running = False
                    # instead of putting it to sleep, we
                    # could schedule it maybe (so that it can finish an
                    # restart at some given time again)
                    # time.sleep(DEFAULT_TRACKLIST_REGEN_INTERVAL)

                _waited += 1
            time.sleep(1.0)

    ############################################
    # track loader
    def track_loader_thread(self):
        assert self.on, f'{self.box_type} must be on'
        self._track_loader_thread = threading.Thread(target=_track_loader_task, kwargs={'box': self, })
        self._track_loader_thread.name = 'Track Loader Thread'
        self._track_loader_thread.daemon = False
        self._track_loader_thread.start()

    @property
    def track_list(self):
        return DjangoTrack.objects.filter(album__album_type=self.album_type)

    def get_next_track(self):
        # TODO: it could happen that the file path is not up to date
        #  so a if file does not exist check must be implemented

        next_track = None

        # Random mode
        if self.loader_mode == 'random':
            self.LOG.info('Getting next track in random mode...')
            tracks = self.track_list
            if not bool(tracks):
                self.LOG.debug(f'{self.album_type} tracklist is empty! Returning None.')
                return None
            next_track = random.choice(tracks)
            self.LOG.info(f'Next track is: {next_track}.')
            return next_track

        # Album mode
        elif self.loader_mode == 'album':
            self.LOG.info('Getting next track in album mode...')

            if self.requested_album_id is not None:
                self.LOG.info(f'Next track with specified album id: {self.requested_album_id} ({Album.objects.get(id=self.requested_album_id)})')

                album_tracks = DjangoTrack.objects.filter(album=self.requested_album_id)
                _next_track = JukeboxTrack(django_track=album_tracks[0])
                next_track = _next_track.first_album_track
                self.LOG.info(f'Returning next track: {_next_track}')
                self.requested_album_id = None
                self._need_first_album_track = False

                return next_track

            if self._need_first_album_track:
                self.LOG.info("First album track requested...")
                self._need_first_album_track = False
                if self.playing_track is not None:
                    self.LOG.info("Track is playing...")
                    if self.playing_track.is_first_album_track:
                        self.LOG.info("Currently playing track is first of album. Returning second...")
                        next_track = self.playing_track.next_album_track
                    else:
                        self.LOG.info("Returning first...")
                        next_track = self.playing_track.first_album_track
                    self.LOG.info(next_track)
                    return next_track
                else:
                    self.LOG.info(f'No track is playing.')
                    if bool(self.tracks):
                        # This should never happen as long as the queue gets emptied
                        # by kill_loading_process() FIRST
                        raise NotImplementedError('This case is not implemented.')
                        """
                        LOG.info(f'Queue is not empty. Getting album of first track in queue...')
                        first_in_queue = self.tracks[0]
                        """
                    else:
                        self.LOG.info(f'Queue is empty. Getting first track of random album...')
                        tracks = self.track_list
                        _next_track = JukeboxTrack(django_track=random.choice(tracks))
                        next_track = _next_track.first_album_track
                        self.LOG.info(f'Next track: {next_track}')
                        return next_track

            else:
                if bool(self.tracks):
                    # This can happen after a mode change if the queue gets filled with
                    # content very quickly after it was emptied

                    # TODO:
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [DEBUG] [Track Loader Thread|2939155552] [player.jukeoroni.juke_box]: 1 of 3 tracks cached. Queue: [Brothers of Metal - Prophecy of Ragnarok [FLAC][16][44.1] - 01 Death of the God of Light.flac]
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [INFO] [Track Loader Thread|2939155552] [player.jukeoroni.juke_box]: Getting next track in album mode...
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [INFO] [State Watcher Thread|2970612832] [player.jukeoroni.jukeoroni]: Media inserted: Brothers of Metal - Prophecy of Ragnarok [FLAC][16][44.1] - 01 Death of the God of Light.flac (type <class 'player.jukeoroni.box_track.JukeboxTrack'>)
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [INFO] [Track Loader Thread|2939155552] [player.jukeoroni.juke_box]: Getting next track based on queue list...
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: Exception in thread Track Loader Thread:
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: Traceback (most recent call last):
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:     self.run()
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:   File "/usr/lib/python3.7/threading.py", line 865, in run
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:     self._target(*self._args, **self._kwargs)
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:   File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 216, in _track_loader_task
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:     loading_track = self.get_next_track()
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:   File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 318, in get_next_track
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]:     next_album_track = self.tracks[-1].next_album_track
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: IndexError: list index out of range
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [DEBUG] [State Watcher Thread|2970612832] [player.jukeoroni.jukeoroni]: Starting new playback thread
                    #  Apr 24 09:54:45 jukeoroni gunicorn[2736]: [04-24-2022 09:54:45] [INFO] [JukeOroni Playback Thread|2939155552] [player.jukeoroni.jukeoroni]: starting playback thread: for /data/usb_hdd/media/audio/music/on_device/Brothers of Metal - 2017 - Prophecy of Ragnarok [FLAC][16][44.1]/01 Death of the God of Light.flac from /data/usb_hdd/media/audio/music/on_device/Brothers of Metal - 2017 - Prophecy of Ragnarok [FLAC][16][44.1]/01 Death of the God of Light.flac

                    self.LOG.info(f'Getting next track based on queue list...')
                    next_album_track = self.tracks[-1].next_album_track
                    if next_album_track is None:
                        self.LOG.info(f'Last track in queue is last track of album. Getting first track of random album...')
                        tracks = self.track_list
                        _next_track = JukeboxTrack(django_track=random.choice(tracks))
                        next_track = _next_track.first_album_track
                        self.LOG.info(f'Next track: {next_track}')
                        return next_track
                    else:
                        next_track = next_album_track
                        self.LOG.info(f'Next track: {next_track}')
                        return next_track

                else:
                    self.LOG.info(f'Queue list is empty. Getting track based on currently playing...')

                    first_album_track = self.playing_track.first_album_track

                    '''
[11-20-2022 02:32:59] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [Aqen - Meditation Astrale [FLAC][24][44.1] - 01 - L'oubli.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 02 - Sinistre Cauchemar.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 03 - Terreur Interieure.flac]
[11-20-2022 02:33:00] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [Aqen - Meditation Astrale [FLAC][24][44.1] - 01 - L'oubli.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 02 - Sinistre Cauchemar.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 03 - Terreur Interieure.flac]
[11-20-2022 02:33:01] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [Aqen - Meditation Astrale [FLAC][24][44.1] - 01 - L'oubli.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 02 - Sinistre Cauchemar.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 03 - Terreur Interieure.flac]
[11-20-2022 02:33:02] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 3 of 3 tracks cached. Queue: [Aqen - Meditation Astrale [FLAC][24][44.1] - 01 - L'oubli.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 02 - Sinistre Cauchemar.flac, Aqen - Meditation Astrale [FLAC][24][44.1] - 03 - Terreur Interieure.flac]
[11-20-2022 02:33:03] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-20-2022 02:33:03] [INFO    ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 37, in _track_loader_task:    meditationbox     : Next track OK: off_device/Sounds of Nature (Serenity Series) - 1995 - Ocean Surf (Philippe De Canck) [FLAC][16][44.1]/01 - Ocean Surf.flac
...
[11-20-2022 02:33:59] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-20-2022 02:33:59] [WARNING ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 26, in _track_loader_task:    meditationbox     : Got "None" track. Retrying...
[11-20-2022 02:34:00] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-20-2022 02:34:00] [WARNING ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 26, in _track_loader_task:    meditationbox     : Got "None" track. Retrying...
[11-20-2022 02:34:01] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-20-2022 02:34:01] [WARNING ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 26, in _track_loader_task:    meditationbox     : Got "None" track. Retrying...
...
[11-20-2022 03:32:48] [DEBUG   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 16, in _track_loader_task:    meditationbox     : 0 of 3 tracks cached. Queue: []
[11-20-2022 03:32:48] [ERROR   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 59, in _track_loader_task:    meditationbox     : 'NoneType' object has no attribute 'first_album_track'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 23, in _track_loader_task
    loading_track = box.get_next_track()
  File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 317, in get_next_track
    first_album_track = self.playing_track.first_album_track
AttributeError: 'NoneType' object has no attribute 'first_album_track'
[11-20-2022 03:32:48] [ERROR   ] [Track Loader Thread|2896163936], File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 62, in _track_loader_task:    meditationbox     : 'NoneType' object has no attribute 'first_album_track'
Traceback (most recent call last):
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 60, in _track_loader_task
    raise e
  File "/data/django/jukeoroni/player/jukeoroni/track_loader.py", line 23, in _track_loader_task
    loading_track = box.get_next_track()
  File "/data/django/jukeoroni/player/jukeoroni/base_box.py", line 317, in get_next_track
    first_album_track = self.playing_track.first_album_track
AttributeError: 'NoneType' object has no attribute 'first_album_track'
...
                    '''

                    self.LOG.info(f'First album track of playing album track is: {first_album_track}')

                    if self.playing_track.django_track == first_album_track:
                        second_album_track = self.playing_track.next_album_track
                        self.LOG.info(f'Playing track and first track are the same. Returning next: {second_album_track}')
                        return second_album_track
                    else:
                        self.LOG.info(f'Returing first album track: {first_album_track}')
                        return first_album_track

        self.LOG.warning('We have an unexpected condition! No next track!')
        assert next_track is not None, 'We have an unexpected condition! No next track!'

    def kill_loading_process(self):
        # TODO: we could implement storing the first track in the queue
        #  that gets emptied here to get stored somewhere so that
        #  we can switch from random to album mode based on the
        #  the first track in the queue if nothing is playing
        #  (track index should suffice)
        # if self.loading_track is not None:
            # LOG.info('loading_process: {0}'.format(self.loading_track._))
        # LOG.info('killing self.loading_process and resetting it to None')
        if bool(self.tracks) or \
                not bool(self.tracks) and self.playing_track is not None \
                or self.requested_album_id is not None:
            if self.loading_track is not None:
                self.LOG.info('loading_process is active, trying to terminate and join...')
                # os.kill(self.process_pid, signal.SIGKILL)
                # TODO try kill()
                self.loading_track.kill_caching_process()
                # self.loading_track.kill()  # SIGKILL
                # # self.loading_process.terminate()  # SIGTERM Does not join
                # LOG.info('loading_process terminated.')
                # self.loading_process.join()
                # LOG.info('loading_process terminated and joined')
                # a process can be joined multiple times:
                # here: just wait for termination before proceeding
                # self.loading_process.join()
            self.loading_track = None

            # remove all cached tracks from the filesystem except the one
            # that is currently playing

            # is it a problem if self.track is still empty?
            for track in self.tracks:
                if track.cached and not track.is_playing:
                    if os.path.exists(track.cache_tmp):
                        try:
                            os.remove(track.cache_tmp)
                        except FileNotFoundError:
                            self.LOG.exception('Tempfile not found:')
            self.tracks = []
            self._track_loader_thread = None
    ############################################
