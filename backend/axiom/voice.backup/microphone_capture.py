"""
Microphone Audio Capture Setup

Handles real-time audio input from microphone for voice pipeline.

Install audio library: pip install sounddevice
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MicrophoneCapture:
    """
    Captures audio from microphone in real-time.
    
    Provides async generator for feeding audio chunks to the voice pipeline.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        device_id: Optional[int] = None,
    ):
        """
        Initialize microphone capture.
        
        Args:
            sample_rate: Sample rate in Hz (16000 recommended for STT)
            chunk_size: Chunk size in samples
            channels: Number of channels (1 for mono)
            device_id: Specific device to use (None = default)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_id = device_id
        self.stream = None
        self._is_recording = False
    
    def list_devices(self) -> list[dict]:
        """
        List available audio devices.
        
        Returns:
            List of device info dicts
        """
        try:
            import sounddevice as sd
            
            devices = []
            for i, device in enumerate(sd.query_devices()):
                if device['max_input_channels'] > 0:
                    devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                    })
            
            return devices
        except ImportError:
            logger.error("sounddevice not installed. Install with: pip install sounddevice")
            return []
    
    async def start(self) -> bool:
        """
        Start microphone recording.
        
        Returns:
            True if successfully started
        """
        try:
            import sounddevice as sd
            
            logger.info(
                f"Starting microphone capture: {self.sample_rate}Hz, "
                f"{self.channels} channels, {self.chunk_size} chunk size"
            )
            
            self._is_recording = True
            
            logger.info("Microphone capture started")
            return True
        
        except ImportError:
            logger.error("sounddevice not installed")
            return False
        except Exception as e:
            logger.error(f"Error starting microphone: {e}")
            return False
    
    async def stop(self):
        """Stop microphone recording."""
        self._is_recording = False
        if self.stream:
            try:
                self.stream.stop()
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
        logger.info("Microphone capture stopped")
    
    async def audio_stream_generator(self) -> AsyncGenerator[np.ndarray, None]:
        """
        Async generator that yields audio chunks from microphone.
        
        Yields:
            Audio chunks as numpy arrays (float32, mono)
        """
        try:
            import sounddevice as sd
            
            if not self._is_recording:
                await self.start()
            
            # Use sounddevice InputStream with async support
            loop = asyncio.get_event_loop()
            queue = asyncio.Queue()
            
            def audio_callback(indata, frames, time_info, status):
                """Callback for audio stream."""
                if status:
                    logger.warning(f"Audio status: {status}")
                
                # Copy audio data and put in queue
                audio_copy = indata[:, 0].copy() if self.channels == 1 else indata.copy()
                try:
                    loop.call_soon_threadsafe(queue.put_nowait, audio_copy)
                except Exception as e:
                    logger.error(f"Error in audio callback: {e}")
            
            # Create stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk_size,
                device=self.device_id,
                callback=audio_callback,
                dtype='float32',
            )
            
            with self.stream:
                logger.info("Microphone stream active")
                
                while self._is_recording:
                    try:
                        # Get audio chunk from queue
                        chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
                        yield chunk.astype(np.float32)
                    except asyncio.TimeoutError:
                        # Timeout is normal - just means no audio yet
                        continue
        
        except ImportError:
            logger.error(
                "sounddevice not installed. "
                "Install with: pip install sounddevice"
            )
        except Exception as e:
            logger.error(f"Error in audio stream: {e}")


def create_microphone_stream(
    sample_rate: int = 16000,
    chunk_size: int = 1024,
    device_id: Optional[int] = None,
) -> MicrophoneCapture:
    """
    Create a microphone capture instance.
    
    Args:
        sample_rate: Sample rate in Hz
        chunk_size: Audio chunk size
        device_id: Specific device ID
        
    Returns:
        MicrophoneCapture instance
    """
    return MicrophoneCapture(
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        device_id=device_id,
    )


# ============================================================================
# Test utilities
# ============================================================================


async def test_microphone_setup():
    """Test microphone setup and device discovery."""
    logger.info("Testing microphone setup...")
    
    capture = MicrophoneCapture()
    
    # List devices
    devices = capture.list_devices()
    logger.info(f"Available audio devices:")
    for device in devices:
        logger.info(f"  [{device['id']}] {device['name']} ({device['channels']} channels)")
    
    if not devices:
        logger.error("No audio input devices found!")
        return False
    
    # Try to start recording
    try:
        success = await capture.start()
        if not success:
            logger.error("Failed to start microphone")
            return False
        
        logger.info("Microphone started successfully")
        
        # Record for a few seconds
        logger.info("Recording 3 seconds of audio...")
        audio_chunk_count = 0
        
        async for chunk in capture.audio_stream_generator():
            audio_chunk_count += 1
            
            if audio_chunk_count >= 3:  # 3 seconds worth of chunks
                break
            
            # Log audio level
            level = np.abs(chunk).mean()
            logger.debug(f"Audio level: {level:.4f}")
        
        logger.info(f"Captured {audio_chunk_count} audio chunks")
        
        await capture.stop()
        return True
    
    except Exception as e:
        logger.error(f"Error testing microphone: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test microphone
    success = asyncio.run(test_microphone_setup())
    
    if success:
        logger.info("✅ Microphone setup successful!")
    else:
        logger.error("❌ Microphone setup failed!")
