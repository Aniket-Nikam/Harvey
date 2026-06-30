import sounddevice as sd
import numpy as np

class AudioListener:
    def __init__(self, config):
        self.config = config
    
    def get_loopback_device_index(self):
        try:
            import pyaudiowpatch as pyaudio
            p = pyaudio.PyAudio()
            # 1. Look for a device explicitly marked as loopback
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev.get('isLoopbackDevice'):
                    p.terminate()
                    return i
            
            # 2. Fallback: find loopback device associated with default WASAPI output
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if (dev.get('hostApi') == wasapi_info['index'] and 
                    dev.get('isLoopbackDevice') and 
                    default_output['name'] in dev['name']):
                    p.terminate()
                    return i
            p.terminate()
        except Exception:
            pass
        return None

    def listen_via_microphone(self, duration=10):
        fs = self.config['audio']['sample_rate']
        try:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            return recording.flatten().astype(np.float32) / 32768.0
        except Exception as e:
            print(f"Error capturing microphone audio: {e}")
            return None

    def listen_for_question(self, duration=10):
        """Capture system audio (meeting partner speaking) via WASAPI loopback without cables."""
        import pyaudiowpatch as pyaudio
        import time
        
        loopback_idx = self.get_loopback_device_index()
        if loopback_idx is None:
            # Fallback to microphone if no loopback device is active
            return self.listen_via_microphone(duration)
            
        p = pyaudio.PyAudio()
        try:
            dev_info = p.get_device_info_by_index(loopback_idx)
            rate = int(dev_info['defaultSampleRate'])
            channels = int(dev_info['maxInputChannels'])
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=loopback_idx
            )
            
            frames = []
            start_time = time.time()
            total_samples_needed = duration * rate
            
            while sum(len(f) for f in frames) < total_samples_needed:
                # Absolute safety timeout to prevent locking up
                if time.time() - start_time > duration + 1.0:
                    break
                
                # Retrieve available frames without blocking if system is silent
                available = stream.get_read_available()
                if available >= 1024:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(np.frombuffer(data, dtype=np.int16))
                else:
                    time.sleep(0.01)
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            if not frames:
                return self.listen_via_microphone(duration)
                
            recording = np.concatenate(frames)
            
            # Convert to mono if stereo
            if channels > 1:
                recording = recording.reshape(-1, channels).mean(axis=1)
                
            # Downsample to 16000Hz (Whisper's required samplerate) using linear interpolation
            if rate != 16000:
                num_samples = int(len(recording) * 16000 / rate)
                recording = np.interp(
                    np.linspace(0, len(recording) - 1, num_samples),
                    np.arange(len(recording)),
                    recording
                )
                
            return recording.astype(np.float32) / 32768.0
            
        except Exception as e:
            print(f"Error capturing loopback audio: {e}")
            try:
                p.terminate()
            except Exception:
                pass
            return self.listen_via_microphone(duration)