import sys
import time
from mpd import MPDClient, MPDError, CommandError
import os

class PiPlayerError(Exception):
    """Fatal error in PiPlayer."""
   
class PiPlayer():
    VOLUME_STEP = 10 # Volume increment
    PLAYLIST_FILENAME = "playlist" # Playlist filename

    def __init__(self, host="localhost", port="6600", password=None):
        self._host = host
        self._port = port
        self._password = password
        self._client = MPDClient() # MPD client class
         
        # MPD settings
        self._client.timeout = 10  # Network timeout in seconds (floats allowed), default: None
        self._client.idletimeout = None  # Timeout for fetching the result of the idle command is handled seperately, default: None
        #client.repeat(1)  # Set to repeat mode
        
    # Connect to MPD
    def connect(self):
        try:
            self._client.connect(self._host, self._port)
        # Catch socket errors
        except IOError as err:
            errno, strerror = err
            raise PiPlayerError("Could not connect to '%s': %s" %
                              (self._host, strerror))

        # Catch all other possible errors
        except MPDError as e:
            raise PiPlayerError("Could not connect to '%s': %s" %
                              (self._host, e))

        if self._password:
            try:
                self._client.password(self._password)

            # Catch errors with the password command (e.g., wrong password)
            except CommandError as e:
                # On CommandErrors we have access to the parsed error response
                # split into errno, offset, command and msg.
                raise PiPlayerError("Could not connect to '%s': "
                                    "password commmand failed: [%d] %s" %
                                    (self._host, e.errno, e.msg))

            # Catch all other possible errors
            except (MPDError, IOError) as e:
                raise PiPlayerError("Could not connect to '%s': "
                            "error with password command: %s" %
                            (self._host, e))

    def disconnect(self):
        # Try to tell MPD we're closing the connection first
        try:
            self._client.close()

        # If that fails, don't worry, just ignore it and disconnect
        except (MPDError, IOError):
            pass

        try:
            self._client.disconnect()

            # Disconnecting failed, so use a new client object instead
        except (MPDError, IOError):
            self._client = MPDClient()

    def poll(self):
        try:
            song = self._client.currentsong()

        # Couldn't get the current song, so try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                song = self._client.currentsong()

            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't retrieve current song: %s" % e)
            
                        
    def next_channel(self):
        try: # Try setting
            self._client.next()  # Switch to next channel in playlist
            
        # Couldn't get the current song, so try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                self._client.next()
                
            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't switch channel: %s" % e)

    def previous_channel(self):
        try: # Try setting
            self._client.previous()  # Switch to next channel in playlist
            
        # Couldn't get the current song, so try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                self._client.previous()
                
            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't switch channel: %s" % e)  
        
    def toggle_play(self):
        if self.mpdStatus['state'] == 'play':  # Check if playing
            self.stop_play()  # Stop play
        else: 
            self.start_play()  # Start play
        
    def increase_volume(self):
        volume_set = int(self._client.status(['volume']))  # Get the current volume
        volume_new = volume_set + self.VOLUME_STEP  # Calculate the new volume
        self.set_volume(volume_new)  # Set the new volume
                        
    def decrease_volume(self):
        volume_set = int(self._client.status(['volume']))  # Get the current volume
        volume_new = volume_set - self.VOLUME_STEP  # New volume
        self.set_volume(volume_new)  # Set the new volume
            
    def set_volume(self, volume_new):
        if 0 <= volume_new <= 100:  # Check if the volume is within range
            
            try: # Try setting
                self._client.setvol(volume_new)  
                
            # Couldn't get the current song, so try reconnecting and retrying
            except (MPDError, IOError):
                self.disconnect()

                try:
                    self.connect()

                # Reconnecting failed
                except PiPlayerError as e:
                    raise PiPlayerError("Reconnecting failed: %s" % e)

                try:
                    self._client.setvol(volume_new) 
                    
                # Failed again, just give up
                except (MPDError, IOError) as e:
                    raise PiPlayerError("Couldn't change volume: %s" % e)  
            
    def stop_play(self):
        try: # Try setting
            self._client.stop()  
                
        # Couldn't get the current song, so try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                self._client.stop() 
                    
            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't stop play: %s" % e)   
                
    def start_play(self):
        try: # Try setting
            self._client.play()  
                
        # Try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                self._client.play() 
                    
            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't start play: %s" % e)    
                
    def pause_play(self):
        try: # Try setting
            self._client.pause()  
                
        # Couldn't get the current song, so try reconnecting and retrying
        except (MPDError, IOError):
            self.disconnect()

            try:
                self.connect()

            # Reconnecting failed
            except PiPlayerError as e:
                raise PiPlayerError("Reconnecting failed: %s" % e)

            try:
                self._client.pause() 
                    
            # Failed again, just give up
            except (MPDError, IOError) as e:
                raise PiPlayerError("Couldn't pause play: %s" % e)  
                
    #def event_handler(self, eventType):
     #   if eventType == Event.ENCODER1_SWITCH_DOWN:
      #      self.toggle_play() # Toggle play
       # elif eventType == Event.ENCODER1_SWITCH_LONG_HOLD:
          #  self.shutdown() # System shutdown

        #if self.mpdStatus['state'] == 'play':
         #   if eventType == Event.ENCODER1_UP:
          #      self.increase_volume() # Increase volume
           # elif eventType == Event.ENCODER1_DOWN:
            #    self.decrease_volume() # Decrease volume
            #elif eventType == Event.ENCODER2_UP:
             #   self.next_station() # Next station
            #elif eventType == Event.ENCODER2_DOWN:
             #   self.previous_station()  # Previous station
            #elif eventType == Event.ENCODER1_SWITCH_LONG_HOLD:
             #   pass
            #elif eventType == Event.ENCODER2_SWITCH_DOWN:
             #   pass
            #elif eventType == Event.ENCODER2_SWITCH_UP:
             #   pass
            
        #event.clear() # Clear events for next trigger 
               
    def shutdown(self):
        self._client.close()  # Close connection
        self._client.kill()  # Kill MPD
        #os.system('Shutting down now')  # System shutdown

    def load_playlist(self):
        try:
            self._client.load(self.PLAYLIST_FILENAME)  # Load playlist
        except Exception as e:
            print(e)  # Print exception
                                                    
                                                                              
if __name__ == "__main__":
    piPlayer = PiPlayer()
    piPlayer.connect()
    piPlayer.set_volume(30)
    piPlayer.load_playlist()
    piPlayer.start_play()
    time.sleep(5)
    piPlayer.pause_play()
    time.sleep(5)
    piPlayer.stop_play()
    piPlayer.disconnect()
    
    #piPlayer.set_volume(20)
    #piPlayer.start_play()
    #while True:
     #   piPlayer.poll()
      #  sleep(3)
                         
