#!/bin/bash
# 🚀 OBA Test Environment Startup Script

echo "🍓 OBA Raspberry Pi Test Environment başlatılıyor..."

# SSH host keys oluştur (eğer yoksa)
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    echo "🔑 SSH host keys oluşturuluyor..."
    ssh-keygen -A
fi

# SSH servisini başlat
echo "📡 SSH servisi başlatılıyor..."
service ssh start

# Test bilgilerini göster
echo ""
echo "✅ Test environment hazır!"
echo "==============================="
echo "🍓 Simulated Raspberry Pi OS"
echo "👤 Username: pi"
echo "🔑 Password: raspberry"
echo "📡 SSH Port: 22"
echo "🌐 Web Port: 8080"
echo ""
echo "Bağlantı komutu:"
echo "ssh -p 2222 pi@localhost"
echo ""

# Sonsuz döngü - container'ı canlı tut
echo "🔄 Container aktif tutlacak..."
tail -f /dev/null
