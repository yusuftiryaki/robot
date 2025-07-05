#!/usr/bin/env python3
"""
⚙️ Smart Config Manager
Ortam Bazlı Akıllı Konfigürasyon Yöneticisi
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .environment_manager import EnvironmentManager, EnvironmentType


class SmartConfigManager:
    """⚙️ Akıllı konfigürasyon yöneticisi - Ortam bazlı config yükleme"""

    def __init__(self, base_config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.env_manager = EnvironmentManager()

        # Config dosya yolları
        self.base_config_path = Path(base_config_path) if base_config_path else Path("config/robot_config.yaml")
        self.env_config_dir = Path("config/environments")

        # Cache
        self._config_cache = None

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Ortam bazlı konfigürasyonu yükle"""

        if self._config_cache and not force_reload:
            return self._config_cache

        self.logger.info("⚙️ Konfigürasyon yükleniyor...")

        # 1. Temel konfigürasyonu yükle
        base_config = self._load_base_config()

        # 2. Ortam bazlı konfigürasyonu yükle
        env_config = self._load_environment_config()

        # 3. Runtime adaptasyonları uygula
        runtime_config = self._apply_runtime_adaptations()

        # 4. Konfigürasyonları birleştir
        final_config = self._merge_configs(base_config, env_config, runtime_config)

        # 5. Validasyon
        self._validate_config(final_config)

        # Cache'le
        self._config_cache = final_config

        self.logger.info(f"✅ Konfigürasyon yüklendi: {self.env_manager.environment_type.value}")
        return final_config

    def _load_base_config(self) -> Dict[str, Any]:
        """Temel konfigürasyonu yükle"""

        if not self.base_config_path.exists():
            self.logger.warning(f"⚠️ Temel config bulunamadı: {self.base_config_path}")
            return self._get_default_config()

        try:
            with open(self.base_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.logger.debug(f"📄 Temel config yüklendi: {self.base_config_path}")
                return config or {}
        except Exception as e:
            self.logger.error(f"❌ Temel config yükleme hatası: {e}")
            return self._get_default_config()

    def _load_environment_config(self) -> Dict[str, Any]:
        """Ortam bazlı konfigürasyonu yükle"""

        env_type = self.env_manager.environment_type
        env_config_path = self.env_config_dir / f"{env_type.value}.yaml"

        if not env_config_path.exists():
            self.logger.info(f"ℹ️ Ortam config'i bulunamadı: {env_config_path}")
            return {}

        try:
            with open(env_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.logger.debug(f"🌍 Ortam config'i yüklendi: {env_config_path}")
                return config or {}
        except Exception as e:
            self.logger.error(f"❌ Ortam config yükleme hatası: {e}")
            return {}

    def _apply_runtime_adaptations(self) -> Dict[str, Any]:
        """Runtime adaptasyonları uygula"""

        runtime_config = {
            "runtime": {
                "environment_type": self.env_manager.environment_type.value,
                "is_simulation": self.env_manager.is_simulation_mode,
                "is_hardware": self.env_manager.is_hardware_mode,
                "capabilities": {
                    cap.value: available
                    for cap, available in self.env_manager.capabilities.items()
                },
                "detected_at": self._get_current_timestamp()
            }
        }

        # Ortam bazlı otomatik adaptasyonlar
        adaptations = {}

        # Simülasyon modu adaptasyonları
        if self.env_manager.is_simulation_mode:
            adaptations.update({
                "simulation": {"enabled": True},
                "motors": {"type": "simulation"},
                "sensors": {"mock_enabled": True},
                # "logging": {"level": "DEBUG"},  # Environment config'i override etme
                "web_interface": {"debug": True}
            })

        # Donanım modu adaptasyonları
        if self.env_manager.is_hardware_mode:
            adaptations.update({
                "simulation": {"enabled": False},
                "motors": {"type": "hardware"},
                "sensors": {"mock_enabled": False},
                "logging": {"level": "INFO"},
                "web_interface": {"debug": False}
            })

        # Yetenek bazlı adaptasyonlar
        from .environment_manager import HardwareCapability

        if not self.env_manager.has_capability(HardwareCapability.GPIO):
            adaptations.setdefault("motors", {})["type"] = "simulation"
            adaptations.setdefault("sensors", {})["gpio_based"] = False

        if not self.env_manager.has_capability(HardwareCapability.CAMERA):
            adaptations.setdefault("camera", {})["enabled"] = False

        if not self.env_manager.has_capability(HardwareCapability.I2C):
            adaptations.setdefault("sensors", {}).setdefault("i2c", [])

        # Runtime config'e ekle
        runtime_config.update(adaptations)

        return runtime_config

    def _merge_configs(self, *configs) -> Dict[str, Any]:
        """Birden fazla konfigürasyonu birleştir"""

        merged = {}

        for config in configs:
            if config:
                self._deep_merge(merged, config)

        return merged

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Derin birleştirme (nested dict'ler için)"""

        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    self._deep_merge(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    # List'leri extend et
                    target[key].extend(value)
                else:
                    # Override et
                    target[key] = value
            else:
                target[key] = value

    def _validate_config(self, config: Dict[str, Any]):
        """Konfigürasyonu validate et"""

        required_sections = ["robot", "logging", "web_interface"]

        for section in required_sections:
            if section not in config:
                self.logger.warning(f"⚠️ Eksik config bölümü: {section}")

        # Özel validasyonlar
        if config.get("simulation", {}).get("enabled") and config.get("motors", {}).get("type") == "hardware":
            self.logger.warning("⚠️ Simülasyon modu açık ama motor tipi 'hardware' - motor tipi 'simulation' olarak değiştirildi")
            config["motors"]["type"] = "simulation"

    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon"""

        return {
            "robot": {
                "name": "OBA",
                "version": "1.0.0"
            },
            "simulation": {
                "enabled": self.env_manager.is_simulation_mode
            },
            "motors": {
                "type": "simulation" if self.env_manager.is_simulation_mode else "hardware"
            },
            "sensors": {
                "mock_enabled": self.env_manager.is_simulation_mode
            },
            "camera": {
                "enabled": self.env_manager.has_capability(HardwareCapability.CAMERA),
                "resolution": {"width": 640, "height": 480}
            },
            "web_interface": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 5000,
                "debug": self.env_manager.is_simulation_mode
            },
            "logging": {
                "level": "DEBUG" if self.env_manager.is_simulation_mode else "INFO",
                "console": {"enabled": True},
                "file": {"enabled": True, "path": "logs"}
            },
            "paths": {
                "data": "data",
                "logs": "logs",
                "models": "models",
                "config": "config"
            }
        }

    def _get_current_timestamp(self) -> str:
        """Mevcut timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_config_summary(self) -> Dict[str, Any]:
        """Konfigürasyon özeti"""

        config = self.load_config()

        return {
            "environment": self.env_manager.environment_type.value,
            "simulation_mode": config.get("simulation", {}).get("enabled", False),
            "motor_type": config.get("motors", {}).get("type", "unknown"),
            "camera_enabled": config.get("camera", {}).get("enabled", False),
            "web_port": config.get("web_interface", {}).get("port", 0),
            "log_level": config.get("logging", {}).get("level", "INFO"),
            "capabilities": self.env_manager.capabilities
        }

    def save_current_config(self, output_path: Optional[str] = None):
        """Mevcut konfigürasyonu dosyaya kaydet"""

        if not output_path:
            timestamp = self._get_current_timestamp().replace(":", "-").replace(".", "-")
            output_path = f"config/generated/config_{timestamp}.yaml"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        config = self.load_config()

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

            self.logger.info(f"💾 Konfigürasyon kaydedildi: {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Konfigürasyon kaydetme hatası: {e}")


# Convenience function
def load_smart_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Akıllı konfigürasyon yükleme - tek satırda kullanım"""
    manager = SmartConfigManager(config_path)
    return manager.load_config()
