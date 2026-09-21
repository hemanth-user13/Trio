import redis

client=redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
    
)
client.set("knowledgehub:test","hemanth")
print(client.get("knowledgehub:test"))
