def calculate_idle_time(data):
    total = len(data)
    if total == 0:
        return 0.0
    idle = sum(1 for d in data if d["status"] == "IDLE")
    return (idle / total) * 100
