#!/bin/bash
# Скрипт для автоматической остановки и удаления студенческих VM (ID начинается с 8)
# Запускается ежедневно в 00:00 через cron

LOG_FILE="/var/log/student_vm_cleanup.log"
PROXMOX_HOST="10.100.0.254"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== Начало очистки студенческих VM =========="

# Получаем список всех VM через SSH на Proxmox
VM_LIST=$(ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    root@${PROXMOX_HOST} "qm list" 2>/dev/null | awk '{print $1}' | grep -E '^8[0-9]+$')

if [ -z "$VM_LIST" ]; then
    log "Студенческих VM (начинающихся с 8) не найдено"
    exit 0
fi

STOPPED_COUNT=0
DESTROYED_COUNT=0

for VMID in $VM_LIST; do
    log "Обработка VM $VMID..."

    # Останавливаем VM
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        root@${PROXMOX_HOST} "qm stop $VMID" 2>/dev/null

    if [ $? -eq 0 ]; then
        log "  ✓ VM $VMID остановлена"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    else
        log "  ✗ Ошибка остановки VM $VMID (возможно уже остановлена)"
    fi

    # Ждем 3 секунды перед удалением
    sleep 3

    # Удаляем VM
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        root@${PROXMOX_HOST} "qm destroy $VMID --purge" 2>/dev/null

    if [ $? -eq 0 ]; then
        log "  ✓ VM $VMID удалена"
        DESTROYED_COUNT=$((DESTROYED_COUNT + 1))
    else
        log "  ✗ Ошибка удаления VM $VMID"
    fi

    # Удаляем конфиг файл (на всякий случай)
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        root@${PROXMOX_HOST} "rm -f /etc/pve/qemu-server/${VMID}.conf" 2>/dev/null
done

log "========== Завершено: остановлено $STOPPED_COUNT, удалено $DESTROYED_COUNT VM =========="
