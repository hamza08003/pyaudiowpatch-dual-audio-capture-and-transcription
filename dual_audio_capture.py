import pyaudiowpatch as pyaudio
import numpy as np
import time


def init_pyaudio():
    return pyaudio.PyAudio()


def get_default_audio_sources(p):
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_mic_index = wasapi_info["defaultInputDevice"]
    default_mic = p.get_device_info_by_index(default_mic_index)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break

    print(f"Monitoring devices:\nMicrophone: {default_mic['name']}\nLoopback Device: {default_speakers['name']}")
    return default_mic, default_speakers


def get_channel_value(channel_type):
    if channel_type.lower() == "mono":
        return 1
    elif channel_type.lower() == "stereo":
        return 2
    else:
        raise ValueError("Invalid channel type. Use 'mono' or 'stereo'.")


def open_audio_stream(p, device_info, channel, format=pyaudio.paFloat32, sample_rate=None, frames_per_buffer=1024):
    channel_value = get_channel_value(channel)
    return p.open(
        format=format,
        channels=channel_value,
        rate=int(sample_rate or device_info["defaultSampleRate"]),
        input=True,
        frames_per_buffer=frames_per_buffer,
        input_device_index=device_info["index"],
    )


def detect_audio_source(audio_data, threshold=0.035):
    rms = np.sqrt(np.mean(np.square(audio_data)))  
    # print(f"RMS: {rms}")
    return rms > threshold


def monitor_audio_streams(mic_stream, loopback_stream, mic_name, speaker_name, audio_detection_threshold=0.035, silence_detection_threshold=50):
    current_source = None
    silence_counter = 0

    try:
        print("Listening for audio activity...")
        while True:
            # read data from both streams
            mic_data = np.frombuffer(mic_stream.read(1024, exception_on_overflow=False), dtype=np.float32)
            loopback_data = np.frombuffer(loopback_stream.read(1024, exception_on_overflow=False), dtype=np.float32)

            mic_active = detect_audio_source(mic_data, audio_detection_threshold)
            loopback_active = detect_audio_source(loopback_data, audio_detection_threshold)

            # detect audio source
            if mic_active:
                if current_source != "Microphone":
                    print(f"Audio Source: Microphone ({mic_name})")
                    current_source = "Microphone"
                    silence_counter = 0  # reset silence counter

            elif loopback_active:
                if current_source != "System Loopback":
                    print(f"Audio Source: System Loopback ({speaker_name})")
                    current_source = "System Loopback"
                    silence_counter = 0  # reset silence counter

            else:
                # if silence detected; count consecutive silent frames
                silence_counter += 1
                if silence_counter >= silence_detection_threshold:
                    if current_source != "Silence":
                        print("Silence...")
                        current_source = "Silence"

            # sleep briefly to reduce CPU load
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        loopback_stream.stop_stream()
        loopback_stream.close()

    