from .dual_audio_capture import *


def main():
    
    p = init_pyaudio()
    
    try:
        # get default devices
        default_mic, default_speakers = get_default_audio_sources(p)
        # open microphone stream
        mic_stream = open_audio_stream(p, default_mic, channel="mono")
        # open loopback stream for system audio
        loopback_stream = open_audio_stream(p, default_speakers, channel="stereo")
        # monitor both streams for audio activity
        monitor_audio_streams(mic_stream, loopback_stream, default_mic['name'], default_speakers['name'])
    finally:
        p.terminate()


if __name__ == "__main__":
    main()
