import psutil
import shutil
import platform
import time
from datetime import timedelta

BOOT_TIME = psutil.boot_time()


def format_bytes(size):
    power = 1024
    units = ["B", "KB", "MB", "GB", "TB"]

    n = 0
    while size > power and n < len(units)-1:
        size /= power
        n += 1

    return f"{round(size,2)} {units[n]}"


def get_cpu():

    cpu = psutil.cpu_percent(interval=0.5)

    if cpu < 60:
        status = "Healthy"
        color = "green"

    elif cpu < 85:
        status = "Warning"
        color = "orange"

    else:
        status = "Critical"
        color = "red"

    return {
        "usage": cpu,
        "status": status,
        "color": color
    }


def get_memory():

    mem = psutil.virtual_memory()

    usage = mem.percent

    if usage < 70:
        status = "Healthy"
        color = "green"

    elif usage < 90:
        status = "Warning"
        color = "orange"

    else:
        status = "Critical"
        color = "red"

    return {

        "usage": usage,

        "used": format_bytes(mem.used),

        "available": format_bytes(mem.available),

        "total": format_bytes(mem.total),

        "status": status,

        "color": color

    }


def get_disk():

    disk = shutil.disk_usage("/")

    used_percent = round((disk.used/disk.total)*100,2)

    if used_percent < 75:
        status = "Healthy"
        color = "green"

    elif used_percent < 90:
        status = "Warning"
        color = "orange"

    else:
        status = "Critical"
        color = "red"

    return {

        "usage": used_percent,

        "used": format_bytes(disk.used),

        "free": format_bytes(disk.free),

        "total": format_bytes(disk.total),

        "status": status,

        "color": color

    }


def get_system():

    uptime_seconds = time.time() - BOOT_TIME

    return {

        "hostname": platform.node(),

        "os": platform.system(),

        "release": platform.release(),

        "processor": platform.processor(),

        "uptime": str(timedelta(seconds=int(uptime_seconds)))

    }


def get_system_health():

    return {

        "cpu": get_cpu(),

        "memory": get_memory(),

        "disk": get_disk(),

        "system": get_system()

    }