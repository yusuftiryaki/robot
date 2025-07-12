"""
📷 Kamera HAL Interface - Hardware Abstraction Layer
Hacı Abi'nin temiz kamera mimarisi!

Bu interface, simülasyon ve gerçek kamera implementasyonları için
ortak bir arayüz sağlar. SOLID prensiplerine uygun clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np


class KameraInterface(ABC):
    """
    📷 Kamera Hardware Abstraction Layer Interface

    Tüm kamera implementasyonları bu interface'i implement etmelidir.
    Simülasyon ve gerçek kamera arasında tutarlı API sağlar.
    """

    @abstractmethod
    async def baslat(self) -> bool:
        """
        🚀 Kamerayı başlat

        Returns:
            bool: Başlatma başarılı mı?
        """
        pass

    @abstractmethod
    async def goruntu_al(self) -> Optional[np.ndarray]:
        """
        📸 Kameradan görüntü al

        Returns:
            Optional[np.ndarray]: BGR formatında görüntü, None ise hata
        """
        pass

    @abstractmethod
    async def durdur(self) -> None:
        """
        🛑 Kamerayı durdur ve kaynakları temizle
        """
        pass

    @abstractmethod
    def get_kamera_bilgisi(self) -> Dict[str, Any]:
        """
        ℹ️ Kamera bilgilerini al

        Returns:
            Dict: Kamera durumu ve özellikleri
        """
        pass

    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """
        📐 Kamera çözünürlüğünü al

        Returns:
            Tuple[int, int]: (width, height)
        """
        pass

    @abstractmethod
    def is_simulation(self) -> bool:
        """
        🔍 Simülasyon modunda mı?

        Returns:
            bool: True ise simülasyon, False ise gerçek kamera
        """
        pass

    @abstractmethod
    def set_parametreler(self, parametreler: Dict[str, Any]) -> bool:
        """
        ⚙️ Kamera parametrelerini ayarla (exposure, gain vs.)

        Args:
            parametreler: Ayarlanacak parametreler

        Returns:
            bool: Ayarlama başarılı mı?
        """
        pass

    @abstractmethod
    def goruntu_kaydet(self, dosya_yolu: str) -> bool:
        """
        💾 Mevcut görüntüyü kaydet

        Args:
            dosya_yolu: Kaydedilecek dosya yolu

        Returns:
            bool: Kaydetme başarılı mı?
        """
        pass
