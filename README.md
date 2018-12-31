# botzone-mccts

Misaka Cloud Computing Telepathy Suite: the BotZone AI in your own computer

## Advantages

- Fully utilize the performance of your computer
- Increase the timeout per turn to 10 seconds
- Easy development from local host

## Requirements

- A stable network condition
- A Python 3.x environment
- A BotZone account
- An executable AI program (or we will use built-in emulated invader)

## Setting Up

- `pip install -r requirements.txt`
- Upload `mcc_client.py` (Python 3.6.5) to BotZone
- Run `mcc_server.py`
- Input your program's path and your BotZone login credential as prompted
- Keep the server running forever

## Hints

- Select "Basic I/O" on BotZone in regard with your program
- Don't input your program's path in order to activate built-in emulated invader for Amazons
- To avoid timeout error, keep the execution time of your program no more than 8 seconds
- In case of crashes, you might need to delete `/data/misaka_*` manually in your user directory
