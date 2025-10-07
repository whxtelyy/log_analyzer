logs_storage = []

async def get_logs() -> list[str]:
    return logs_storage

async def add_log(log: str):
    logs_storage.append(log)
    return {'message': 'Log added', 'total': len(logs_storage)}