#!/usr/bin/env python3
"""
🌍 Environment Manager - Ortam Yönetimi
Hacı Abi'nin Akıllı Ortam Tespit ve Yönetim Sistemi
"""

import logging
import os
import platform
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class EnvironmentType(Enum):
    """Ortam tipleri"""
    DEV_CONTAINER = "dev_container"
    RASPBERRY_PI = "raspberry_pi"
    LINUX_DESKTOP = "linux_desktop"
    WINDOWS_WSL = "windows_wsl"
    MACOS = "macos"
    DOCKER = "docker"
    UNKNOWN = "unknown"


class HardwareCapability(Enum):
    """Donanım yeteneği tipleri"""
    GPIO = "gpio"
    CAMERA = "camera"
    I2C = "i2c"
    SPI = "spi"
    UART = "uart"
    USB = "usb"
    AUDIO = "audio"
    DISPLAY = "display"
    NETWORK = "network"


class EnvironmentManager:
    """🌍 Ortam yöneticisi - Geliştirme vs Hardware otomatik yönetimi"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._env_type = None
        self._capabilities = None
        self._config = None

        # Ortam tespiti
        self._detect_environment()
        self._detect_capabilities()

        self.logger.info(f"🔍 Tespit edilen ortam: {self._env_type.value}")

    def _detect_environment(self) -> None:
        """Çalışma ortamını otomatik tespit et"""

        # Dev Container kontrolü
        if self._is_dev_container():
            self._env_type = EnvironmentType.DEV_CONTAINER

        # Docker kontrolü
        elif self._is_docker():
            self._env_type = EnvironmentType.DOCKER

        # Raspberry Pi kontrolü
        elif self._is_raspberry_pi():
            self._env_type = EnvironmentType.RASPBERRY_PI

        # Windows WSL kontrolü
        elif self._is_wsl():
            self._env_type = EnvironmentType.WINDOWS_WSL

        # macOS kontrolü
        elif self._is_macos():
            self._env_type = EnvironmentType.MACOS

        # Linux Desktop kontrolü
        elif self._is_linux_desktop():
            self._env_type = EnvironmentType.LINUX_DESKTOP

        else:
            self._env_type = EnvironmentType.UNKNOWN
            self.logger.warning("⚠️ Bilinmeyen ortam tespit edildi")

    def _is_dev_container(self) -> bool:
        """Dev Container mi?"""
        indicators = [
            os.environ.get("CODESPACES"),
            os.environ.get("REMOTE_CONTAINERS"),
            os.environ.get("REMOTE_CONTAINERS_IPC"),
            os.environ.get("VSCODE_REMOTE_CONTAINERS_SESSION"),
            Path("/.devcontainer").exists(),
            "/workspaces/" in os.getcwd()
        ]
        return any(indicators)

    def _is_docker(self) -> bool:
        """Docker container mi?"""
        indicators = [
            Path("/.dockerenv").exists(),
            os.environ.get("DOCKER_CONTAINER") == "true"
        ]

        # /proc/1/cgroup kontrolü
        try:
            if Path("/proc/1/cgroup").exists():
                with open("/proc/1/cgroup", "r") as f:
                    if "docker" in f.read():
                        indicators.append(True)
        except:
            pass

        return any(indicators)

    def _is_raspberry_pi(self) -> bool:
        """Raspberry Pi mi?"""
        indicators = []

        # /proc/cpuinfo kontrolü
        try:
            if Path("/proc/cpuinfo").exists():
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read()
                    if any(x in content for x in ["Raspberry Pi", "BCM2835", "BCM2836", "BCM2837", "BCM2711"]):
                        indicators.append(True)
        except:
            pass

        # /proc/device-tree/model kontrolü
        try:
            if Path("/proc/device-tree/model").exists():
                with open("/proc/device-tree/model", "r") as f:
                    if "Raspberry Pi" in f.read():
                        indicators.append(True)
        except:
            pass

        # ARM architecture + Linux
        if platform.machine().lower().startswith('arm') and platform.system() == "Linux":
            indicators.append(True)

        return any(indicators)

    def _is_wsl(self) -> bool:
        """Windows WSL mi?"""
        if platform.system() != "Linux":
            return False

        indicators = []

        # /proc/version kontrolü
        try:
            if Path("/proc/version").exists():
                with open("/proc/version", "r") as f:
                    content = f.read().lower()
                    if any(x in content for x in ["microsoft", "wsl"]):
                        indicators.append(True)
        except:
            pass

        # uname kontrolü
        try:
            uname = platform.uname().release.lower()
            if any(x in uname for x in ["microsoft", "wsl"]):
                indicators.append(True)
        except:
            pass

        return any(indicators)

    def _is_macos(self) -> bool:
        """macOS mi?"""
        return platform.system() == "Darwin"

    def _is_linux_desktop(self) -> bool:
        """Linux Desktop mi?"""
        return (platform.system() == "Linux" and
                os.environ.get("DISPLAY") is not None)

    def _detect_capabilities(self) -> None:
        """Donanım yeteneklerini tespit et"""
        self._capabilities = {}

        for capability in HardwareCapability:
            self._capabilities[capability] = self._check_capability(capability)

    def _check_capability(self, capability: HardwareCapability) -> bool:
        """Belirli bir donanım yeteneğini kontrol et"""

        if capability == HardwareCapability.GPIO:
            return self._check_gpio()

        elif capability == HardwareCapability.CAMERA:
            return self._check_camera()

        elif capability == HardwareCapability.I2C:
            return self._check_i2c()

        elif capability == HardwareCapability.SPI:
            return self._check_spi()

        elif capability == HardwareCapability.UART:
            return self._check_uart()

        elif capability == HardwareCapability.USB:
            return self._check_usb()

        elif capability == HardwareCapability.AUDIO:
            return self._check_audio()

        elif capability == HardwareCapability.DISPLAY:
            return self._check_display()

        elif capability == HardwareCapability.NETWORK:
            return self._check_network()

        return False

    def _check_gpio(self) -> bool:
        """GPIO kullanılabilir mi?"""
        # Raspberry Pi'de GPIO var
        if self._env_type == EnvironmentType.RASPBERRY_PI:
            try:
                import RPi.GPIO as GPIO
                return True
            except ImportError:
                return False

        # Diğer ortamlarda GPIO yok
        return False

    def _check_camera(self) -> bool:
        """Kamera kullanılabilir mi?"""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            is_available = cap.isOpened()
            cap.release()
            return is_available
        except:
            return False

    def _check_i2c(self) -> bool:
        """I2C kullanılabilir mi?"""
        i2c_devices = ["/dev/i2c-0", "/dev/i2c-1", "/dev/i2c-2"]
        return any(Path(device).exists() for device in i2c_devices)

    def _check_spi(self) -> bool:
        """SPI kullanılabilir mi?"""
        spi_devices = ["/dev/spidev0.0", "/dev/spidev0.1"]
        return any(Path(device).exists() for device in spi_devices)

    def _check_uart(self) -> bool:
        """UART kullanılabilir mi?"""
        uart_devices = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0"]
        return any(Path(device).exists() for device in uart_devices)

    def _check_usb(self) -> bool:
        """USB kullanılabilir mi?"""
        return Path("/sys/bus/usb").exists()

    def _check_audio(self) -> bool:
        """Audio kullanılabilir mi?"""
        audio_indicators = [
            Path("/dev/snd").exists(),
            Path("/proc/asound").exists()
        ]
        return any(audio_indicators)

    def _check_display(self) -> bool:
        """Display kullanılabilir mi?"""
        return os.environ.get("DISPLAY") is not None

    def _check_network(self) -> bool:
        """Network bağlantısı var mı?"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False

    @property
    def environment_type(self) -> EnvironmentType:
        """Ortam tipini döndür"""
        return self._env_type

    @property
    def is_simulation_mode(self) -> bool:
        """Simülasyon modunda mı?"""
        simulation_environments = [
            EnvironmentType.DEV_CONTAINER,
            EnvironmentType.DOCKER,
            EnvironmentType.LINUX_DESKTOP,
            EnvironmentType.WINDOWS_WSL,
            EnvironmentType.MACOS
        ]
        return self._env_type in simulation_environments

    @property
    def is_hardware_mode(self) -> bool:
        """Donanım modunda mı?"""
        return self._env_type == EnvironmentType.RASPBERRY_PI

    @property
    def capabilities(self) -> Dict[HardwareCapability, bool]:
        """Donanım yeteneklerini döndür"""
        return self._capabilities.copy()

    def has_capability(self, capability: HardwareCapability) -> bool:
        """Belirli bir yeteneğe sahip mi?"""
        return self._capabilities.get(capability, False)

    def get_environment_info(self) -> Dict[str, Any]:
        """Detaylı ortam bilgisi"""
        return {
            "environment_type": self._env_type.value,
            "is_simulation": self.is_simulation_mode,
            "is_hardware": self.is_hardware_mode,
            "capabilities": {cap.value: available for cap, available in self._capabilities.items()},
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0]
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation()
            },
            "paths": {
                "cwd": os.getcwd(),
                "home": os.path.expanduser("~")
            }
        }

    def get_recommended_config(self) -> Dict[str, Any]:
        """Ortam için önerilen konfigürasyon"""
        config = {
            "simulation": self.is_simulation_mode,
            "debug": self.is_simulation_mode,
            "hardware": {
                "gpio_enabled": self.has_capability(HardwareCapability.GPIO),
                "camera_enabled": self.has_capability(HardwareCapability.CAMERA),
                "i2c_enabled": self.has_capability(HardwareCapability.I2C),
                "spi_enabled": self.has_capability(HardwareCapability.SPI),
                "uart_enabled": self.has_capability(HardwareCapability.UART)
            },
            "logging": {
                "level": "DEBUG" if self.is_simulation_mode else "INFO",
                "console": True,
                "file": True
            },
            "web_interface": {
                "enabled": True,
                "host": "0.0.0.0" if self.is_hardware_mode else "127.0.0.1",
                "port": 8080 if self.is_hardware_mode else 5000,
                "debug": self.is_simulation_mode
            }
        }

        # Ortam özel ayarlar
        if self._env_type == EnvironmentType.DEV_CONTAINER:
            config.update({
                "data_path": "/workspaces/oba/data",
                "log_path": "/workspaces/oba/logs",
                "mock_sensors": True,
                "visualization": True
            })

        elif self._env_type == EnvironmentType.RASPBERRY_PI:
            config.update({
                "data_path": "/home/pi/oba/data",
                "log_path": "/home/pi/oba/logs",
                "mock_sensors": False,
                "visualization": False,
                "performance_optimized": True
            })

        return config

    def print_environment_summary(self):
        """Ortam özetini yazdır"""
        print("🌍 ORTAM BİLGİLERİ")
        print("=" * 40)
        print(f"🔍 Ortam Tipi: {self._env_type.value}")
        print(f"🎮 Simülasyon Modu: {'✅ Evet' if self.is_simulation_mode else '❌ Hayır'}")
        print(f"⚙️ Donanım Modu: {'✅ Evet' if self.is_hardware_mode else '❌ Hayır'}")
        print()

        print("🔧 DONANIM YETENEKLERİ")
        print("-" * 25)
        for capability, available in self._capabilities.items():
            status = "✅" if available else "❌"
            print(f"{status} {capability.value.upper()}")

        print()
        print("💡 ÖNERİLEN AYARLAR")
        print("-" * 20)
        config = self.get_recommended_config()
        print(f"🎮 Simülasyon: {config['simulation']}")
        print(f"🐛 Debug: {config['debug']}")
        print(f"🌐 Web Port: {config['web_interface']['port']}")
        print(f"📊 Log Level: {config['logging']['level']}")

    # Public wrapper metodlar
    def is_dev_container(self) -> bool:
        """Dev Container ortamında mı?"""
        return self._env_type == EnvironmentType.DEV_CONTAINER

    def is_raspberry_pi(self) -> bool:
        """Raspberry Pi ortamında mı?"""
        return self._env_type == EnvironmentType.RASPBERRY_PI

    def is_docker(self) -> bool:
        """Docker ortamında mı?"""
        return self._env_type == EnvironmentType.DOCKER
