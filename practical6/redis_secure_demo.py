# file: redis_secure_demo.py
import redis

def create_redis_client():
    client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        username="app_user",
        password="appStrongPwd",
        ssl=True,
        ssl_ca_certs="/etc/redis/tls/ca.crt",
        ssl_check_hostname=False,
        decode_responses=True,
    )
    return client

if __name__ == "__main__":
    r = create_redis_client()
    print("Connected as:", r.acl_whoami())
    r.set("session:python_demo", "hello from python")
    print("Value:", r.get("session:python_demo"))