import websocket

try:
    ws = websocket.create_connection("wss://ws.bitget.com/v2/ws/public")
    print("连接成功")
except Exception as e:
    print("连接失败:", e)