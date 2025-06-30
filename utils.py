def validate_time(ts: str) -> bool:
    parts = ts.split(":")
    return len(parts)==2 and parts[0].isdigit() and parts[1].isdigit() and 0<=int(parts[0])<24 and 0<=int(parts[1])<60
