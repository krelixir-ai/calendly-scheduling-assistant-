from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from agents.main_agent import Agent
from guardrails.safety import validate_input, validate_output
from observability.monitoring import process_request
from error_handling.handler import retry
import yaml

app = FastAPI()

# Load configuration
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    config = {}

# Security - API Key Authentication (Example)
API_KEY = "your_secret_api_key"  # Replace with a secure method of storing/retrieving the API key

def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
@process_request
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
@process_request
async def chat_endpoint(request: ChatRequest, api_key_valid: bool = Depends(verify_api_key)):
    try:
        validated_input = validate_input(request.message)
        if "Error" in validated_input:
            return ChatResponse(response=validated_input)

        agent = Agent()

        def run_agent():
            return agent.run(validated_input)

        response = retry(run_agent, attempts=config.get("retry_attempts", 3))
        validated_output = validate_output(response)

        return ChatResponse(response=validated_output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn, os, socket
    def _port_free(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", p)) != 0
    port = int(os.environ.get("PORT", 8081))
    while not _port_free(port):
        print(f"Port {port} is already in use.")
        try:
            ans = input(f"Try port {port + 1} instead? [Y/n]: ").strip().lower()
        except EOFError:
            ans = "y"
        if ans in ("", "y", "yes"):
            port += 1
        else:
            print("Exiting. Free the port and try again.")
            raise SystemExit(1)
    print(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)