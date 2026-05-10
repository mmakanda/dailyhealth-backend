from slowapi import Limiter

def get_real_ip(request):
    """Extract real client IP from Railway's proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host

limiter = Limiter(key_func=get_real_ip)
