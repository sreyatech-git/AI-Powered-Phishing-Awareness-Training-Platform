from system_health.system_monitor import get_system_health
from system_health.db_monitor import get_database_health
from system_health.service_monitor import (
    check_smtp,
    check_ai,
    check_services
)


def get_complete_health():

    return {

        "system": get_system_health(),

        "database": get_database_health(),

        "smtp": check_smtp(),

        "ai": check_ai(),

        "services": check_services()

    }
    