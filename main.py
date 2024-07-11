from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,PlainTextResponse,FileResponse
from pyotp import TOTP,random_base32
from os import getenv,listdir
from asyncio import sleep,create_task

class Volatile:
    def __init__(self) -> None:
        self.token = ""
        self.latest_otp = ""
        self.downloaded:list[str] = []
app = FastAPI(openapi_url=None)
keys = listdir("key/")
secret = getenv('OTP_SECRET')
data = Volatile()
otp = TOTP(secret, digits=8, interval=30,name='OTP', issuer='give-me-my-key')

async def token_timeout():
    await sleep(5)
    data.token = ""
    data.downloaded.clear()

class EmptyResponse(HTMLResponse):
    def __init__(self, *args,**kwargs) -> None:
        data.latest_otp = otp.now()
        print("locked!")
        super().__init__("",*args,**kwargs)

@app.get("/")
async def root(request: Request):
    return EmptyResponse()

@app.get("/{part1}")
async def empty(part1:str):
    return EmptyResponse()

@app.get("/{part1}/{part2}")
async def verify(part1:str,part2:str,request: Request):
    if len(part1) != 4:
        return EmptyResponse()
    if len(part2) != 4:
        return EmptyResponse()
    key = part1 + part2
    if not otp.verify(key):
        return EmptyResponse()
    if data.latest_otp == key:
        return EmptyResponse()
    scheme = request.url.scheme
    netloc = request.url.netloc
    data.latest_otp = key
    data.token = random_base32(128)
    create_task(token_timeout())
    files = [f'curl -o ~/.ssh/{file} "{scheme}://{netloc}/{part1}/{part2}/{data.token}/{file}"' for file in keys]
    return PlainTextResponse('\n'.join(files))

@app.get("/{part1}/{part2}/{provided_token}/{filename}")
async def getfile(part1:str,part2:str,provided_token:str,filename:str):
    if provided_token != data.token:
        return EmptyResponse()
    if len(part1) != 4:
        return EmptyResponse()
    if len(part2) != 4:
        return EmptyResponse()
    key = part1 + part2
    if not otp.verify(key):
        return EmptyResponse()
    if filename in data.downloaded:
        return EmptyResponse()
    data.downloaded.append(filename)
    provided_token = provided_token
    if otp.verify(key):
        return FileResponse(f"key/{filename}")
    else:
        return EmptyResponse()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print("========= IP INFO =========")
    print(request.headers.get("X-Forwarded-For") or request.client.host or request.headers.get("host"))
    response = await call_next(request)
    return response
