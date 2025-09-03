import tkinter as tk
from tkinter import messagebox
import vlc
import os
import datetime
import subprocess
import platform


class VideoPlayer:
    """Simplified VLC-based video player for RTSP streams"""

    def __init__(self, parent_frame, status_callback=None):
        """
        Initialize the video player

        Args:
            parent_frame: Tkinter frame to embed the video player
            status_callback: Function to call when status updates
        """
        self.parent_frame = parent_frame
        self.status_callback = status_callback or self._default_status_callback

        # VLC initialization with minimal, working options
        self._init_vlc_instance()

        # UI elements
        self.video_frame = None
        self.controls_frame = None
        self.status_label = None
        self.control_buttons = {}

        # State variables
        self._vlc_window_id = None

        # Create UI
        self._create_ui()

        # Check VLC initialization status
        self._check_vlc_status()

    def _check_vlc_status(self):
        """Check VLC initialization status and update UI accordingly"""
        if self.vlc_player is None or self.vlc_instance is None:
            self.status_callback("VLC initialization failed - limited functionality available")
            print("WARNING: VLC not properly initialized. Some features may not work.")
        else:
            self.status_callback("Ready - VLC initialized successfully")
            print("VLC initialized successfully")

    def _init_vlc_instance(self):
        """Initialize VLC with GDI video output to avoid Direct3D issues"""
        # Set environment variables to force GDI and software rendering
        os.environ['VLC_VERBOSE'] = '1'  # Enable verbose logging for debugging

        # Use GDI video output instead of Direct3D to avoid compatibility issues
        vlc_options = [
            '--no-video-title-show',
            '--no-qt-system-tray',
            '--no-osd',
            '--vout=gdi',  # Use GDI video output (most compatible)
            '--avcodec-hw=none',  # Force software decoding
            '--avcodec-threads=1',  # Single thread
            '--network-caching=1000',
            '--no-video-deco',
            '--no-spu',  # Disable subtitles
            '--no-sub-autodetect-file',
            '--no-video-on-top',
            '--no-video-wallpaper',
        ]

        try:
            self.vlc_instance = vlc.Instance(vlc_options)
            self.vlc_player = self.vlc_instance.media_player_new()

            # Log successful initialization
            print("VLC instance initialized successfully with GDI video output")
            print(f"VLC version: {vlc.libvlc_get_version()}")

        except Exception as e:
            print(f"VLC initialization failed: {e}")
            # Try with even more minimal options
            try:
                minimal_options = [
                    '--no-video-title-show',
                    '--no-qt-system-tray',
                    '--no-osd',
                    '--vout=dummy',  # No video output initially
                    '--aout=dummy',  # No audio output initially
                ]
                self.vlc_instance = vlc.Instance(minimal_options)
                self.vlc_player = self.vlc_instance.media_player_new()
                print("VLC initialized with dummy output - will switch to video when needed")
            except Exception as e2:
                print(f"Minimal VLC initialization also failed: {e2}")
                self.vlc_instance = None
                self.vlc_player = None

    def _create_ui(self):
        """Create the video player UI elements"""
        # Create main container frame and pack it initially (but don't fill)
        self.main_frame = tk.Frame(self.parent_frame, bg='#000000')
        self.main_frame.pack(fill=tk.BOTH, expand=True)  # Pack initially so pack_forget works

        # Video display frame
        self.video_frame = tk.Frame(
            self.main_frame,
            bg='#000000',
            width=640,
            height=480
        )
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        # Controls frame
        self.controls_frame = tk.Frame(self.main_frame, bg='#f0f0f0', height=50)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Control buttons
        self._create_control_buttons()

        # Status label
        self.status_label = tk.Label(
            self.controls_frame,
            text="Ready",
            bg='#f0f0f0',
            fg='#000000',
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def _create_control_buttons(self):
        """Create the control buttons for the video player"""
        button_style = {
            'font': ("Segoe UI", 9),
            'bg': '#ffffff',
            'fg': '#000000',
            'activebackground': '#e0e0e0',
            'relief': tk.RAISED,
            'bd': 2,
            'cursor': 'hand2',
            'width': 12,
            'height': 2
        }

        # Play button
        self.control_buttons['play'] = tk.Button(
            self.controls_frame,
            text="▶️ Play",
            command=self.play,
            **button_style
        )
        self.control_buttons['play'].pack(side=tk.LEFT, padx=5, pady=5)

        # Pause button
        self.control_buttons['pause'] = tk.Button(
            self.controls_frame,
            text="⏸️ Pause",
            command=self.pause,
            **button_style
        )
        self.control_buttons['pause'].pack(side=tk.LEFT, padx=5, pady=5)

        # Stop button
        self.control_buttons['stop'] = tk.Button(
            self.controls_frame,
            text="⏹️ Stop",
            command=self.stop,
            **button_style
        )
        self.control_buttons['stop'].pack(side=tk.LEFT, padx=5, pady=5)

        # Screenshot button
        self.control_buttons['screenshot'] = tk.Button(
            self.controls_frame,
            text="📸 Screenshot",
            command=self.take_screenshot,
            **button_style
        )
        self.control_buttons['screenshot'].pack(side=tk.LEFT, padx=5, pady=5)

        # Troubleshoot button
        self.control_buttons['troubleshoot'] = tk.Button(
            self.controls_frame,
            text="🔧 Fix",
            command=self.troubleshoot,
            **button_style
        )
        self.control_buttons['troubleshoot'].pack(side=tk.LEFT, padx=5, pady=5)

    def _default_status_callback(self, message):
        """Default status callback that updates the status label"""
        if self.status_label:
            self.status_label.config(text=message)

    def _setup_video_output(self):
        """Setup video output to the Tkinter frame with simplified, proven working approach"""
        if self.vlc_player is None:
            print("VLC player not initialized, skipping video output setup")
            return False

        if not self._vlc_window_id:
            try:
                # Ensure the video frame is properly mapped and has a valid window ID
                if not self.video_frame.winfo_exists():
                    print("Video frame not yet created, skipping video output setup")
                    return False

                # Force the window to be fully created and mapped
                self.parent_frame.update_idletasks()
                self.video_frame.update_idletasks()

                # Get window handle
                self._vlc_window_id = self.video_frame.winfo_id()
                print(f"Setting up video output for window ID: {self._vlc_window_id}")

                # Set the window handle for video output - this is the critical step
                self.vlc_player.set_hwnd(self._vlc_window_id)

                # Disable mouse and keyboard input on video
                self.vlc_player.video_set_mouse_input(False)
                self.vlc_player.video_set_key_input(False)

                # Set basic video scaling and aspect ratio
                self.vlc_player.video_set_scale(1.0)
                self.vlc_player.video_set_aspect_ratio(None)

                print(f"Video output setup complete for window ID: {self._vlc_window_id}")
                return True

            except Exception as e:
                print(f"Failed to setup video output: {e}")
                # Reset window ID so we can try again later
                self._vlc_window_id = None
                return False
        else:
            print(f"Video output already set up for window ID: {self._vlc_window_id}")
            return True

    def play_stream(self, stream_url):
        """Play an RTSP stream with simplified, proven working approach"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return False

        try:
            self.status_callback("Connecting to RTSP stream...")
            print(f"Loading RTSP stream into VideoPlayer: {stream_url}")

            # Store current RTSP URL for external player fallback
            self.current_rtsp_url = stream_url

            # Validate RTSP URL format
            if not stream_url.startswith('rtsp://'):
                error_msg = "Invalid RTSP URL format. URL must start with 'rtsp://'"
                self.status_callback(f"Error: {error_msg}")
                messagebox.showerror("RTSP Error", error_msg)
                return False

            # Setup video output first
            self._setup_video_output()

            # Create media with minimal, proven working options
            media = self.vlc_instance.media_new(stream_url)

            # Add minimal RTSP options that work reliably
            media.add_option('--rtsp-tcp')  # Force TCP transport
            media.add_option('--network-caching=1000')  # Network caching
            media.add_option('--avcodec-hw=none')  # Software decoding

            self.vlc_player.set_media(media)

            # Start playing
            result = self.vlc_player.play()
            if result != 0:
                error_msg = f"VLC play failed with result: {result}"
                self.status_callback(f"Error: {error_msg}")
                messagebox.showerror("Playback Error", error_msg)
                return False

            self.status_callback("Connecting to stream...")

            # Force video output refresh after starting playback
            self.parent_frame.after(500, lambda: self._refresh_video_output())

            # Verify connection after a delay
            self.parent_frame.after(3000, lambda: self._check_rtsp_connection(stream_url))

            return True

        except Exception as e:
            error_msg = f"Failed to load RTSP stream: {str(e)}"
            self.status_callback(f"RTSP Error: {str(e)}")
            print(f"RTSP connection error: {e}")

            # Simple error handling - offer external player
            try:
                use_external = messagebox.askyesno("RTSP Connection Error",
                    f"Failed to connect to RTSP stream: {str(e)}\n\nWould you like to try opening the stream in an external player?")
                if use_external:
                    self.force_external_player(stream_url)
            except:
                pass
            return False

    def _check_rtsp_connection(self, stream_url):
        """Check RTSP connection status and handle connection issues"""
        if self.vlc_player is None:
            return

        try:
            if self.vlc_player.is_playing():
                self.status_callback("RTSP stream connected - playing")
                print("RTSP stream successfully connected and playing")

                # Refresh video output to ensure visibility
                self._refresh_video_output()

                # Check if video is actually visible after a short delay
                self.parent_frame.after(1000, lambda: self._verify_video_display())

            else:
                # Check the player state for more detailed error information
                state = self.vlc_player.get_state()
                print(f"RTSP connection state: {state}")

                if state == vlc.State.Error:
                    self.status_callback("RTSP connection failed")
                    self._handle_rtsp_error("Connection failed", stream_url)
                elif state == vlc.State.Buffering:
                    self.status_callback("RTSP stream buffering...")
                    # Check again in 2 seconds
                    self.parent_frame.after(2000, lambda: self._check_rtsp_connection(stream_url))
                elif state == vlc.State.Opening:
                    self.status_callback("RTSP stream opening...")
                    # Check again in 1 second
                    self.parent_frame.after(1000, lambda: self._check_rtsp_connection(stream_url))
                else:
                    self.status_callback(f"RTSP state: {state}")
                    # Try to restart if not in error state
                    self.parent_frame.after(2000, lambda: self._retry_rtsp_connection(stream_url))

        except Exception as e:
            print(f"RTSP connection check error: {e}")
            self.status_callback("RTSP connection check failed")

    def _handle_rtsp_error(self, error_message, stream_url):
        """Handle RTSP-specific errors and provide troubleshooting options"""
        print(f"RTSP Error Details: {error_message}")

        # Check for specific RTSP error patterns
        if "400" in error_message or "Bad Request" in error_message:
            error_type = "RTSP Bad Request (400)"
            troubleshooting = (
                "🔧 RTSP 400 Bad Request Troubleshooting:\n\n"
                "This error usually means the RTSP server rejected the request.\n\n"
                "Possible causes:\n"
                "• Authentication required (username/password)\n"
                "• Invalid RTSP URL or stream path\n"
                "• RTSP server configuration issue\n"
                "• Firewall blocking RTSP traffic\n\n"
                "Solutions to try:\n"
                "1. Check RTSP URL format\n"
                "2. Add authentication: rtsp://user:pass@ip:port/path\n"
                "3. Verify camera/stream is accessible\n"
                "4. Check firewall settings (port 8554)\n"
                "5. Try different RTSP transport method"
            )
        elif "401" in error_message or "Unauthorized" in error_message:
            error_type = "RTSP Authentication Required (401)"
            troubleshooting = (
                "🔧 RTSP Authentication Error:\n\n"
                "The RTSP stream requires authentication.\n\n"
                "Try these URL formats:\n"
                "• rtsp://username:password@192.168.8.185:8554/cam\n"
                "• rtsp://admin:password@192.168.8.185:8554/cam\n"
                "• Check camera documentation for default credentials"
            )
        elif "404" in error_message or "Not Found" in error_message:
            error_type = "RTSP Stream Not Found (404)"
            troubleshooting = (
                "🔧 RTSP Stream Not Found:\n\n"
                "The requested RTSP stream path doesn't exist.\n\n"
                "Common stream paths to try:\n"
                "• /cam\n"
                "• /stream\n"
                "• /live\n"
                "• /0\n"
                "• /1\n\n"
                "Check your camera's RTSP documentation."
            )
        elif "timeout" in error_message.lower() or "time" in error_message.lower():
            error_type = "RTSP Connection Timeout"
            troubleshooting = (
                "🔧 RTSP Connection Timeout:\n\n"
                "The RTSP server is not responding.\n\n"
                "Possible solutions:\n"
                "• Check network connectivity\n"
                "• Verify camera IP address\n"
                "• Check if camera is powered on\n"
                "• Try different network interface\n"
                "• Check firewall/antivirus settings"
            )
        else:
            error_type = "RTSP Connection Error"
            troubleshooting = (
                "🔧 General RTSP Connection Error:\n\n"
                "Unable to connect to RTSP stream.\n\n"
                "Troubleshooting steps:\n"
                "1. Verify camera IP and RTSP port\n"
                "2. Check network connectivity\n"
                "3. Try accessing stream in web browser\n"
                "4. Test with VLC Media Player directly\n"
                "5. Check camera configuration\n\n"
                f"Current URL: {stream_url}"
            )

        # Show troubleshooting dialog
        troubleshoot_msg = f"🎥 {error_type}\n\n{troubleshooting}\n\nWould you like to try alternative connection methods?"

        try_alternative = messagebox.askyesno("RTSP Connection Error", troubleshoot_msg)

        if try_alternative:
            self._try_alternative_rtsp_connection(stream_url)

    def _try_alternative_rtsp_connection(self, original_url):
        """Try alternative RTSP connection methods"""
        try:
            # Extract components from original URL
            if "rtsp://" in original_url:
                base_url = original_url.replace("rtsp://", "")
                if "@" in base_url:
                    # Has authentication
                    auth_part, path_part = base_url.split("@", 1)
                    ip_port, stream_path = path_part.split("/", 1)
                    username, password = auth_part.split(":", 1)
                else:
                    # No authentication
                    ip_port, stream_path = base_url.split("/", 1)
                    username = password = None

                # Try different RTSP transport methods
                alternatives = []

                if username and password:
                    base_auth = f"{username}:{password}@{ip_port}"
                else:
                    base_auth = ip_port

                # Try different transport methods
                alternatives.append(f"rtsp://{base_auth}/{stream_path}?transport=tcp")
                alternatives.append(f"rtsp://{base_auth}/{stream_path}?transport=udp")

                # Try different stream paths
                common_paths = ["cam", "stream", "live", "0", "1", "video", "h264"]
                for path in common_paths:
                    if username and password:
                        alternatives.append(f"rtsp://{username}:{password}@{ip_port}/{path}")
                    else:
                        alternatives.append(f"rtsp://{ip_port}/{path}")

                # Try connecting with each alternative
                for alt_url in alternatives[:3]:  # Try first 3 alternatives
                    print(f"Trying alternative RTSP URL: {alt_url}")
                    self.status_callback(f"Trying: {alt_url.split('/')[-1]}")

                    try:
                        media = self.vlc_instance.media_new(alt_url)
                        media.add_option('--rtsp-tcp')
                        media.add_option('--network-caching=2000')
                        media.add_option('--avcodec-hw=none')

                        self.vlc_player.set_media(media)
                        result = self.vlc_player.play()

                        if result == 0:
                            self.status_callback("Alternative connection successful")
                            messagebox.showinfo("Success",
                                f"Connected using alternative RTSP URL:\n{alt_url}")
                            return

                        # Wait a moment for connection attempt
                        self.parent_frame.after(2000)

                    except Exception as e:
                        print(f"Alternative connection failed: {e}")
                        continue

                # If all alternatives failed, offer external player
                self.status_callback("All RTSP connection attempts failed")
                messagebox.showwarning("Connection Failed",
                    "Unable to connect to RTSP stream with any method.\n\n"
                    "Would you like to try opening the stream in an external player?")

        except Exception as e:
            print(f"Alternative connection setup error: {e}")
            self.status_callback("Alternative connection failed")

    def _retry_rtsp_connection(self, stream_url):
        """Retry RTSP connection with different settings"""
        if self.vlc_player is None:
            return

        try:
            print("Retrying RTSP connection...")
            self.status_callback("Retrying RTSP connection...")

            # Stop current attempt
            self.vlc_player.stop()

            # Create new media with different options
            media = self.vlc_instance.media_new(stream_url)
            media.add_option('--rtsp-tcp')  # Force TCP
            media.add_option('--network-caching=3000')  # Higher network caching
            media.add_option('--avcodec-hw=none')
            media.add_option('--live-caching=2000')

            self.vlc_player.set_media(media)
            result = self.vlc_player.play()

            if result == 0:
                self.status_callback("RTSP retry successful")
                self.parent_frame.after(3000, lambda: self._check_rtsp_connection(stream_url))
            else:
                self.status_callback("RTSP retry failed")
                self._handle_rtsp_error(f"Retry failed (result: {result})", stream_url)

        except Exception as e:
            print(f"RTSP retry error: {e}")
            self.status_callback("RTSP retry error")

    def play_file(self, file_path):
        """Play a video file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")

            self.status_callback("Loading video file...")
            self._setup_video_output()

            # Create and set media
            media = self.vlc_instance.media_new(file_path)
            self.vlc_player.set_media(media)

            # Start playing
            self.vlc_player.play()
            self.status_callback(f"Playing: {os.path.basename(file_path)}")

        except Exception as e:
            error_msg = f"Failed to play video file: {str(e)}"
            self.status_callback(f"Error: {str(e)}")
            messagebox.showerror("Video Error", error_msg)
            return False
        return True

    def play(self):
        """Play/resume the current media"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return

        try:
            if self.vlc_player.is_playing():
                self.pause()
            else:
                self.vlc_player.play()
                self.status_callback("Playing")
        except Exception as e:
            self.status_callback(f"Play error: {e}")
            print(f"Play error: {e}")

    def pause(self):
        """Pause the current media"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return

        try:
            self.vlc_player.pause()
            self.status_callback("Paused")
        except Exception as e:
            self.status_callback(f"Pause error: {e}")
            print(f"Pause error: {e}")

    def stop(self):
        """Stop the current media"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return

        try:
            self.vlc_player.stop()
            self.status_callback("Stopped")
        except Exception as e:
            self.status_callback(f"Stop error: {e}")
            print(f"Stop error: {e}")

    def take_screenshot(self):
        """Take a screenshot of the current video"""
        if self.vlc_player is None:
            messagebox.showerror("Screenshot Error", "VLC player not initialized")
            return

        try:
            if not self.vlc_player.is_playing():
                messagebox.showwarning("Screenshot Error", "No video is currently playing. Please start the live feed first.")
                return

            # Create screenshots directory
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            # Generate filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)

            # Take screenshot
            result = self.vlc_player.video_take_snapshot(0, filepath, 0, 0)

            if result == 0:  # Success
                self.status_callback(f"Screenshot saved: {filename}")
                messagebox.showinfo("Screenshot Saved",
                    f"Screenshot captured successfully!\n\nSaved to: {filepath}\n\nYou can find all screenshots in the 'screenshots' folder.")
            else:
                messagebox.showerror("Screenshot Error", "Failed to capture screenshot. Please ensure the video is playing and visible.")

        except Exception as e:
            messagebox.showerror("Screenshot Error", f"Failed to take screenshot: {str(e)}")

    def troubleshoot(self):
        """Provide troubleshooting options for VLC and RTSP issues"""
        # First check current video status
        video_status = self._diagnose_video_issues()

        troubleshoot_msg = (
            "🔧 VLC & RTSP Troubleshooting Options:\n\n"
            f"📊 Current Status: {video_status}\n\n"
            "🎥 Video Display Issues:\n"
            "• Video connected but not visible\n"
            "• Black screen with audio only\n"
            "• Video window not updating\n\n"
            "📡 RTSP Stream Issues:\n"
            "• Verify Camera IP Address\n"
            "• Check RTSP Port (usually 8554)\n"
            "• Test Stream in VLC Media Player\n"
            "• Check Network/Firewall Settings\n\n"
            "🔧 Quick Fixes:\n"
            "• Force Video Redraw\n"
            "• Restart Video Output\n"
            "• Try Alternative Stream\n"
            "• Use External Media Player\n\n"
            "Would you like to try fixing the video display first?"
        )

        fix_video_first = messagebox.askyesno("VLC Troubleshooting", troubleshoot_msg)

        if fix_video_first:
            self._fix_video_display_issues()
        else:
            use_external = messagebox.askyesno("Use External Player", "Would you like to try using an external video player instead?")
            if use_external:
                self.force_external_player()

    def force_external_player(self, stream_url=None):
        """Force the use of an external media player for RTSP streams"""
        try:
            import subprocess
            import platform

            # Get current RTSP URL if not provided
            if not stream_url:
                if hasattr(self, 'current_rtsp_url') and self.current_rtsp_url:
                    stream_url = self.current_rtsp_url
                else:
                    stream_url = "rtsp://192.168.8.185:8554/cam"  # Default RTSP URL

            # Store current URL for future reference
            self.current_rtsp_url = stream_url

            # Try to open with system default media player
            if platform.system() == "Windows":
                # Use cmd to start the URL (works better with RTSP)
                subprocess.run(["cmd", "/c", "start", stream_url], shell=False, check=False)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", stream_url], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", stream_url], check=False)

            self.status_callback("Opened RTSP stream in external player")
            messagebox.showinfo("External Player",
                f"RTSP stream opened in external media player.\n\nURL: {stream_url}\n\nIf the external player doesn't open automatically, you can manually paste this URL into VLC Media Player or another RTSP-compatible player.")

        except Exception as e:
            error_msg = f"Failed to open external player: {str(e)}"
            self.status_callback(f"External player error: {str(e)}")
            messagebox.showerror("External Player Error", error_msg)

    def test_rtsp_connection(self, stream_url):
        """Test RTSP connection before attempting to play"""
        try:
            self.status_callback("Testing RTSP connection...")

            # Try a quick connection test using VLC
            if self.vlc_instance is None:
                self.status_callback("VLC not available for connection test")
                return False

            # Create a test media with short timeout
            test_media = self.vlc_instance.media_new(stream_url)
            test_media.add_option('--rtsp-tcp')
            test_media.add_option('--network-caching=500')  # Short caching
            test_media.add_option('--avcodec-hw=none')

            # Create a test player
            test_player = self.vlc_instance.media_player_new()
            test_player.set_media(test_media)

            # Try to play briefly
            result = test_player.play()

            if result == 0:
                # Wait a moment for connection
                self.parent_frame.after(2000, lambda: self._check_test_connection(test_player, stream_url))
                return True
            else:
                self.status_callback("RTSP connection test failed")
                return False

        except Exception as e:
            print(f"RTSP connection test error: {e}")
            self.status_callback("RTSP test failed")
            return False

    def _check_test_connection(self, test_player, stream_url):
        """Check the result of RTSP connection test"""
        try:
            if test_player.is_playing():
                self.status_callback("RTSP connection test successful")
                test_player.stop()
                test_player.release()
                return True
            else:
                state = test_player.get_state()
                if state == vlc.State.Error:
                    self.status_callback("RTSP connection test failed")
                    test_player.release()
                    return False
                elif state in [vlc.State.Buffering, vlc.State.Opening]:
                    # Still trying, check again
                    self.parent_frame.after(1000, lambda: self._check_test_connection(test_player, stream_url))
                else:
                    self.status_callback("RTSP connection test inconclusive")
                    test_player.release()
                    return False
        except Exception as e:
            print(f"RTSP test check error: {e}")
            self.status_callback("RTSP test error")
            return False

    def _refresh_video_output(self):
        """Refresh video output to ensure video is visible"""
        try:
            if self.vlc_player is None:
                return

            # Force window update
            self.parent_frame.update_idletasks()
            self.video_frame.update_idletasks()

            # Re-setup video output if needed
            if not self._vlc_window_id:
                print("Refreshing video output - setting up window handle")
                self._setup_video_output()

            # Try to get video size and adjust if needed
            try:
                if self.vlc_player.video_get_size(0):
                    width, height = self.vlc_player.video_get_size(0)
                    print(f"Video dimensions: {width}x{height}")

                    # Adjust frame size to match video if needed
                    current_width = self.video_frame.winfo_width()
                    current_height = self.video_frame.winfo_height()

                    if current_width != width or current_height != height:
                        print(f"Adjusting video frame size from {current_width}x{current_height} to {width}x{height}")
                        self.video_frame.config(width=width, height=height)
                        self.parent_frame.update_idletasks()
                else:
                    print("Could not get video size - video may not be ready yet")
            except Exception as size_error:
                print(f"Error getting video size: {size_error}")

            # Force video repaint
            try:
                self.vlc_player.video_set_scale(1.0)
                self.vlc_player.video_set_aspect_ratio(None)
            except Exception as scale_error:
                print(f"Error setting video scale: {scale_error}")

            print("Video output refresh completed")

        except Exception as e:
            print(f"Video output refresh error: {e}")

    def _verify_video_display(self):
        """Verify that video is actually being displayed"""
        try:
            if self.vlc_player is None:
                print("Video verification: VLC player not initialized")
                return

            # Check if player is still playing
            is_playing = self.vlc_player.is_playing()
            print(f"Video verification: Player playing = {is_playing}")

            # Check video size
            try:
                video_size = self.vlc_player.video_get_size(0)
                if video_size:
                    width, height = video_size
                    print(f"Video verification: Video size = {width}x{height}")
                else:
                    print("Video verification: No video size available")
            except Exception as size_error:
                print(f"Video verification: Error getting video size = {size_error}")

            # Check video track info
            try:
                track_info = self.vlc_player.video_get_track_description()
                if track_info:
                    print(f"Video verification: Video tracks available = {len(track_info)}")
                else:
                    print("Video verification: No video track information")
            except Exception as track_error:
                print(f"Video verification: Error getting track info = {track_error}")

            # Check window handle
            if self._vlc_window_id:
                print(f"Video verification: Window handle set = {self._vlc_window_id}")
            else:
                print("Video verification: No window handle set")

            # Check if video frame is visible
            if self.video_frame.winfo_ismapped():
                print("Video verification: Video frame is mapped and visible")
            else:
                print("Video verification: Video frame is not mapped")

            # Update status based on findings
            if is_playing and video_size:
                self.status_callback("Video streaming - display active")
                print("✅ Video verification: Stream appears to be working correctly")
            elif is_playing:
                self.status_callback("Audio streaming - video display issue")
                print("⚠️ Video verification: Audio working but video not displaying")
                # Try to force video refresh
                self.parent_frame.after(1000, lambda: self._force_video_redraw())
            else:
                self.status_callback("Stream not active")
                print("❌ Video verification: Stream not playing")

        except Exception as e:
            print(f"Video verification error: {e}")
            self.status_callback("Video verification failed")

    def _force_video_redraw(self):
        """Force video area redraw to make video visible"""
        try:
            print("Attempting to force video redraw...")

            # Force window updates
            self.parent_frame.update_idletasks()
            self.video_frame.update_idletasks()

            # Try to reset video scaling
            if self.vlc_player:
                self.vlc_player.video_set_scale(1.0)
                self.vlc_player.video_set_aspect_ratio(None)

                # Try to toggle fullscreen briefly (this can force redraw)
                try:
                    self.vlc_player.set_fullscreen(False)
                except:
                    pass

            # Force frame redraw
            self.video_frame.config(bg='#000000')  # Ensure black background
            self.parent_frame.update()

            print("Video redraw attempt completed")

        except Exception as e:
            print(f"Video redraw error: {e}")

    def _diagnose_video_issues(self):
        """Diagnose current video display issues"""
        try:
            if self.vlc_player is None:
                return "VLC not initialized"

            is_playing = self.vlc_player.is_playing()
            state = self.vlc_player.get_state()

            if not is_playing:
                return f"Stream not playing (State: {state})"

            # Check video size
            try:
                video_size = self.vlc_player.video_get_size(0)
                if video_size:
                    return f"Video connected {video_size[0]}x{video_size[1]} - display issue"
                else:
                    return "Audio only - no video stream"
            except:
                return "Video status unknown"

        except Exception as e:
            return f"Diagnosis error: {str(e)}"

    def _fix_video_display_issues(self):
        """Try to fix common video display issues"""
        try:
            self.status_callback("Attempting to fix video display...")

            # Step 1: Force video output refresh
            print("Step 1: Refreshing video output...")
            self._refresh_video_output()

            # Step 2: Force video redraw
            self.parent_frame.after(500, lambda: self._force_video_redraw())

            # Step 3: Try resetting video scaling
            self.parent_frame.after(1000, lambda: self._reset_video_scaling())

            # Step 4: Verify fix after delay
            self.parent_frame.after(2000, lambda: self._verify_video_display())

            self.status_callback("Video display fixes applied")

            messagebox.showinfo("Video Fix Applied",
                "Video display fixes have been applied:\n\n"
                "• Refreshed video output\n"
                "• Forced video redraw\n"
                "• Reset video scaling\n\n"
                "The video should now be visible. If not, try:\n"
                "• Clicking the 'Fix' button again\n"
                "• Using the external player option\n"
                "• Restarting the application")

        except Exception as e:
            print(f"Video fix error: {e}")
            messagebox.showerror("Fix Error", f"Failed to apply video fixes: {str(e)}")

    def _reset_video_scaling(self):
        """Reset video scaling and aspect ratio"""
        try:
            if self.vlc_player:
                print("Resetting video scaling...")
                self.vlc_player.video_set_scale(1.0)
                self.vlc_player.video_set_aspect_ratio(None)

                # Try different scaling options
                for scale in [0.5, 1.0, 1.5]:
                    try:
                        self.vlc_player.video_set_scale(scale)
                        self.parent_frame.update_idletasks()
                    except:
                        continue

                # Reset to normal scaling
                self.vlc_player.video_set_scale(1.0)
                print("Video scaling reset completed")

        except Exception as e:
            print(f"Video scaling reset error: {e}")

    def _handle_video_error(self, error_message):
        """Handle video-related errors and offer fallback options"""
        if "direct3d11" in error_message.lower() or "SetThumbNailClip" in error_message:
            print("Direct3D11 error detected, offering external player option...")
            self.status_callback("Video error detected - click 'Fix' button for options")

            # Automatically show troubleshooting dialog after a short delay
            self.parent_frame.after(1000, self._show_error_troubleshooting)

    def _show_error_troubleshooting(self):
        """Show troubleshooting dialog for video errors"""
        error_msg = (
            "🎥 Video Error Detected\n\n"
            "A Direct3D11 video error has been detected. This is a common issue with\n"
            "embedded video playback on Windows systems.\n\n"
            "Options:\n"
            "• Try restarting the application\n"
            "• Use external video player\n"
            "• Update graphics drivers\n\n"
            "Would you like to switch to external video player mode?"
        )

        use_external = messagebox.askyesno("Video Error", error_msg)

        if use_external:
            self.force_external_player()

    def fallback_external_player(self, stream_url):
        """Fallback to external media player if VLC integration fails (alias for force_external_player)"""
        self.force_external_player(stream_url)

    def _check_playback(self):
        """Check if VLC is actually playing and handle issues"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return

        try:
            if self.vlc_player.is_playing():
                self.status_callback("Playing - Stream active")
            else:
                # Check if there were any critical errors
                state = self.vlc_player.get_state()
                if state == vlc.State.Error:
                    self.status_callback("Stream error - trying fallback...")
                    # Try to restart the stream
                    self.parent_frame.after(1000, lambda: self._retry_stream())
                else:
                    self.status_callback("Stream not active - retrying...")
                    self.vlc_player.play()
                    # Check again in 2 seconds
                    self.parent_frame.after(2000, lambda: self.status_callback("Playing"))
        except Exception as e:
            print(f"VLC playback check error: {e}")
            self.status_callback("Playback check failed")

    def _retry_stream(self):
        """Retry loading the stream with different settings"""
        if self.vlc_player is None:
            self.status_callback("VLC not initialized")
            return

        try:
            current_media = self.vlc_player.get_media()
            if current_media:
                media_url = current_media.get_mrl()
                self.status_callback("Retrying stream...")

                # Stop current playback
                self.vlc_player.stop()

                # Create new media with additional options
                media = self.vlc_instance.media_new(media_url)
                media.add_option('--avcodec-hw=none')
                media.add_option('--avcodec-threads=1')
                media.add_option('--network-caching=2000')

                self.vlc_player.set_media(media)
                self.vlc_player.play()

                self.parent_frame.after(3000, lambda: self.status_callback("Stream restarted"))
        except Exception as e:
            print(f"Stream retry failed: {e}")
            self.status_callback("Stream retry failed")

    def is_playing(self):
        """Check if the player is currently playing"""
        if self.vlc_player is None:
            return False
        try:
            return self.vlc_player.is_playing()
        except Exception as e:
            print(f"Error checking playback status: {e}")
            return False

    def stop_stream(self):
        """Stop the current stream"""
        self.stop()

    def set_video_window(self):
        """Set up the video output window"""
        self._setup_video_output()

    def get_frame(self):
        """Get the main video player frame for packing/unpacking"""
        return self.main_frame

    def cleanup(self):
        """Clean up VLC resources"""
        try:
            # Clean up main player
            if self.vlc_player:
                self.vlc_player.stop()
                self.vlc_player.release()

            if self.vlc_instance:
                self.vlc_instance.release()

        except Exception as e:
            print(f"VLC cleanup error: {e}")
