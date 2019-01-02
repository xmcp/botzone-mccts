# botzone-mccts

Misaka Cloud Computing Telepathy Suite: the BotZone AI in your own computer

## Advantages

- Fully utilize the performance of your computer
- Increase the timeout per turn to 10 seconds (Python client) or 5 seconds (C++ client)
- Unlock more possibilities with Internet connection

## Requirements

- A stable network condition
- A Python 3.x environment
- A BotZone account
- An executable AI program or Python module

## Setting Up

- `pip install -r requirements.txt`
- Upload `mcc_client.py` (Python 3.6.5) or `mcc_client.cpp` (C++17) to BotZone
- Run `mcc_server.py`
- Input your AI's information (See "AI Integrating How-To" below)
- Input your BotZone login credential
- Keep the server running forever

## Hints

- Select "Basic I/O" on BotZone in regard with your program
- To avoid timeout error, keep the execution time of your AI in no more than 8.5 seconds (Python client) or 3.5 seconds (C++ client)
- In case of crashes, you might need to delete `/data/misaka_*` manually in your user directory
- Store `["username","password"]` into environment variable `mcc_credentials` so that you will not be prompted to input your credential every time

## AI Integrating How-To

If your AI is an executable program:
- Receive input from `stdin` and give output to `stdout`
- Input your program's path name as prompted

If your AI is a Python module:
- Expose a function `main(inp: str) -> str`
- Input your module's name as prompted

